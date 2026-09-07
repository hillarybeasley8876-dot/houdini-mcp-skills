import hou
import json
import struct
import threading
import socket
import time
import difflib
import fnmatch
from itertools import islice
from contextlib import contextmanager
import requests
import tempfile
import traceback
import os
import shutil
import sys
# Try PySide6 first (Houdini 21.0+), fall back to PySide2 (older versions)
try:
    from PySide6 import QtWidgets, QtCore
    print("Using PySide6 (Houdini 21.0+)")
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore
        print("Using PySide2 (Houdini 19.5-20.x)")
    except ImportError:
        print("Warning: Neither PySide6 nor PySide2 found. Some features may not work.")
        # Create dummy classes to prevent import errors
        class QtCore:
            class QTimer:
                pass
        QtWidgets = None
import io
from contextlib import redirect_stdout, redirect_stderr

# Imports for OPUS import
import zipfile
from urllib.parse import urlparse
import uuid # For unique temp dirs and file processing

# --- NEW: Import render functions --- 
# try:
from .HoudiniMCPRender import *
# HMCPLib = HoudiniMCPRender # Alias for easier use
print("HoudiniMCPRender module loaded successfully.")
# except ImportError:
#     HMCPLib = None
#     print("Warning: HoudiniMCPRender.py not found or failed to import. Rendering tools will be unavailable.")
# ----------------------------------

# Info about the extension (optional metadata)
EXTENSION_NAME = "Houdini MCP"
EXTENSION_VERSION = (0, 1)
EXTENSION_DESCRIPTION = "Connect Houdini to Claude via MCP"

