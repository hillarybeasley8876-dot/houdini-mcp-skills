import hou
from .server import HoudiniMCPServer

def start_server(host='127.0.0.1', port=9877):
    existing = getattr(hou.session, "houdinimcp_server", None)
    if existing is not None and existing.running:
        print(f"HoudiniMCP Server is already running on {existing.host}:{existing.port}")
        return
    if existing is not None and not existing.running:
        existing.stop()
    server = HoudiniMCPServer(host=host, port=port)
    server.start()
    if server.running:
        hou.session.houdinimcp_server = server
    else:
        hou.session.houdinimcp_server = None

def stop_server():
    existing = getattr(hou.session, "houdinimcp_server", None)
    if existing is not None:
        existing.stop()
        hou.session.houdinimcp_server = None
    else:
        print("HoudiniMCP Server is not running.")

def is_server_running():
    existing = getattr(hou.session, "houdinimcp_server", None)
    return existing is not None and existing.running

def restart_server(host='127.0.0.1', port=9877):
    stop_server()
    start_server(host=host, port=port)

def initialize_plugin():
    if not hasattr(hou.session, "houdinimcp_use_assetlib"):
        hou.session.houdinimcp_use_assetlib = False
