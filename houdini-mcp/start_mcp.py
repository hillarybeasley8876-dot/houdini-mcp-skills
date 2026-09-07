"""Start the local Houdini MCP listener after the UI is ready."""
from pathlib import Path
import json
import os
import sys
from datetime import datetime, timezone
import hou

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("HOUDINI_MCP_PORT", "9877"))
python_path = str(ROOT / "scripts" / "python")
if python_path not in sys.path:
    sys.path.insert(0, python_path)
if hou.isUIAvailable():
    import houdinimcp
    houdinimcp.initialize_plugin()
    houdinimcp.start_server(host="127.0.0.1", port=PORT)
    server = getattr(hou.session, "houdinimcp_server", None)
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "houdini_version": hou.applicationVersionString(),
        "pref_dir": hou.getenv("HOUDINI_USER_PREF_DIR"),
        "running": houdinimcp.is_server_running(),
        "host": "127.0.0.1",
        "port": PORT,
        "event_loop_registered": bool(getattr(server, "_loop_callback_registered", False)),
    }
    (ROOT / "last-start.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print("[houdinimcp] " + json.dumps(status))
