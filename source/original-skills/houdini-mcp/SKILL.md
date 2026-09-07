---
name: houdini-mcp
description: Connect Claude Code to a running Houdini session via MCP. Use when the user wants to set up, restart, debug, or verify the Houdini MCP integration on this machine. Examples - "重连 houdini mcp", "houdini mcp 不通了", "set up houdini mcp", "reload houdini plugin".
---

# Houdini MCP Connection Skill

## Current local installation — Houdini 22 / Codex (2026-09-06)

Use this installation for Houdini 22. The Houdini 21 paths and port 9876 below are legacy notes; the old plugin files were absent when checked on 2026-09-06.

- Houdini: `H:\Program Files\Side Effects Software\Houdini 22.0.368\bin\houdini.exe` (Python 3.13).
- Plugin root and complete instructions: `C:\Users\nieyi\Documents\houdini22.0\houdini-mcp\INSTALLATION.md`.
- Plugin package: `<root>\scripts\python\houdinimcp`; independent Python 3.12 bridge at `<root>\.venv\Scripts\python.exe`.
- Codex registration: `~/.codex/config.toml`, `[mcp_servers.houdini]`, bridge argument `--port 9877`. Host `127.0.0.1`. **9876 is reserved for Blender MCP.**
- Autostart: package `Documents\houdini22.0\packages\houdinimcp.json` adds root to Houdini path; `python3.13libs/uiready.py` calls `<root>\start_mcp.py`. Also installed package entries under `~\houdini22.0\packages` for alternate preference resolution.
- Current upstream `__init__.py` does not autostart on import: explicitly call `initialize_plugin()` then `start_server(host='127.0.0.1', port=9877)`.
- Current patched server uses `server_socket`, not the legacy `socket` field. Event polling uses `hou.ui.addEventLoopCallback`; FastMCP uses `instructions=`. Protocol is 4-byte big-endian length followed by UTF-8 JSON.
- Local SHFS assets are on C: while Houdini is on H:. `packages/shfs-location.json` points SHFS to `C:/Program Files/Side Effects Software/shfs`, fixing the startup warning.
- Verified actual GUI autostart, stdio handshake, 25 tools, scene reads, and read-only Python execution. Results: `<root>\validation-ui.json`, `<root>\validation-mcp.json`. Six OPUS tools require optional RapidAPI configuration.
- Manual load into an already running Houdini Python Shell (one line): `exec(compile(open(r'C:/Users/nieyi/Documents/houdini22.0/houdini-mcp/start_mcp.py', encoding='utf-8').read(), 'start_mcp.py', 'exec'))`.
- Read the installation instructions before reusing the legacy recipes below. First install requires restarting Codex to load newly registered tools.

This skill restores or sets up Claude → Houdini MCP control on this Windows box. The full architecture and file paths are in the user's memory `houdini_mcp_integration.md` — read that first if context is missing.

## Architecture (one-screen recap)

```
Claude Code  ──stdio──▶  bridge venv python (.venv\Scripts\python.exe houdini_mcp_server.py)
                                  │
                                  │ TCP localhost:9876
                                  ▼
                         Houdini UI process
                         (houdinimcp Python plugin)
```

- Bridge process is spawned by Claude Code per session via `mcpServers` config in `~/.claude/settings.json` (or `~/.claude.json`).
- Houdini-side plugin auto-loads via `Documents\houdini21.0\scripts\123.py` and listens on 9876 inside the running UI process.
- **Houdini must be the UI process** (`houdini.exe` / `hindie.exe` / `houdinifx.exe`), not `hython.exe` — plugin uses Qt which only exists in UI session.

## Diagnostic flow (run in this order)

When the user reports "MCP doesn't work" or wants to verify:

1. **Is Houdini running?**
   ```powershell
   Get-Process | ? Name -match 'hindie|houdini|houdinicore|houdinifx' | Format-Table Id,Name
   ```
   If empty → ask user to start Houdini, stop here.

2. **Is port 9876 listening?**
   ```powershell
   Get-NetTCPConnection -LocalPort 9876 -ErrorAction SilentlyContinue
   ```
   If empty → plugin isn't loaded; jump to **Reload plugin**.

3. **Smoke test the round-trip**: call `mcp__houdini__get_scene_info` (no args). Returns scene JSON → done. Returns `mcp_server_send_command_timeout` → plugin loaded but tick mechanism is broken; jump to **Apply patches**.

## Reload plugin (one-liner)

Have the user paste this **single-line** snippet into Houdini's Python Shell (multi-line paste breaks the Houdini REPL):

```python
import sys; hou.session.houdinimcp_server.stop() if getattr(hou.session,'houdinimcp_server',None) else None; [sys.modules.pop(m) for m in list(sys.modules) if m=='houdinimcp' or m.startswith('houdinimcp.')]; hou.session.houdinimcp_server=None; import houdinimcp; print('reloaded; cb registered=', hou.session.houdinimcp_server._loop_callback_registered)
```

Expected output ends with `cb registered= True` and `HoudiniMCP server started on localhost:9876`.

## Apply patches (when capoom upstream is freshly downloaded)

