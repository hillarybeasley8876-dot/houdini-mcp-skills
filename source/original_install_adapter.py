from pathlib import Path
import json
import shutil
import subprocess

root = Path(__file__).resolve().parent
upstream = root / 'upstream'
plugin = root / 'scripts' / 'python' / 'houdinimcp'
plugin.mkdir(parents=True, exist_ok=True)
for name in ('__init__.py', 'server.py', 'HoudiniMCPRender.py', 'houdini_mcp_server.py', 'LICENSE', 'README.md', 'pyproject.toml'):
    shutil.copy2(upstream / name, plugin / name)

server_path = plugin / 'server.py'
source = server_path.read_text(encoding='utf-8')
old = '''            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self._process_server)
            self.timer.start(100)
'''
new = '''            hou.ui.addEventLoopCallback(self._process_server)
            self._loop_callback_registered = True
'''
assert source.count(old) == 1, 'Upstream timer implementation changed'
source = source.replace(old, new)
source = source.replace('sets up a QTimer to poll for data.', "uses Houdini's UI event loop to poll for data.")
anchor = '    def _cleanup_timer(self):\n'
assert source.count(anchor) == 1
source = source.replace(anchor, anchor + '''        if getattr(self, '_loop_callback_registered', False):
            try:
                hou.ui.removeEventLoopCallback(self._process_server)
            except Exception:
                pass
            self._loop_callback_registered = False
''')
source = source.replace("host='127.0.0.1', port=9876", "host='127.0.0.1', port=9877")
server_path.write_text(source, encoding='utf-8')

init_path = plugin / '__init__.py'
source = init_path.read_text(encoding='utf-8').replace("host='127.0.0.1', port=9876", "host='127.0.0.1', port=9877")
init_path.write_text(source, encoding='utf-8')

bridge = plugin / 'houdini_mcp_server.py'
source = bridge.read_text(encoding='utf-8')
old = '    description="A bridging server'
assert source.count(old) == 1, 'Upstream FastMCP constructor changed'
bridge.write_text(source.replace(old, '    instructions="A bridging server'), encoding='utf-8')
(plugin / 'urls.env').write_text('RAPIDAPI_KEY=\n', encoding='utf-8')

bootstrap = '''"""Start the local Houdini MCP listener after the UI is ready."""
from pathlib import Path
import json
import os
import sys
from datetime import datetime, timezone
import hou

ROOT = Path(r"C:/Users/nieyi/Documents/houdini22.0/houdini-mcp")
python_path = str(ROOT / "scripts" / "python")
if python_path not in sys.path:
    sys.path.insert(0, python_path)
if hou.isUIAvailable():
    import houdinimcp
    houdinimcp.initialize_plugin()
    houdinimcp.start_server(host="127.0.0.1", port=9877)
    server = getattr(hou.session, "houdinimcp_server", None)
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "houdini_version": hou.applicationVersionString(),
        "pref_dir": hou.getenv("HOUDINI_USER_PREF_DIR"),
        "running": houdinimcp.is_server_running(),
        "host": "127.0.0.1",
        "port": 9877,
        "event_loop_registered": bool(getattr(server, "_loop_callback_registered", False)),
    }
    (ROOT / "last-start.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print("[houdinimcp] " + json.dumps(status))
'''
(root / 'start_mcp.py').write_text(bootstrap, encoding='utf-8')

ui_dir = root / 'python3.13libs'
ui_dir.mkdir(exist_ok=True)
ui_start = '''# Load only after the Houdini UI is ready, including when opening an existing HIP.
from pathlib import Path
try:
    _mcp_start = Path(r"C:/Users/nieyi/Documents/houdini22.0/houdini-mcp/start_mcp.py")
    exec(compile(_mcp_start.read_text(encoding="utf-8"), str(_mcp_start), "exec"), {"__name__": "__houdinimcp_startup__"})
except Exception:
    import traceback
    print("[houdinimcp] startup failed")
    traceback.print_exc()
'''
(ui_dir / 'uiready.py').write_text(ui_start, encoding='utf-8')

package = {
    'enable': True,
    'load_package_once': True,
    'hpath': root.as_posix(),
}
for pref in (Path('C:/Users/nieyi/Documents/houdini22.0'), Path('C:/Users/nieyi/houdini22.0')):
    packages = pref / 'packages'
    packages.mkdir(parents=True, exist_ok=True)
    target = packages / 'houdinimcp.json'
    assert not target.exists(), f'Will not overwrite existing package: {target}'
    target.write_text(json.dumps(package, indent=2) + '\n', encoding='utf-8')

toolbar = root / 'toolbar'
toolbar.mkdir(exist_ok=True)
(toolbar / 'MCP.shelf').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<shelfDocument>
  <toolshelf name="houdinimcp22" label="MCP">
    <memberTool name="houdinimcp22_start"/>
    <memberTool name="houdinimcp22_stop"/>
  </toolshelf>
  <tool name="houdinimcp22_start" label="Start MCP" icon="BUTTONS_play">
    <script scriptType="python"><![CDATA[
from pathlib import Path
p = Path(r"C:/Users/nieyi/Documents/houdini22.0/houdini-mcp/start_mcp.py")
exec(compile(p.read_text(encoding="utf-8"), str(p), "exec"))
]]></script>
  </tool>
  <tool name="houdinimcp22_stop" label="Stop MCP" icon="BUTTONS_stop">
    <script scriptType="python"><![CDATA[
import houdinimcp
houdinimcp.stop_server()
]]></script>
  </tool>
</shelfDocument>
''', encoding='utf-8')

commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
manifest = {
    'source': 'https://github.com/capoomgit/houdini-mcp',
    'commit': commit,
    'houdini_version': '22.0.368',
    'houdini_python': '3.13',
    'bridge_python': '3.12',
    'host': '127.0.0.1',
    'port': 9877,
    'patches': ['UI event loop instead of QTimer', 'FastMCP instructions argument', 'Separate Houdini port 9877'],
}
(root / 'installation.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps(manifest, indent=2))
