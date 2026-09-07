---
name: Houdini installation
description: SideFX Houdini 21.0.440 install path and CLI tools available on this Windows machine
type: reference
originSessionId: 685ad3e8-e388-4674-a441-0059e16cc6fc
---
SideFX Houdini 21.0.440 is installed at `C:\Program Files\Side Effects Software\Houdini 21.0.440\`.

CLI tools live in `bin/` and are NOT on PATH — invoke with the full path:
- `hython.exe` — Houdini's Python interpreter (Python 3.11), use for any `import hou` automation
- `hbatch.exe` — non-interactive batch session
- `hrender.exe` / `hrender.py` — render driver
- `husk.exe` — USD/Solaris render
- `hcmd.exe` — opens a shell with Houdini env vars loaded
- `houdini.exe` / `houdinicore.exe` / `houdinifx.exe` — UI

In bash on this machine, quote the path: `"/c/Program Files/Side Effects Software/Houdini 21.0.440/bin/hython.exe"`.

Default `$HIP` resolves to `C:/Users/nieyi` (no project loaded). `hou.expandString` is deprecated in 21 — use `hou.text.expandString` instead.