The vanilla `capoomgit/houdini-mcp` server.py uses `PySide2` and a free-floating `QtCore.QTimer`. Both fail under Houdini 21 (PySide6 only) **and** the QTimer never auto-fires reliably from the Python Shell context. Two patches needed in `Documents\houdini21.0\scripts\python\houdinimcp\server.py`:

### Patch 1 — PySide6 fallback (line ~12)
Replace:
```python
from PySide2 import QtWidgets, QtCore
```
with:
```python
try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore
```

### Patch 2 — Use Houdini's UI event loop (replace `start()` and `stop()` methods)

The whole `start()` / `stop()` / `_io_loop()` cluster gets replaced. Use `hou.ui.addEventLoopCallback(self._process_server)` — Houdini's official UI tick. The legacy `_process_server()` method below it stays untouched as the actual handler.

Replace `start()` body with:
```python
    def start(self):
        """Begin listening on the given port; register a callback on Houdini's UI event loop."""
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.socket.setblocking(False)
            hou.ui.addEventLoopCallback(self._process_server)
            self._loop_callback_registered = True
            print(f"HoudiniMCP server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()
```

Replace `stop()` body with:
```python
    def stop(self):
        """Stop listening; unregister callback and close sockets."""
        self.running = False
        if getattr(self, '_loop_callback_registered', False):
            try:
                hou.ui.removeEventLoopCallback(self._process_server)
            except Exception:
                pass
            self._loop_callback_registered = False
        if self.socket:
            try: self.socket.close()
            except Exception: pass
        if self.client:
            try: self.client.close()
            except Exception: pass
        self.socket = None
        self.client = None
        print("HoudiniMCP server stopped")
```

After patching, run the **Reload plugin** one-liner above.

## What does NOT work (avoid suggesting)

- `QtCore.QTimer()` without parent under PySide6: created but never fires when triggered from Python Shell context.
- `QtCore.QTimer(hou.qt.mainWindow())`: `hou.qt.mainWindow()` returns `None` in some startup contexts → same problem.
- `hdefereval.executeDeferredAfterWaiting(cb, 0.1)` self-rescheduling: only fires when user UI is actually idle — never in a self-loop.
- Background thread + `hdefereval.executeInMainThreadWithResult`: dispatch hangs because main-thread callback delivery shares the same broken trigger.
- Only `hou.ui.addEventLoopCallback` is fully reliable for periodic main-thread polling under Houdini 21.

## Cold-install from scratch (rare)

If the plugin directory doesn't exist yet, do this:

1. `mkdir -p "C:/Users/nieyi/Documents/houdini21.0/scripts/python/houdinimcp" "C:/Users/nieyi/Documents/houdini21.0/toolbar"`
2. Curl 5 files from `https://raw.githubusercontent.com/capoomgit/houdini-mcp/main/`: `__init__.py`, `pyproject.toml`, `server.py`, `HoudiniMCPRender.py`, `houdini_mcp_server.py`
3. Write `urls.env` with empty `RAPIDAPI_KEY=`
4. Apply the two patches above to `server.py`
5. Install uv: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
6. `cd` to plugin dir, `uv venv`, `uv pip install "mcp[cli]>=1.4.1" requests python-dotenv`
7. Write `Documents\houdini21.0\scripts\123.py` containing:
   ```python
   try:
       import houdinimcp
       print("[houdinimcp] auto-started on localhost:9876")
   except Exception as e:
       print(f"[houdinimcp] auto-start failed: {e}")
   ```
8. Add to `~/.claude/settings.json` under top-level `mcpServers`:
   ```json
   "mcpServers": {
     "houdini": {
       "command": "C:\\Users\\nieyi\\Documents\\houdini21.0\\scripts\\python\\houdinimcp\\.venv\\Scripts\\python.exe",
       "args": ["C:\\Users\\nieyi\\Documents\\houdini21.0\\scripts\\python\\houdinimcp\\houdini_mcp_server.py"]
     }
   }
   ```
9. User restarts Claude Code session → new MCP server picked up. User starts Houdini → plugin auto-starts via 123.py.

## Tools exposed once connected

- `mcp__houdini__get_scene_info` — scene metadata + node list
- `mcp__houdini__create_node` — create a single node (`node_type`, `parent_path`, `name`)
- `mcp__houdini__execute_houdini_code` — **most powerful**: arbitrary `hou.*` Python; use this for anything beyond simple node creation
- `mcp__houdini__render_single_view` / `render_quad_views` / `render_specific_camera` — viewport / Karma renders. `render_path` is treated as **base directory**, not file name.
- `mcp__houdini__opus_*` — exposed but will error at call time (no RapidAPI key).

## Gotchas

- **Path discrepancy**: `hindie.exe` uses `Documents/houdini21.0/`, `hython.exe` uses `~/houdini21.0/`. Plugin lives under the UI dir; never trust `hython` for path resolution.
- **Multi-line paste in Houdini Python Shell**: lines get concatenated and break syntax. Always use single-line one-liners (with `;`).
- **Bridge connects fine without Houdini**: `claude mcp list` shows ✓ even when Houdini is closed. Only individual tool calls fail with "Could not connect to Houdini on port 9876".
