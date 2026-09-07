"""Host the MCP plugin headlessly in hython for testing.

Loads server.py and pumps _process_server() manually (no Qt event loop
needed), so the full framed-TCP + handler stack runs in a real hou
environment without a Houdini GUI session.

Usage:
    hython tests/headless_host.py [port]    # default port 19878
Then, in another shell:
    uv run python tests/test_tools.py [port]
"""
import os
import socket
import sys
import time

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 19878
SERVER_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server.py")

with open(SERVER_PY, "r", encoding="utf-8") as f:
    code = f.read()
# Run standalone: the render module needs the installed package; render
# handlers are not under test here.
code = code.replace("from .HoudiniMCPRender import *", "")

namespace = {"__name__": "houdinimcp_headless_test", "__file__": SERVER_PY}
exec(compile(code, SERVER_PY, "exec"), namespace)

server = namespace["HoudiniMCPServer"](host="127.0.0.1", port=PORT)

# Same socket setup as start(), but pumped by a loop instead of a QTimer
# (hython has no Qt event loop).
server.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.server_socket.bind((server.host, server.port))
server.server_socket.listen(4)
server.server_socket.setblocking(False)
server.running = True
print(f"HEADLESS HOST READY on {server.host}:{server.port}", flush=True)

deadline = time.time() + 600  # auto-exit after 10 minutes
while time.time() < deadline:
    server._process_server()
    time.sleep(0.02)
