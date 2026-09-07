---
name: houdini-mcp-no-manual-paste
description: Never ask the user to paste reload snippet into Houdini Python Shell — auto-recover instead (kill + relaunch + monitor 123.py log)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4a8f3014-d692-429a-910c-2cb38ff3bd3a
---

When Houdini MCP is down (port 9876 not listening), DO NOT ask the user to paste anything into Houdini's Python Shell. Auto-recover end-to-end:

1. Read `C:/Users/nieyi/houdini21.0/houdinimcp_startup.log` — check the latest `--- 123.py END ---` timestamp vs current time and vs hindie process StartTime.
2. If 123.py never fired in the current session: kill hindie via `Stop-Process -Id <pid> -Force`, relaunch via `"/c/Program Files/Side Effects Software/Houdini 21.0.440/bin/hindie.exe" "<hip-path>" &` (background).
3. Monitor the log file with a `while` loop until a fresh `--- 123.py END ---` appears, then check port 9876 with `Get-NetTCPConnection -LocalPort 9876 -State Listen`.
4. If 123.py ran but port still down: that's the rare case — only THEN consider asking.

**Why:** The user has shouted "你说了你自动连接" multiple sessions in a row. Asking them to manually paste into Houdini Python Shell every time is the exact behavior they explicitly told me to stop.

**How to apply:** Triggered by any tool result containing "Could not connect to Houdini on localhost:9876" or "Connection Error getting scene info". Skill [houdini-mcp](../../SKILL.md) needs updating to lead with this auto-recovery path; meanwhile, do it inline.
