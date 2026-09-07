# Houdini 22 / Python 3.13 UI-ready hook.
from pathlib import Path
import runpy
try:
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "start_mcp.py"))
except Exception:
    import traceback
    print("[houdinimcp] startup failed")
    traceback.print_exc()
