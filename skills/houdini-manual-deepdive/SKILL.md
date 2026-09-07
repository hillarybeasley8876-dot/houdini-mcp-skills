---
name: houdini-manual-deepdive
description: Sequential deep-dive tutor for the SideFX Houdini official manual (https://www.sidefx.com/docs/houdini/). Walks the user chapter-by-chapter in manual order, no skipping. Each node gets a 7-segment deep-dive (what / why exists / how-recipes / why-not-alternatives / can-be-replaced / recursive parameter breakdown / engine logic) plus a PCG practitioner take. Knowledge base accumulates across sessions in ../houdini-manual-deepdive/knowledge/houdini_manual/. Triggers - 继续学手册 / 学下一节 Houdini / 深拆 X 节点 / 继续 deepdive / study Houdini manual / asked to deeply learn / explain / unpack any official Houdini chapter or node.
---

# Houdini Manual Deepdive

## Purpose

按 SideFX 官方手册的顺序，逐章逐节深度拆解。**每个节点都要覆盖、不准跳**。

核心信条：
- **百科是终点** — 长跑下来知识库覆盖整本手册
- **架构师走读是方法** — 不写参数表流水账，每段都回答 "为什么这样设计"
- **多会话累积是节奏** — 单次 1-3 个子主题，受 [feedback_houdini_corpus_pace](../houdini-mcp/references/memory/feedback_houdini_corpus_pace.md) 约束

## What this skill IS NOT

- 不是 [houdini-architect-analysis](../houdini-architect-analysis/SKILL.md) — 那是从既有 .hip 项目里反推算法
- 不是 [houdini-pcg-practitioner](../houdini-pcg-practitioner/SKILL.md) — 那是端到端建造 PCG 资产的 playbook
- 不是 [houdini-mcp](../houdini-mcp/SKILL.md) — 那是 MCP 集成的设置/排障
- 不是百科快查 — 走读式，不是参数表罗列

## What this skill IS

按手册顺序的"导师"，每次会话陪用户走读 1-3 个子主题，写入知识库。每节最后必给一段 **PCG Practitioner Take** —— 在做 X / Y 类资产时这个节点的角色（受 [houdini_pcg_practitioner_goal](../houdini-mcp/references/memory/houdini_pcg_practitioner_goal.md) 约束）。

## Quick start (per session)

1. 读 [PROGRESS.md](knowledge/houdini_manual/PROGRESS.md) 找下一个 🟡 起点
2. WebFetch 官方页面（URL 在 PROGRESS / TOC 里）
3. 按 [templates/NODE.md](templates/NODE.md) 或 [templates/CHAPTER.md](templates/CHAPTER.md) 写到知识库
4. 推进 1-3 个子主题后停 + 更新 PROGRESS + 在 chat 报告下次起点

## Reference index

- [METHODOLOGY.md](METHODOLOGY.md) — 一次会话的标准流程 + auto-continue 规则 + 数据真实性约束
- [MANUAL_TOC.md](MANUAL_TOC.md) — Houdini 21 官方手册全目录（路由地图）
- [templates/NODE.md](templates/NODE.md) — 节点深拆 7 段模板
- [templates/CHAPTER.md](templates/CHAPTER.md) — 章节总览模板
- [templates/REFLECTION.md](templates/REFLECTION.md) — 章节通读后的 5-问反思模板（受 [feedback_houdini_reflection](../houdini-mcp/references/memory/feedback_houdini_reflection.md) 约束）

## Knowledge base location

`../houdini-manual-deepdive/knowledge/houdini_manual/`
- `PROGRESS.md` — 进度
- `01_getting_started/ ... 09_reference/` — 按手册顶层 9 大块（11 个分组合并到 9 个目录）
- 每个子区一个目录，含 `INDEX.md`（章节总览）、各节点 .md、`99_reflection.md`

## Anti-patterns (hard constraints)

- ❌ 一次写完一章 27 个子页 → 违反 [feedback_houdini_corpus_pace](../houdini-mcp/references/memory/feedback_houdini_corpus_pace.md)
- ❌ 写参数表却不写"为什么这样设计" → 违反 [feedback_houdini_learning_style](../houdini-mcp/references/memory/feedback_houdini_learning_style.md)
- ❌ 跳过自认为简单的章节 → 用户原话"不准偷懒"
- ❌ 末尾问"要不要继续？" → 违反 [feedback_houdini_learning_style](../houdini-mcp/references/memory/feedback_houdini_learning_style.md) 的 auto-continue
- ❌ 凭训练数据胡编参数名 / 默认值 → 必须先 WebFetch 真实页面
- ❌ 写完不更新 PROGRESS → 下次会话找不到起点

## Output discipline

- 内容主体写到知识库 .md 文件；chat 输出关键发现 + 下次起点
- 章节完读（所有子页）后立刻写 `99_reflection.md`
- 每次会话结束更新 PROGRESS.md 的 "Next session 起点" 段