class HoudiniMCPServer:
    def __init__(self, host='127.0.0.1', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.client = None
        self.buffer = b''
        self.timer = None

    def start(self):
        """Begin listening on the given port; sets up a QTimer to poll for data."""
        if self.running:
            print(f"HoudiniMCP server is already running on {self.host}:{self.port}")
            return

        self._cleanup_client()
        self._cleanup_socket()
        self._cleanup_timer()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(4)
            self.server_socket.setblocking(False)
            
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self._process_server)
            self.timer.start(100)

            self.running = True
            print(f"HoudiniMCP server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()
            
    def stop(self):
        """Stop listening; close sockets and timers."""
        self.running = False
        self._cleanup_timer()
        self._cleanup_client()
        self._cleanup_socket()
        print("HoudiniMCP server stopped")

    def _cleanup_timer(self):
        if self.timer is not None:
            try:
                self.timer.stop()
            except Exception:
                pass
            self.timer = None

    def _cleanup_client(self):
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
        self.buffer = b''

    def _cleanup_socket(self):
        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

    def _process_server(self):
        """
        Timer callback to accept connections and process any incoming data.
        This runs in the main Houdini thread to avoid concurrency issues.
        
        Protocol: each message is a 4-byte big-endian length prefix
        followed by that many bytes of UTF-8 JSON.
        """
        if not self.running:
            return
        
        try:
            # Accept all pending connections; the newest client wins. A stale
            # idle client (e.g. an abandoned bridge process) must never be able
            # to hold the slot and lock new clients out of the server.
            if self.server_socket:
                while True:
                    try:
                        new_client, address = self.server_socket.accept()
                    except BlockingIOError:
                        break
                    except Exception as e:
                        print(f"Error accepting connection: {str(e)}")
                        break
                    if self.client is not None:
                        print(f"New connection from {address}; replacing existing client")
                        self._cleanup_client()
                    new_client.setblocking(False)
                    self.client = new_client
                    print(f"Connected to client: {address}")
            
            if self.client:
                try:
                    data = self.client.recv(8192)
                    if data:
                        self.buffer += data
                        while True:
                            if len(self.buffer) < 4:
                                break
                            msg_len = struct.unpack('>I', self.buffer[:4])[0]
                            MAX_MSG_LEN = 50 * 1024 * 1024
                            if msg_len > MAX_MSG_LEN:
                                print(f"Message too large ({msg_len} bytes), disconnecting client")
                                self._cleanup_client()
                                break
                            if len(self.buffer) < 4 + msg_len:
                                break
                            payload = self.buffer[4:4 + msg_len]
                            self.buffer = self.buffer[4 + msg_len:]
                            try:
                                command = json.loads(payload.decode('utf-8'))
                                response = self.execute_command(command)
                                response_bytes = json.dumps(response).encode('utf-8')
                                response_frame = struct.pack('>I', len(response_bytes)) + response_bytes
                                try:
                                    self.client.sendall(response_frame)
                                except (BrokenPipeError, ConnectionResetError, OSError) as send_err:
                                    print(f"Failed to send response (client likely disconnected): {send_err}")
                                    self._cleanup_client()
                                    break
                            except json.JSONDecodeError as e:
                                print(f"Invalid JSON in message: {e}")
                    else:
                        print("Client disconnected (empty recv)")
                        self._cleanup_client()
                except BlockingIOError:
                    pass
                except (ConnectionResetError, BrokenPipeError, OSError) as e:
                    print(f"Client connection lost: {str(e)}")
                    self._cleanup_client()

        except Exception as e:
            print(f"Server error: {str(e)}")

    # -------------------------------------------------------------------------
    # Command Handling
    # -------------------------------------------------------------------------
    
    def execute_command(self, command):
        """Entry point for executing a JSON command from the client."""
        try:
            return self._execute_command_internal(command)
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        """
        Internal dispatcher that looks up 'cmd_type' from the JSON,
        calls the relevant function, and returns a JSON-friendly dict.
        """
        cmd_type = command.get("type")
        params = command.get("params", {})

        # Always-available handlers
        handlers = {
            "get_scene_info": self.get_scene_info,
            "create_node": self.create_node,
            "modify_node": self.modify_node,
            "delete_node": self.delete_node,
            "get_node_info": self.get_node_info,
            "execute_code": self.execute_code,
            "set_material": self.set_material,
            "get_asset_lib_status": self.get_asset_lib_status,
            "import_opus_url": self.handle_import_opus_url,
            # Graph editing & introspection
            "connect_nodes": self.connect_nodes,
            "disconnect_input": self.disconnect_input,
            "set_parameters": self.set_parameters,
            "get_parameter_schema": self.get_parameter_schema,
            "set_node_flags": self.set_node_flags,
            "layout_children": self.layout_children,
            "find_error_nodes": self.find_error_nodes,
            "cook_node": self.cook_node,
            # VEX wrangles
            "create_wrangle": self.create_wrangle,
            "set_wrangle_code": self.set_wrangle_code,
            # Geometry introspection
            "get_geometry_info": self.get_geometry_info,
            "get_geometry_data": self.get_geometry_data,
            # Add new render handlers
            "render_single_view": self.handle_render_single_view,
            "render_quad_view": self.handle_render_quad_view,
            "render_specific_camera": self.handle_render_specific_camera,
            "ping": self._handle_ping,
        }
        
        # If user has toggled asset library usage
        if getattr(hou.session, "houdinimcp_use_assetlib", False):
            asset_handlers = {
                "get_asset_categories": self.get_asset_categories,
                "search_assets": self.search_assets,
                "import_asset": self.import_asset,
            }
            handlers.update(asset_handlers)

        handler = handlers.get(cmd_type)
        if not handler:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

        print(f"Executing handler for {cmd_type}")
        with self._undo_group(cmd_type):
            result = handler(**params)
        print(f"Handler execution complete for {cmd_type}")
        return {"status": "success", "result": result}

    # Commands that mutate the scene get wrapped in a single undo group so the
    # artist can Ctrl+Z any agent action as one step.
    MUTATING_COMMANDS = frozenset({
        "create_node", "modify_node", "delete_node", "set_material",
        "import_opus_url", "import_asset", "connect_nodes", "disconnect_input",
        "set_parameters", "set_node_flags", "layout_children",
        "create_wrangle", "set_wrangle_code",
    })

    @contextmanager
    def _undo_group(self, cmd_type):
        if cmd_type in self.MUTATING_COMMANDS and hasattr(hou, "undos"):
            with hou.undos.group(f"MCP: {cmd_type}"):
                yield
        else:
            yield

    def _handle_ping(self):
        return {"pong": True, "protocol": 1}

    # -------------------------------------------------------------------------
    # Basic Info & Node Operations
    # -------------------------------------------------------------------------

    def get_asset_lib_status(self):
        """Checks if the user toggled asset library usage in hou.session."""
        use_assetlib = getattr(hou.session, "houdinimcp_use_assetlib", False)
        msg = ("Asset library usage is enabled." 
               if use_assetlib 
               else "Asset library usage is disabled.")
        return {"enabled": use_assetlib, "message": msg}

    def get_scene_info(self):
        """Returns basic info about the current .hip file and top-level nodes per context."""
        try:
            hip_file = hou.hipFile.name()
            scene_info = {
                "name": os.path.basename(hip_file) if hip_file else "Untitled",
                "filepath": hip_file or "",
                "fps": hou.fps(),
                "start_frame": hou.playbar.frameRange()[0],
                "end_frame": hou.playbar.frameRange()[1],
                "contexts": {},
            }

            # Collect per-context node summaries (avoids expensive allSubChildren traversal)
            root = hou.node("/")
            contexts = ["obj", "shop", "out", "ch", "vex", "stage"]

            for ctx_name in contexts:
                ctx_node = root.node(ctx_name)
                if ctx_node:
                    children = ctx_node.children()
                    scene_info["contexts"][ctx_name] = {
                        "count": len(children),
                        "nodes": [
                            {
                                "name": node.name(),
                                "path": node.path(),
                                "type": node.type().name(),
                            }
                            for node in children[:20]
                        ],
                    }

            return scene_info

        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}

    def create_node(self, node_type, parent_path="/obj", name=None, position=None, parameters=None):
        """Creates a new node in the specified parent."""
        try:
            parent = hou.node(parent_path)
            if not parent:
                raise ValueError(f"Parent path not found: {parent_path}")
            
            node = parent.createNode(node_type, node_name=name)
            if position and len(position) >= 2:
                node.setPosition([position[0], position[1]])
            if parameters:
                for p_name, p_val in parameters.items():
                    parm = node.parm(p_name)
                    if parm:
                        parm.set(p_val)
            
            return {
                "name": node.name(),
                "path": node.path(),
                "type": node.type().name(),
                "position": list(node.position()),
            }
        except Exception as e:
            raise Exception(f"Failed to create node: {str(e)}")

    def modify_node(self, path, parameters=None, position=None, name=None):
        """Modifies an existing node."""
        node = hou.node(path)
        if not node:
            raise ValueError(f"Node not found: {path}")
        
        changes = []
        old_name = node.name()
        
        if name and name != old_name:
            node.setName(name)
            changes.append(f"Renamed from {old_name} to {name}")
        
        if position and len(position) >= 2:
            node.setPosition([position[0], position[1]])
            changes.append(f"Position set to {position}")
        
        if parameters:
            for p_name, p_val in parameters.items():
                parm = node.parm(p_name)
                if parm:
                    old_val = parm.eval()
                    parm.set(p_val)
                    changes.append(f"Parameter {p_name} changed from {old_val} to {p_val}")
        
        return {"path": node.path(), "changes": changes}

    def delete_node(self, path):
        """Deletes a node from the scene."""
        node = hou.node(path)
        if not node:
            raise ValueError(f"Node not found: {path}")
        node_path = node.path()
        node_name = node.name()
        node.destroy()
        return {"deleted": node_path, "name": node_name}

    def get_node_info(self, path):
        """Returns detailed information about a single node."""
        node = hou.node(path)
        if not node:
            raise ValueError(f"Node not found: {path}")
        
        node_info = {
            "name": node.name(),
            "path": node.path(),
            "type": node.type().name(),
            "category": node.type().category().name(),
            "position": [node.position()[0], node.position()[1]],
            "color": list(node.color().rgb()) if node.color() else None,
            "is_bypassed": getattr(node, "isBypassed", lambda: None)(),
            "is_displayed": getattr(node, "isDisplayFlagSet", lambda: None)(),
            "is_rendered": getattr(node, "isRenderFlagSet", lambda: None)(),
            "parameters": [],
            "inputs": [],
            "outputs": []
        }

        # Limit to 20 parameters for brevity
        for i, parm in enumerate(node.parms()):
            if i >= 20:
                break
            node_info["parameters"].append({
                "name": parm.name(),
                "value": str(parm.eval()),
                "type": parm.parmTemplate().type().name()
            })

        # Inputs
        for i, in_node in enumerate(node.inputs()):
            if in_node:
                node_info["inputs"].append({
                    "index": i,
                    "name": in_node.name(),
                    "path": in_node.path(),
                    "type": in_node.type().name()
                })

        # Outputs
        for i, out_conn in enumerate(node.outputConnections()):
            out_node = out_conn.outputNode()
            node_info["outputs"].append({
                "index": i,
                "name": out_node.name(),
                "path": out_node.path(),
                "type": out_node.type().name(),
                "input_index": out_conn.inputIndex()
            })

        return node_info

    def execute_code(self, code):
        """Executes arbitrary Python code within Houdini."""
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        try:
            namespace = {"hou": hou}
            # Capture stdout/stderr during exec
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, namespace)

            # Success case: return execution status and captured output
            return {
                "executed": True,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue()
            }
        except Exception as e:
            # Failure case: print traceback to actual stderr for debugging in Houdini
            print("--- Houdini MCP: execute_code Error ---", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            print("--- End Error ---", file=sys.stderr)
            # Re-raise the exception so it's caught by execute_command
            # and reported back as a standard error message.
            raise Exception(f"Code execution error: {str(e)}")

    # -------------------------------------------------------------------------
    # Graph Editing & Introspection
    # -------------------------------------------------------------------------

    def _resolve_node(self, path):
        """Return the hou.Node at 'path' or raise a clear error."""
        node = hou.node(path)
        if not node:
            raise ValueError(f"Node not found: {path}")
        return node

    def _resolve_geometry_node(self, path):
        """
        Resolve 'path' to a SOP node that owns geometry. Accepts a SOP path
        directly, or a geometry container (OBJ node) whose display SOP is used.
        """
        node = self._resolve_node(path)
        if isinstance(node, hou.SopNode):
            return node
        display = getattr(node, "displayNode", lambda: None)()
        if display is not None:
            return display
        raise ValueError(
            f"{path} has no geometry. Pass a SOP path or a geometry container "
            f"(got {node.type().category().name()} node '{node.type().name()}')."
        )

    @staticmethod
    def _jsonable(value):
        """Convert HOM values (vectors, tuples, ...) to JSON-friendly types."""
        if isinstance(value, (bool, int, float, str)) or value is None:
            return value
        if isinstance(value, (hou.Vector2, hou.Vector3, hou.Vector4, hou.Quaternion)):
            return list(value)
        if isinstance(value, (tuple, list)):
            return [HoudiniMCPServer._jsonable(v) for v in value]
        return str(value)

    @staticmethod
    def _parm_value(parm_tuple):
        """Evaluate a parm tuple; single-component parms come back as scalars."""
        value = HoudiniMCPServer._jsonable(parm_tuple.eval())
        if isinstance(value, list) and len(parm_tuple) == 1:
            return value[0]
        return value

    def _cook_and_report(self, node):
        """Force-cook a node and return a structured pass/fail report."""
        start = time.time()
        cook_exception = None
        try:
            node.cook(force=True)
        except hou.OperationFailed as e:
            cook_exception = str(e)
        elapsed_ms = round((time.time() - start) * 1000.0, 1)

        errors = [e.strip() for e in node.errors() if e.strip()]
        warnings = [w.strip() for w in node.warnings() if w.strip()]
        if cook_exception and not errors:
            errors.append(cook_exception)

        return {
            "node": node.path(),
            "cooked": not errors,
            "cook_time_ms": elapsed_ms,
            "errors": errors,
            "warnings": warnings,
        }

    def connect_nodes(self, from_path, to_path, input_index=0, output_index=0):
        """Wire from_path's output into to_path's input."""
        src = self._resolve_node(from_path)
        dst = self._resolve_node(to_path)
        if src.parent() != dst.parent():
            raise ValueError(
                f"Nodes must share a parent network: {src.parent().path()} != {dst.parent().path()}"
            )
        dst.setInput(input_index, src, output_index)
        return {
            "from": src.path(),
            "to": dst.path(),
            "input_index": input_index,
            "output_index": output_index,
        }

    def disconnect_input(self, path, input_index=0):
        """Disconnect one input of a node."""
        node = self._resolve_node(path)
        previous = None
        for connection in node.inputConnections():
            if connection.inputIndex() == input_index:
                previous = connection.inputNode()
                break
        node.setInput(input_index, None)
        return {
            "node": node.path(),
            "input_index": input_index,
            "was_connected_to": previous.path() if previous else None,
        }

    def _set_one_parm(self, node, name, value):
        """
        Set a single parameter (or parm tuple). Returns (previous, new).
        Resolves menu tokens/labels for string values on menu parms, and
        suggests close parameter names when the name doesn't exist.
        """
        parm_tuple = node.parmTuple(name)
        if parm_tuple is None:
            candidates = [pt.name() for pt in node.parmTuples()]
            close = difflib.get_close_matches(name, candidates, n=3, cutoff=0.5)
            hint = f" Did you mean: {', '.join(close)}?" if close else ""
            raise ValueError(f"Parameter '{name}' not found on {node.path()}.{hint}")

        previous = self._parm_value(parm_tuple)

        if isinstance(value, (list, tuple)):
            if len(value) != len(parm_tuple):
                raise ValueError(
                    f"'{name}' has {len(parm_tuple)} component(s), got {len(value)} values"
                )
            parm_tuple.set(tuple(value))
        else:
            if len(parm_tuple) != 1:
                raise ValueError(
                    f"'{name}' has {len(parm_tuple)} components; pass a list of {len(parm_tuple)} values"
                )
            parm = parm_tuple[0]
            try:
                parm.set(value)
            except (TypeError, hou.OperationFailed):
                # A string that isn't a valid menu token: resolve label to index.
                if not isinstance(value, str):
                    raise
                try:
                    tokens = list(parm.menuItems())
                    labels = list(parm.menuLabels())
                except hou.OperationFailed:
                    raise TypeError(
                        f"'{name}' does not accept a string value on {node.path()}"
                    )
                if value in tokens:
                    parm.set(tokens.index(value))
                elif value in labels:
                    parm.set(labels.index(value))
                else:
                    raise ValueError(
                        f"'{value}' is not a menu token or label of '{name}'. "
                        f"Tokens: {tokens[:20]}"
                    )

        return previous, self._parm_value(parm_tuple)

    def set_parameters(self, path, parameters):
        """
        Set multiple parameters on a node in one call.
        Values: scalar for single parms, list for tuples (e.g. "t": [0, 1, 0]),
        menu token/label strings for menu parms.
        """
        node = self._resolve_node(path)
        if not isinstance(parameters, dict) or not parameters:
            raise ValueError("'parameters' must be a non-empty dict of {name: value}")

        applied, failed = [], []
        for name, value in parameters.items():
            try:
                previous, new = self._set_one_parm(node, name, value)
                applied.append({"name": name, "previous": previous, "value": new})
            except Exception as e:
                failed.append({"name": name, "error": str(e)})

        return {"node": node.path(), "set": applied, "failed": failed}

    def get_parameter_schema(self, path, pattern=None, offset=0, limit=50):
        """
        Describe a node's parameters: name, label, type, size, current value,
        defaults, ranges and menu options. Filter with a glob 'pattern'
        (matched against name and label), paginate with offset/limit.
        """
        node = self._resolve_node(path)
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))

        parm_tuples = node.parmTuples()
        if pattern:
            pat = pattern.lower()
            parm_tuples = [
                pt for pt in parm_tuples
                if fnmatch.fnmatch(pt.name().lower(), pat)
                or fnmatch.fnmatch(pt.parmTemplate().label().lower(), pat)
            ]

        entries = []
        for pt in parm_tuples[offset:offset + limit]:
            template = pt.parmTemplate()
            entry = {
                "name": pt.name(),
                "label": template.label(),
                "type": template.type().name(),
                "size": len(pt),
                "value": self._parm_value(pt),
            }
            try:
                default = self._jsonable(template.defaultValue())
                if isinstance(default, list) and len(default) == 1:
                    default = default[0]
                entry["default"] = default
            except AttributeError:
                pass
            if isinstance(template, (hou.FloatParmTemplate, hou.IntParmTemplate)):
                entry["min"] = template.minValue()
                entry["max"] = template.maxValue()
            menu_items = getattr(template, "menuItems", lambda: ())()
            if menu_items:
                menu_labels = template.menuLabels()
                entry["menu"] = [
                    {"token": t, "label": l}
                    for t, l in islice(zip(menu_items, menu_labels), 30)
                ]
                if len(menu_items) > 30:
                    entry["menu_truncated"] = len(menu_items)
            entries.append(entry)

        return {
            "node": node.path(),
            "node_type": node.type().name(),
            "total": len(parm_tuples),
            "offset": offset,
            "parameters": entries,
        }

    def set_node_flags(self, path, display=None, render=None, bypass=None, template=None):
        """Set node flags; only the flags passed (non-None) are touched."""
        node = self._resolve_node(path)
        requested = {
            "display": (display, "setDisplayFlag"),
            "render": (render, "setRenderFlag"),
            "bypass": (bypass, "bypass"),
            "template": (template, "setTemplateFlag"),
        }
        applied, unsupported = {}, []
        for flag, (value, method_name) in requested.items():
            if value is None:
                continue
            method = getattr(node, method_name, None)
            if method is None:
                unsupported.append(flag)
                continue
            method(bool(value))
            applied[flag] = bool(value)

        return {"node": node.path(), "applied": applied, "unsupported": unsupported}

    def layout_children(self, path):
        """Auto-layout all children of a network node."""
        node = self._resolve_node(path)
        node.layoutChildren()
        return {"node": node.path(), "children_laid_out": len(node.children())}

    def find_error_nodes(self, root_path="/obj", include_warnings=False,
                         max_nodes=2000, limit=50):
        """
        Walk the network under root_path and report nodes whose last cook
        produced errors (and optionally warnings). Does not force cooks.
        """
        root = self._resolve_node(root_path)
        found = []
        scanned = 0
        truncated = False
        stack = [root]

        while stack:
            if scanned >= max_nodes or len(found) >= limit:
                truncated = True
                break
            node = stack.pop()
            scanned += 1
            errors = [e.strip() for e in node.errors() if e.strip()]
            warnings = []
            if include_warnings:
                warnings = [w.strip() for w in node.warnings() if w.strip()]
            if errors or warnings:
                entry = {"path": node.path(), "type": node.type().name(), "errors": errors}
                if include_warnings:
                    entry["warnings"] = warnings
                found.append(entry)
            stack.extend(node.children())

        return {
            "root": root.path(),
            "scanned": scanned,
            "truncated": truncated,
            "error_node_count": len(found),
            "nodes": found,
        }

    def cook_node(self, path):
        """Force-cook a node and report errors, warnings and cook time."""
        return self._cook_and_report(self._resolve_node(path))

    # -------------------------------------------------------------------------
    # VEX Wrangles
    # -------------------------------------------------------------------------

    def _set_run_over(self, node, run_over):
        """Match 'run_over' against the wrangle's class menu (token or label)."""
        class_parm = node.parm("class")
        if class_parm is None:
            return None  # e.g. volumewrangle has no class parm
        want = run_over.lower().rstrip("s")
        tokens = list(class_parm.menuItems())
        labels = list(class_parm.menuLabels())
        for index, (token, label) in enumerate(zip(tokens, labels)):
            if want in (token.lower().rstrip("s"), label.lower().rstrip("s")):
                class_parm.set(index)
                return token
        raise ValueError(
            f"Unknown run_over '{run_over}'. Valid options: {tokens}"
        )

    def create_wrangle(self, parent_path, vex_code, name=None, run_over="points",
                       input_node=None, wrangle_type="attribwrangle"):
        """
        Create a wrangle SOP, set its VEX snippet, optionally wire an input,
        then cook it so VEX compile errors are reported immediately.
        """
        parent = self._resolve_node(parent_path)
        if parent.childTypeCategory() != hou.sopNodeTypeCategory():
            raise ValueError(
                f"{parent_path} is not a SOP network (cannot contain wrangles). "
                f"Pass a geometry container or SOP subnet."
            )

        node = parent.createNode(wrangle_type, node_name=name)
        try:
            snippet = node.parm("snippet")
            if snippet is None:
                raise ValueError(f"'{wrangle_type}' has no 'snippet' parameter")
            snippet.set(vex_code)
            run_over_token = self._set_run_over(node, run_over)
            if input_node:
                node.setInput(0, self._resolve_node(input_node))
            node.moveToGoodPosition()
        except Exception:
            node.destroy()  # don't leave a half-configured node behind
            raise

        return {
            "path": node.path(),
            "type": wrangle_type,
            "run_over": run_over_token,
            "validation": self._cook_and_report(node),
        }

    def set_wrangle_code(self, path, vex_code, validate=True):
        """Replace the VEX snippet on an existing wrangle and re-validate."""
        node = self._resolve_node(path)
        snippet = node.parm("snippet")
        if snippet is None:
            raise ValueError(f"{path} has no 'snippet' parameter (not a wrangle)")
        snippet.set(vex_code)
        result = {"path": node.path(), "code_length": len(vex_code)}
        if validate:
            result["validation"] = self._cook_and_report(node)
        return result

    # -------------------------------------------------------------------------
    # Geometry Introspection
    # -------------------------------------------------------------------------

    @staticmethod
    def _attrib_summary(attribs):
        return [
            {"name": a.name(), "type": a.dataType().name(), "size": a.size()}
            for a in attribs
        ]

    def get_geometry_info(self, path):
        """
        Summarize a node's geometry: element counts, bounding box, attributes
        and group names. Accepts a SOP or a geometry container path.
        """
        sop = self._resolve_geometry_node(path)
        geo = sop.geometry()
        if geo is None:
            report = self._cook_and_report(sop)
            raise ValueError(
                f"{sop.path()} produced no geometry. Cook errors: {report['errors']}"
            )

        bbox = geo.boundingBox()
        return {
            "node": sop.path(),
            "point_count": geo.intrinsicValue("pointcount"),
            "primitive_count": geo.intrinsicValue("primitivecount"),
            "vertex_count": geo.intrinsicValue("vertexcount"),
            "bounding_box": {
                "min": list(bbox.minvec()),
                "max": list(bbox.maxvec()),
                "size": list(bbox.sizevec()),
                "center": list(bbox.center()),
            },
            "attributes": {
                "point": self._attrib_summary(geo.pointAttribs()),
                "primitive": self._attrib_summary(geo.primAttribs()),
                "vertex": self._attrib_summary(geo.vertexAttribs()),
                "detail": self._attrib_summary(geo.globalAttribs()),
            },
            "groups": {
                "point": [g.name() for g in geo.pointGroups()],
                "primitive": [g.name() for g in geo.primGroups()],
            },
        }

    def get_geometry_data(self, path, element="points", attributes=None,
                          start=0, limit=100):
        """
        Read actual attribute values from geometry, paginated.
        element: 'points' or 'primitives'. attributes: list of names
        (default: position for points, type info for prims).
        """
        sop = self._resolve_geometry_node(path)
        geo = sop.geometry()
        if geo is None:
            raise ValueError(f"{sop.path()} has no geometry (node may not cook)")

        start = max(0, int(start))
        limit = max(1, min(int(limit), 500))

        if element == "points":
            total = geo.intrinsicValue("pointcount")
            available = {a.name(): a for a in geo.pointAttribs()}
            iterator = geo.iterPoints()
        elif element == "primitives":
            total = geo.intrinsicValue("primitivecount")
            available = {a.name(): a for a in geo.primAttribs()}
            iterator = geo.iterPrims()
        else:
            raise ValueError(f"element must be 'points' or 'primitives', got '{element}'")

        if attributes:
            missing = [a for a in attributes if a not in available]
            if missing:
                raise ValueError(
                    f"Attribute(s) {missing} not found on {element}. "
                    f"Available: {sorted(available)}"
                )
            selected = [available[a] for a in attributes]
        else:
            selected = [available["P"]] if "P" in available else []

        rows = []
        for elem in islice(iterator, start, start + limit):
            row = {"number": elem.number()}
            if element == "primitives":
                row["type"] = elem.type().name()
            for attrib in selected:
                row[attrib.name()] = self._jsonable(elem.attribValue(attrib))
            rows.append(row)

        return {
            "node": sop.path(),
            "element": element,
            "total": total,
            "start": start,
            "count": len(rows),
            "data": rows,
        }

    # -------------------------------------------------------------------------
    # set_material (now completed)
    # -------------------------------------------------------------------------
    def set_material(self, node_path, material_type="principledshader", name=None, parameters=None):
        """
        Creates or applies a material to an OBJ node. 
        For example, we can create a Principled Shader in /mat 
        and assign it to a geometry node or set the 'shop_materialpath'.
        """
        try:
            target_node = hou.node(node_path)
            if not target_node:
                raise ValueError(f"Node not found: {node_path}")
            
            # Verify it's an OBJ node (i.e., category Object)
            if target_node.type().category().name() != "Object":
                raise ValueError(
                    f"Node {node_path} is not an OBJ-level node and cannot accept direct materials."
                )

            # Attempt to create/find a material in /mat (or /shop)
            mat_context = hou.node("/mat")
            if not mat_context:
                # Fallback: try /shop if /mat doesn't exist
                mat_context = hou.node("/shop")
                if not mat_context:
                    raise RuntimeError("No /mat or /shop context found to create materials.")

            mat_name = name or (f"{material_type}_auto")
            mat_node = mat_context.node(mat_name)
            if not mat_node:
                # Create a new material node
                mat_node = mat_context.createNode(material_type, mat_name)

            # Apply any parameter overrides
            if parameters:
                for k, v in parameters.items():
                    p = mat_node.parm(k)
                    if p:
                        p.set(v)

            # Now assign this material to the OBJ node
            # Typically, you either set a "shop_materialpath" parameter 
            # or inside the geometry, you create a Material SOP.
            mat_parm = target_node.parm("shop_materialpath")
            if mat_parm:
                mat_parm.set(mat_node.path())
            else:
                # If there's a geometry node inside, we might make or update a Material SOP
                geo_sop = target_node.node("geometry")
                if not geo_sop:
                    raise RuntimeError("No 'geometry' node found inside OBJ to apply material to.")
                
                material_sop = geo_sop.node("material1")
                if not material_sop:
                    material_sop = geo_sop.createNode("material", "material1")
                    # Hook it up to the chain
                    # For a brand-new geometry node, there's often a 'file1' SOP or similar
                    first_sop = None
                    for c in geo_sop.children():
                        if c.isDisplayFlagSet():
                            first_sop = c
                            break
                    if first_sop:
                        material_sop.setFirstInput(first_sop)
                    material_sop.setDisplayFlag(True)
                    material_sop.setRenderFlag(True)

                # The Material SOP typically has shop_materialpath1, shop_materialpath2, etc.
                mat_sop_parm = material_sop.parm("shop_materialpath1")
                if mat_sop_parm:
                    mat_sop_parm.set(mat_node.path())
                else:
                    raise RuntimeError(
                        "No shop_materialpath1 on Material SOP to assign the material."
                    )

            return {
                "status": "ok",
                "material_node": mat_node.path(),
                "applied_to": target_node.path(),
            }

        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": str(e), "node": node_path}

    # -------------------------------------------------------------------------
    # NEW OPUS Import Handler and Helpers
    # -------------------------------------------------------------------------
    
    def _download_file(self, url, dest_folder):
        """
        Download from 'url' to local 'dest_folder', returning local filepath.
        Helper for import_opus_url.
        """
        if not url:
            raise ValueError("Download URL cannot be empty.")
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder, exist_ok=True)
    
        # Generate filename, ensure it ends with .zip if possible
        try:
            path_part = urlparse(url).path
            filename = os.path.basename(path_part) if path_part else f"{uuid.uuid4()}.zip"
            if not filename.lower().endswith('.zip'):
                filename += ".zip"
        except Exception:
             filename = f"{uuid.uuid4()}.zip" # Fallback
             
        local_path = os.path.join(dest_folder, filename)
        # Ensure forward slashes
        local_path = local_path.replace('\\', '/')
        print(f"  Downloading {url} => {local_path}")
    
        try:
            # Use requests (already imported) for downloading
            resp = requests.get(url, stream=True, timeout=60) # Add timeout
            resp.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"  Download complete: {local_path}")
            return local_path
        except requests.exceptions.RequestException as e:
             print(f"  Download failed: {str(e)}")
             # Clean up potentially incomplete file
             if os.path.exists(local_path):
                  try: os.remove(local_path)
                  except: pass
             raise ConnectionError(f"Failed to download file: {str(e)}") from e

    def _unzip_file(self, zip_path, dest_folder):
        """
        Unzip 'zip_path' into 'dest_folder'. Return list of extracted file paths.
        Helper for import_opus_url.
        
        Validates each entry to prevent ZipSlip (path traversal) attacks.
        """
        extracted_files = []
        dest_folder = os.path.realpath(dest_folder)
        print(f"  Unzipping {zip_path} => {dest_folder}")
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for info in z.infolist():
                    extracted_path = os.path.realpath(os.path.join(dest_folder, info.filename))
                    if not extracted_path.startswith(dest_folder + os.sep) and extracted_path != dest_folder:
                        raise ValueError(f"ZipSlip detected: entry '{info.filename}' escapes destination folder")
                z.extractall(dest_folder)
                extracted_files = [os.path.join(dest_folder, p).replace('\\', '/') for p in z.namelist()]
            print(f"  Unzip complete. Extracted {len(extracted_files)} files.")
            return extracted_files
        except zipfile.BadZipFile as e:
             print(f"  Unzip failed: Bad zip file - {str(e)}")
             raise ValueError(f"Downloaded file is not a valid zip file: {str(e)}") from e
        except Exception as e:
             print(f"  Unzip failed: {str(e)}")
             raise IOError(f"Failed to unzip file: {str(e)}") from e

    def handle_import_opus_url(self, url, node_name="opus_import"):
        """
        Downloads a ZIP file from URL, unzips it, finds a USD file,
        and imports it into a new subnet in Houdini.
        """
        temp_dir = None
        zip_filepath = None
        try:
            # Create a unique temporary directory for download and extraction
            temp_dir = tempfile.mkdtemp(prefix="houdini_opus_import_")
            print(f"Created temporary directory: {temp_dir}")

            # Download the zip file
            zip_filepath = self._download_file(url, temp_dir)
            if not zip_filepath or not os.path.exists(zip_filepath):
                 raise FileNotFoundError("Download failed or file not found.")

            # Unzip the file
            extract_dir = os.path.join(temp_dir, "extracted")
            extracted_files = self._unzip_file(zip_filepath, extract_dir)
            if not extracted_files:
                 raise FileNotFoundError("Unzip failed or zip file was empty.")

            # Find the primary USD file (e.g., .usd, .usda, .usdc)
            # Also check for GLTF/GLB as the zip name was gltf.zip
            import_file = None
            possible_usd_extensions = (".usd", ".usda", ".usdc")
            possible_gltf_extensions = (".gltf", ".glb")
            
            # Prioritize USD files
            for f in extracted_files:
                if f.lower().endswith(possible_usd_extensions):
                    import_file = f
                    print(f"Found USD file: {import_file}")
                    break
            
            # If no USD found, check for GLTF/GLB
            if not import_file:
                for f in extracted_files:
                     if f.lower().endswith(possible_gltf_extensions):
                        import_file = f
                        print(f"Found GLTF/GLB file: {import_file}")
                        break # Take the first match
            
            if not import_file:
                 raise FileNotFoundError(f"No USD ({possible_usd_extensions}) or GLTF/GLB ({possible_gltf_extensions}) file found in the extracted contents.")

            # --- Import into Houdini using gltf_hierarchy node directly in /obj ---
            obj_context = hou.node("/obj")
            if not obj_context:
                 raise RuntimeError("Cannot find /obj context in Houdini.")
            
            # Create a gltf_hierarchy node directly in /obj
            node_actual_name = node_name or "opus_import"
            gltf_node = obj_context.createNode("gltf_hierarchy", node_actual_name)
            if not gltf_node:
                 raise RuntimeError(f"Failed to create gltf_hierarchy node '{node_actual_name}' in /obj.")
            print(f"Created gltf_hierarchy node: {gltf_node.path()}")

            # Set the filename parameter
            print(f"Setting filename on {gltf_node.path()} to {import_file}")
            try:
                 # Parameter name might vary slightly, check common names
                 param_name = "filename"
                 if not gltf_node.parm(param_name):
                      param_name = "file"
                      if not gltf_node.parm(param_name):
                           raise RuntimeError(f"Could not find filename parameter ('filename' or 'file') on {gltf_node.path()}")
                           
                 gltf_node.parm(param_name).set(import_file)
                 print(f"Set parameter '{param_name}' successfully.")
            except hou.Error as parm_e:
                 print(f"Error setting filename parameter on gltf_hierarchy node: {parm_e}")
                 raise RuntimeError(f"Failed to set filename on gltf_hierarchy node: {parm_e}") from parm_e

            # Press the Build Scene button
            build_scene_parm = gltf_node.parm("buildscene")
            if build_scene_parm:
                 print(f"Pressing 'Build Scene' button on {gltf_node.path()}")
                 build_scene_parm.pressButton()
            else:
                 print(f"Warning: Could not find 'buildscene' parameter on {gltf_node.path()}. Scene might not be built automatically.")

            # Layout nodes in /obj (optional, might be useful)
            obj_context.layoutChildren()
            
            # Return the path to the gltf_hierarchy node
            return {"status": "success", "imported_node_path": gltf_node.path(), "imported_file": import_file}

        except Exception as e:
            error_message = f"OPUS Import Failed: {str(e)}"
            print(error_message)
            traceback.print_exc() # Print full traceback to Houdini console
            # Re-raise to be caught by execute_command and sent back as standard error
            raise Exception(error_message) from e

        finally:
            # --- Cleanup --- 
            # Only delete the downloaded zip file, keep the extracted contents
            # as the gltf_hierarchy SOP needs to reference them.
            if zip_filepath and os.path.exists(zip_filepath):
                try:
                    os.remove(zip_filepath)
                    print(f"Cleaned up temporary zip file: {zip_filepath}")
                except Exception as cleanup_zip_e:
                    print(f"Warning: Failed to clean up temporary zip file {zip_filepath}: {cleanup_zip_e}")
            
            # Keep the temp_dir itself and the extracted folder for now
            # If keeping the temp dir is problematic, we could copy the needed files elsewhere
            # before deleting the temp_dir.
            # if temp_dir and os.path.exists(temp_dir):
            #     try:
            #         shutil.rmtree(temp_dir)
            #         print(f"Cleaned up temporary directory: {temp_dir}")
            #     except Exception as cleanup_e:
            #         print(f"Warning: Failed to clean up temporary directory {temp_dir}: {cleanup_e}")

    # -------------------------------------------------------------------------
    # NEW Render Command Handlers (using HoudiniMCPRender.py)
    # -------------------------------------------------------------------------
    # def _check_render_lib(self):
    #     """Helper to check if the render library was imported."""
    #     if HMCPLib is None:
    #         raise RuntimeError("HoudiniMCPRender library not available. Cannot execute render commands.")

    def _process_rendered_image(self, filepath, camera_path=None, view_name=None):
        """
        Helper to validate and return metadata for a rendered image file.
        Returns the file path so the caller can open it directly — avoids
        base64-encoding large image data into the response.
        """
        if not filepath or not os.path.exists(filepath):
            return {"status": "error", "message": f"Rendered file not found: {filepath}", "origin": "_process_rendered_image"}

        # Determine format from extension
        _, ext = os.path.splitext(filepath)
        fmt = ext[1:].lower() if ext else 'unknown'

        # Get resolution from the camera if possible
        resolution = [0, 0]
        if camera_path:
            cam_node = hou.node(camera_path)
            if cam_node and cam_node.parm("resx") and cam_node.parm("resy"):
                resolution = [cam_node.parm("resx").eval(), cam_node.parm("resy").eval()]

        result_data = {
            "status": "success",
            "format": fmt,
            "resolution": resolution,
            "filepath": filepath,
        }
        if view_name:
            result_data["view_name"] = view_name

        return result_data

        # except Exception as e:
        #     error_message = f"Failed to process rendered image {filepath}: {str(e)}"
        #     print(error_message)
        #     traceback.print_exc()
        #     return {"status": "error", "message": error_message, "origin": "_process_rendered_image"}
        # finally:
        #     # Clean up the temporary file
        #     if os.path.exists(filepath):
        #         try:
        #             os.remove(filepath)
        #             print(f"Cleaned up temporary render file: {filepath}")
        #         except Exception as cleanup_e:
        #             print(f"Warning: Failed to clean up temporary render file {filepath}: {cleanup_e}")

    def handle_render_single_view(self, orthographic=False, rotation=(0, 90, 0), render_path=None, render_engine="opengl", karma_engine="cpu"):
        """Handles the 'render_single_view' command."""
        # self._check_render_lib()
        
        # Use a temporary directory for the render output
        if not render_path:
            render_path = tempfile.gettempdir()
            
        try:
            # Ensure rotation is a tuple
            if isinstance(rotation, list): rotation = tuple(rotation)
            
            print(f"Calling HoudiniMCPRender.render_single_view with rotation={rotation}, ortho={orthographic}, engine={render_engine}...")
            filepath = render_single_view(
                orthographic=orthographic,
                rotation=rotation,
                render_path=render_path,
                render_engine=render_engine,
                karma_engine=karma_engine
            )
            print(f"render_single_view returned filepath: {filepath}")

            # Process the result
            # Determine camera path used (it's always /obj/MCP_CAMERA for this func)
            camera_path = "/obj/MCP_CAMERA"
            return self._process_rendered_image(filepath, camera_path)

        except Exception as e:
            error_message = f"Render Single View Failed: {str(e)}"
            print(error_message)
            traceback.print_exc()
            return {"status": "error", "message": error_message, "origin": "handle_render_single_view"}

    def handle_render_quad_view(self, orthographic=True, render_path=None, render_engine="opengl", karma_engine="cpu"):
        """Handles the 'render_quad_view' command."""
        # self._check_render_lib()
        
        if not render_path:
            render_path = tempfile.gettempdir()

        try:
            print(f"Calling HoudiniMCPRender.render_quad_view with ortho={orthographic}, engine={render_engine}...")
            filepaths = render_quad_view(
                orthographic=orthographic,
                render_path=render_path,
                render_engine=render_engine,
                karma_engine=karma_engine
            )
            print(f"render_quad_view returned filepaths: {filepaths}")

            # Process each resulting file
            results = []
            camera_path = "/obj/MCP_CAMERA" # Same camera is reused and modified
            for fp in filepaths:
                # Extract view name from filename if possible (e.g., MCP_OGL_RENDER_front_ortho.jpg -> front)
                view_name = None
                try:
                     filename = os.path.basename(fp)
                     parts = filename.split('_')
                     if len(parts) > 2: # Look for the part after engine/render type
                         view_name = parts[2] 
                except:
                     pass # Ignore errors extracting view name
                     
                results.append(self._process_rendered_image(fp, camera_path, view_name))
                
            # Return the list of results
            return {"status": "success", "results": results}

        except Exception as e:
            error_message = f"Render Quad View Failed: {str(e)}"
            print(error_message)
            traceback.print_exc()
            return {"status": "error", "message": error_message, "origin": "handle_render_quad_view"}

    def handle_render_specific_camera(self, camera_path, render_path=None, render_engine="opengl", karma_engine="cpu"):
        """Handles the 'render_specific_camera' command."""
        # self._check_render_lib()
        
        if not render_path:
            render_path = tempfile.gettempdir()
            
        if not camera_path or not hou.node(camera_path):
             return {"status": "error", "message": f"Camera path '{camera_path}' is invalid or node not found.", "origin": "handle_render_specific_camera"}

        try:
            print(f"Calling HoudiniMCPRender.render_specific_camera for camera={camera_path}, engine={render_engine}...")
            filepath = render_specific_camera(
                camera_path=camera_path,
                render_path=render_path,
                render_engine=render_engine,
                karma_engine=karma_engine
            )
            print(f"render_specific_camera returned filepath: {filepath}")

            # Process the result, using the provided camera_path
            return self._process_rendered_image(filepath, camera_path)

        except Exception as e:
            error_message = f"Render Specific Camera Failed: {str(e)}"
            print(error_message)
            traceback.print_exc()
            return {"status": "error", "message": error_message, "origin": "handle_render_specific_camera"}

    # -------------------------------------------------------------------------
    # Existing Placeholder asset library methods
    # -------------------------------------------------------------------------
    def get_asset_categories(self):
        """Placeholder for an asset library feature (e.g., Poly Haven)."""
        return {"error": "get_asset_categories not implemented"}

    def search_assets(self):
        """Placeholder for asset search logic."""
        return {"error": "search_assets not implemented"}

    def import_asset(self):
        """Placeholder for asset import logic."""
        return {"error": "import_asset not implemented"}
