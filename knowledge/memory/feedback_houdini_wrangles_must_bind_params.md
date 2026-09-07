---
name: houdini-wrangles-must-bind-params
description: Every tweakable number in a Houdini wrangle MUST come from ch/chi/chv on a MASTER_PARAMS null — never hardcode magic numbers
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4a8f3014-d692-429a-910c-2cb38ff3bd3a
---

When writing VEX in Houdini wrangles for procedural assets, EVERY numeric constant that could conceivably be tweaked (sizes, counts, thresholds, ratios, color components, offsets) MUST be bound to a parameter via `ch("/path/to/MASTER_PARAMS/X")`, `chi(...)`, or `chv(...)` — and that parameter must exist on a `MASTER_PARAMS` null in the asset's geo container.

**Why:** The user explicitly called this out — "我服了, 你的wrangle数值都是直接写死的? 不用chi chf 这些提取参数绑定? 那我们能有什么操作空间". The whole point of procedural modeling is parameter-driven control. A wrangle with hardcoded numbers like `float ra_x = 80;` defeats the entire purpose: the user can't tweak from the parameter panel, can't drive variations, can't HDA-ify the asset cleanly. The asset becomes "procedural" only in the loosest sense (a script that generates geometry once) instead of TRUE PCG (parameter-driven, every variation a knob-twist away).

**How to apply:**
1. Before writing a wrangle, list every number that will appear in the snippet — that's the parameter list.
2. Add ALL those parameters to a `MASTER_PARAMS` null in the same geo container (FloatParmTemplate / IntParmTemplate / ColorParmTemplate).
3. In the wrangle, every numeric reference reads from `ch("../MASTER_PARAMS/name")` — relative path so the wrangle survives copy-paste of the geo node.
4. The ONLY hardcoded constants allowed: mathematical constants (`6.28318`, `0.5` for halving), iteration bounds derived from other params (`for i < n_floors`), and trivial multipliers in derived expressions (`fx * 0.5` to halve a footprint param).
5. Even seemingly-trivial things like `seg = 80` (oval segment count) → `chi("../MASTER_PARAMS/oval_segments")` because the user might want to dial geometry density up/down.

**Audit checklist when reviewing a finished asset:**
- Open every wrangle. For each `float X = Y;` or `int X = Y;` line, ask: would the user ever want to change this Y? If yes, it must be a chf/chi.
- Magic conditionals like `if (edge_len > 30)` are also smell — `30` should be a `long_face_threshold` param.
- Color literals like `set(0.65, 0.62, 0.58)` MUST come from a 3-component FloatParmTemplate (color picker).

This is non-negotiable for any asset claiming to be "procedural".
