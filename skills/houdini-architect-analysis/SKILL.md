---
name: houdini-architect-analysis
description: Architect-level analysis of Houdini procedural modeling projects. Identifies the classical algorithm hidden inside each wrangle (longest path / Markov / KDE / level-set / spatial join / multi-ray decision tree), recognizes loop block patterns (feedback / piece / count), maps cross-subnet service nodes, and audits 6-layer collaboration health. Bundled scripts unpack .hip cpio archives and extract topology + every VEX snippet without needing Houdini installed. Use when analyzing a .hip file, reviewing a procedural modeling project, doing architecture review of procedural assets, learning architect-level thinking for procedural modeling, or asked to "deep dive" / "analyze" / "review" / "study" a Houdini project or procedural asset (Chinese triggers: 学习/分析/拆解/审查/架构师 angle for Houdini/程序化建模 项目).
---

# Houdini Architect Analysis

## Purpose

Pull architect-level understanding out of any procedural modeling project (Houdini-first, but the methodology is tool-agnostic). The skill is built on one core conviction: **every wrangle is a classical CS algorithm in geometric disguise** — once you can name the algorithm, you know its complexity, failure modes, and refactor options.

## Quick start (3-step workflow)

1. **Extract the project** (no Houdini needed):
   ```
   python scripts/extract_hip.py path/to/file.hip
   python scripts/parse_hip.py   path/to/file_extracted  out_dir/00_topology.txt
   python scripts/extract_vex.py path/to/file_extracted  out_dir/
   ```
   Produces `00_topology.txt` (SOP graph) + `01_all_wrangles.md` (every VEX) + `02_all_node_key_params.txt`.

2. **Walk the project layer by layer** using the 4-segment template:
   - **Functional contract** — what capability does this layer/subnet provide?
   - **What's implemented** — concrete decisions, node choices, why each
   - **What's deliberately not done** — pushed downstream to which layer
   - **What's missing entirely + how to extend** — concrete refactor sketches

3. **For each wrangle, name the algorithm** before explaining the code. See [ALGORITHMS.md](ALGORITHMS.md) for the catalog.

## Anti-patterns to avoid (hard-learned)

- ❌ **Don't write an encyclopedia document.** Walk layer-by-layer interactively.
- ❌ **Don't explain `rint` vs `floor`** — that's function manuals, not architecture.
- ❌ **Don't ask the user "do you want to continue?"** after each layer. Auto-continue. Only stop on truly mutually-exclusive forks.
- ❌ **Don't go abstract (Conway's Law, Category Theory) at the expense of concrete code.** Math/algo lens must point at specific wrangles.
- ✅ **Do** combine topology view + code in every layer.
- ✅ **Do** name the classical algorithm + complexity + failure mode for every wrangle.

## Reference index

When the question matches, load the relevant file:

- [METHODOLOGY.md](METHODOLOGY.md) — the layer-by-layer process + 4-segment template details
- [ALGORITHMS.md](ALGORITHMS.md) — wrangle algorithm catalog (longest path / Markov / KDE / level-set / spatial join / multi-ray decision tree)
- [PATTERNS.md](PATTERNS.md) — loop block math (feedback=fixed-point, piece=parallel-map, count=truncated), 5-stage pipeline template, cross-subnet bus
- [COLLABORATION.md](COLLABORATION.md) — 6-layer collaboration analysis (L1 cross-wrangle through L6 cross-project) with the metrics dashboard
- [DEBT_CHECKLIST.md](DEBT_CHECKLIST.md) — common architectural debts to flag, with concrete refactor templates

## When to write deliverables

By default the skill outputs **interactive layer-by-layer analysis in the chat**, not files. Only write a `partN.md` summary file when the user explicitly says "write it up" or "save the analysis."
