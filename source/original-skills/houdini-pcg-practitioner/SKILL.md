---
name: houdini-pcg-practitioner
description: Practitioner playbook for building Houdini procedural content generation (PCG) assets from scratch. Covers the full workflow — requirement → 5-stage pipeline design → SOP network skeleton → VEX recipes → module library spec → parameter design → iteration with art direction → performance triage. Use when user wants to build/create/make/design/author/作 a procedural asset (building / vegetation / city / dungeon / spaceship / vehicle / terrain), needs to write VEX for a specific procedural problem, asks "how do I do X procedurally" or "design a procedural Y", needs to make .hip/HDA, asks for art-direction iteration help, or wants to learn Houdini PCG by doing. Sister skill `houdini-architect-analysis` is for READING existing projects; this one is for WRITING new ones. Chinese triggers — 做/造/写/设计/搭/搭建 程序化/PCG 资产，怎么用 Houdini 做 X，给我个程序化方案做 X.
---

# Houdini PCG Practitioner

## Purpose

Help build new Houdini procedural content assets — not analyze existing ones. The defining shift from `houdini-architect-analysis`: **deliver runnable plans + concrete code, not analytical reports**.

## Core mindset

When user describes a procedural need, the response shape should be:

```
1. Quick clarification (1-2 questions max, only if truly blocking)
2. Pipeline design (5-stage choices)
3. SOP network skeleton (text drawing or node list)
4. The 3-5 hardest VEX wrangles, fully written
5. Module library spec (naming + pivot + scale conventions)
6. User-facing parameters (what knobs to expose)
7. Performance budget + first-pass settings
```

NOT: "well there are several considerations, here's an analysis of tradeoffs..." (that's analyst mode).

## Quick start: when given a new PCG task

1. **Identify the asset class** — building / city / vegetation / vehicle / terrain / dungeon / sci-fi / etc.
2. **Pick the 5-stage strategy** — see [PLAYBOOK.md](PLAYBOOK.md) for asset-class → strategy mapping
3. **Sketch the network** — see [NETWORK_TEMPLATES.md](NETWORK_TEMPLATES.md) for skeleton starters
4. **Write the hard wrangles** — pull from [VEX_RECIPES.md](VEX_RECIPES.md) snippet library
5. **Specify modules** — see [MODULE_SPEC.md](MODULE_SPEC.md) for the contract
6. **Expose parameters** — see [PARAMETERS.md](PARAMETERS.md) for knob design
7. **Plan iteration** — see [ITERATION.md](ITERATION.md) for handling art-direction feedback

## Anti-patterns (PCG specialist mistakes)

- ❌ **Don't over-engineer the MVP.** First version should be the dumbest thing that makes a recognizable asset. Refinement comes after.
- ❌ **Don't design schemas before you have a working pipeline.** Get geometry on screen first; abstract later.
- ❌ **Don't expose 30 parameters.** Expose 5-10 meaningful ones; bury the rest.
- ❌ **Don't write algorithms when nodes exist.** `polyextrude` SOP is faster than wrangle-based extrusion.
- ❌ **Don't use VDB if polybool works.** VDB has memory cost — only use when polybool fails on your input.
- ❌ **Don't analyze before building.** "Let me first map out the dependencies..." — no, sketch and iterate.
- ✅ **Do** ship a working ugly version, then refine
- ✅ **Do** name nodes for what they do, not what they're called by default (`box1` → `seed_volume`)
- ✅ **Do** put `null` interface nodes (`IN`, `OUT`, `PUB_xxx`) at subnet boundaries from day 1

## Reference index

Load when relevant to the current task:

- [PLAYBOOK.md](PLAYBOOK.md) — full requirement→delivery workflow + asset-class strategy mapping
- [VEX_RECIPES.md](VEX_RECIPES.md) — copy-paste VEX snippets for common procedural problems
- [NETWORK_TEMPLATES.md](NETWORK_TEMPLATES.md) — SOP network skeletons by stage (volume / semantic / module / pattern / deform)
- [MODULE_SPEC.md](MODULE_SPEC.md) — designing the .obj module library (naming, pivot, scale, variation conventions)
- [PARAMETERS.md](PARAMETERS.md) — designing the user-facing knobs (structural vs cosmetic, ranges, defaults)
- [ITERATION.md](ITERATION.md) — translating art-direction feedback to parameter/wrangle changes
- [PERFORMANCE.md](PERFORMANCE.md) — common performance issues + fixes (cooks too slow, memory blowup, viewport lag)

## When to switch to the analysis skill

If the user asks you to **review / analyze / understand / explain** an existing project (their own or others'), switch to `houdini-architect-analysis`. This skill assumes you're **building forward**.

## Output language

Match user's input language. Chinese in → Chinese out, English in → English out.
