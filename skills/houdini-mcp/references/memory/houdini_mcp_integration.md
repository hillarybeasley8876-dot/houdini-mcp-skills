---
name: Houdini MCP integration
description: How Houdini is wired to Claude Code via MCP — components, file locations, and gotchas needed to debug or modify the setup
type: project
originSessionId: 72498ccc-0e21-4c7e-bdc4-3008682b322d
---
Claude Code controls Houdini via the `capoomgit/houdini-mcp` two-process architecture, set up on 2026-05-11.

**Architecture**:
- Houdini-side plugin (in `houdinimcp` Python package) listens on `localhost:9876` (TCP)
- Bridge process (Python 3.12 in dedicated venv) runs as MCP stdio server, relays to TCP

**Key paths**:
- Plugin: `C:\Users\nieyi\Documents\houdini21.0\scripts\python\houdinimcp\` (5 .py files + pyproject.toml + urls.env)
- Bridge venv: `<plugin>\.venv\Scripts\python.exe` (Python 3.12 via uv)
- Bridge entry: `<plugin>\houdini_mcp_server.py`
- Auto-start hook: `Documents\houdini21.0\scripts\123.py` (does `import houdinimcp` on Houdini startup)
- Shelf button: `Documents\houdini21.0\toolbar\MCP.shelf` (manual toggle)
- MCP registration: `~/.claude.json` (added via `claude mcp add -s user houdini ...`)

**CRITICAL — multiple Houdini binaries use DIFFERENT user pref dirs:**
- `hindie.exe` launched from Start Menu icon: `$HOUDINI_USER_PREF_DIR = C:\Users\nieyi\Documents\houdini21.0`
- `houdini.exe` launched from CLI/script: `$HOUDINI_USER_PREF_DIR = C:\Users\nieyi\houdini21.0` ← different!
- `hython.exe` (CLI Python): `C:\Users\nieyi\houdini21.0`
- Symptom: plugin auto-load silently fails because 123.py / scripts/python/ live in only one of the two dirs.
- **Permanent fix already applied (2026-05-13)**: `~\houdini21.0\scripts\python\houdinimcp` is a Windows directory junction → `~\Documents\houdini21.0\scripts\python\houdinimcp` (created via `mklink /J`, no admin needed). `123.py` and `toolbar/MCP.shelf` are duplicated to both pref dirs. Editing files under `Documents\...\houdinimcp\` updates both because of the junction.
- Always verify which pref dir the running UI uses via Python pane: `print(hou.text.expandString("$HOUDINI_USER_PREF_DIR"))`. Never trust hython for this.

**Local patches** (necessary for Houdini 21 + current mcp library):
1. `server.py` line ~12: `from PySide2 import QtWidgets, QtCore` → `try: from PySide6 ... except ImportError: from PySide2 ...` (Houdini 21 ships PySide6, no PySide2)
2. `server.py` `start()`/`stop()` methods: replace `QtCore.QTimer` polling with `hou.ui.addEventLoopCallback(self._process_server)` / `removeEventLoopCallback`. **QTimer never auto-fires** in PySide6 from Python Shell context — same for `hdefereval.executeDeferredAfterWaiting` self-loops and bg-thread `executeInMainThreadWithResult`. Only `hou.ui.addEventLoopCallback` is reliable.
3. (Already in upstream as of 2026-05-13) `FastMCP(..., instructions=...)` instead of `description=` for newer mcp lib.

The full patched `start()`/`stop()` source and recipe lives in skill `houdini-mcp` at `~/.claude/skills/houdini-mcp/SKILL.md` — invoke that skill for setup/repair.

**Why:** User wanted Claude to drive Houdini directly. The capoom path is the most-documented community option; bridge needed two patches to run on current mcp library version.

**How to apply:** When debugging connection issues, check in this order: (1) is Houdini running? (2) `Test-NetConnection localhost -Port 9876` should succeed; (3) `claude mcp list` should show `houdini ✓ Connected`. The bridge starts fine without Houdini running — only individual tool calls fail at runtime.

**Houdini must be the UI process** (`houdini.exe` / `houdinifx.exe`), not `hython` — the plugin's `server.py` imports PySide2 which isn't available in non-UI hython.

**Useful tools exposed**: `get_scene_info`, `create_node`, `execute_houdini_code` (runs arbitrary `hou.*` Python — most powerful), `render_single_view`, `render_quad_views`, `render_specific_camera`. OPUS tools are exposed but will error on call (no RapidAPI key).
