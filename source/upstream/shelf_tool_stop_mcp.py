# HoudiniMCP — Stop Server shelf tool
# Copy this into a Houdini shelf tool (right-click shelf → New Tool → Script tab)

import houdinimcp

if houdinimcp.is_server_running():
    houdinimcp.stop_server()
    print("HoudiniMCP Server stopped")
else:
    print("HoudiniMCP Server is not running")
