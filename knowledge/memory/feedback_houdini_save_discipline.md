---
name: feedback-houdini-save-discipline
description: "When driving Houdini via MCP, must save .hip and enable autosave from the start; never rely on process not crashing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4a8f3014-d692-429a-910c-2cb38ff3bd3a
---

When driving Houdini via MCP for any non-trivial build:

1. **Enable autosave immediately** after first connection: `hou.hscript("autosave on")` or set via `hou.hipFile.setAutoSaveDelay(60)` (60 sec).
2. **Save the .hip explicitly** to a stable path early — `hou.hipFile.save("C:/Users/nieyi/work/<project>.hip")`. Don't let it stay as `untitled.hip`.
3. **Re-save after each completed stage / major milestone** — not just at the end.
4. **Render commands like `render_quad_views` can hang the Houdini process** (Karma init / OpenGL state). Save BEFORE calling render. Try `render_single_view` first (lighter) instead of quad.

**Why:** A render-quad-views call hung Houdini and crashed the process; all of stages 1–4 of a tower build were lost because nothing was saved. The user's rebuke ("你没有自动保存的习惯？要我教你？") was justified — the work-loss was preventable with one `hipFile.save()` call after each clean cook.

**How to apply:** Make autosave + initial save part of the standard "first MCP call" routine, before any geometry-building. Treat `hou.hipFile.save(...)` as something to call after every successful cook of a major OUT null, the same way you'd commit after a clean build.

Linked: [[houdini-mcp-integration]] for connection setup; [[houdini-pcg-practitioner]] for the build workflow that benefits from this.
