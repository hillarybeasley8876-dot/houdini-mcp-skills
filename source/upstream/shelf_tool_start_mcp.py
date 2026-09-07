# HoudiniMCP — Start Server shelf tool
# Copy this into a Houdini shelf tool (right-click shelf → New Tool → Script tab)
#
# Prerequisites:
#   - houdinimcp package must be in Houdini's Python path
#   - See CLAUDE.md for setup instructions

import houdinimcp

if houdinimcp.is_server_running():
    server = hou.session.houdinimcp_server
    print(f"HoudiniMCP Server is already running on {server.host}:{server.port}")
else:
    houdinimcp.start_server()
    if houdinimcp.is_server_running():
        server = hou.session.houdinimcp_server
        print(f"HoudiniMCP Server started on {server.host}:{server.port}")
    else:
        print("HoudiniMCP Server failed to start")
