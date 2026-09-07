---
name: houdini-manual-progress
description: "SideFX 官方手册深拆项目的进度索引;指向知识库 PROGRESS.md 和 skill houdini-manual-deepdive。当用户问\"学到哪了 / 下一节是什么 / 继续学手册\"时查这里。"
metadata: 
  node_type: memory
  type: project
  originSessionId: 71e48b7e-478d-4651-b6d1-9b2cf071e90a
---

# Houdini Manual Deepdive — Progress Index

**Skill**: [[houdini-manual-deepdive]] (`~/.claude/skills/houdini-manual-deepdive/`)
**Knowledge base**: `~/.claude/projects/C--Users-nieyi/houdini_manual/`
**Master progress**: `~/.claude/projects/C--Users-nieyi/houdini_manual/PROGRESS.md`

## Project meaning

按 SideFX 官方手册（https://www.sidefx.com/docs/houdini/）顺序逐章逐节深度拆解,每个节点都覆盖。**百科是终点,架构师走读是方法,多会话累积是节奏**。

## Why

用户原话: "给我狠狠的学 houdini 手册的每一个章节,对应理解,不准走马观花,需要做到,是什么,为什么,怎么做,其他的为什么不行,能不能用别的方式替代?... 完全的制作每个节点的计划书,然后把它储存成一个巨大的 skill"

核心目标是建立完整的"想做什么 → 用什么节点"知识库,与 [[houdini_pcg_practitioner_goal]] 的 PCG practitioner 方向对齐。

## How to apply

- 用户说 "继续学手册" / "下一节" / "继续 deepdive" / "学下一节 Houdini" → 调用 [[houdini-manual-deepdive]] skill
- 读 master PROGRESS.md 找下次起点（🟡 标记）
- 推进 1-3 个子主题（[[feedback_houdini_corpus_pace]]）
- 不要在末尾问"要不要继续？"（[[feedback_houdini_learning_style]] 的 auto-continue）
- 每节必须先 WebFetch 真实页面再下笔（数据真实性约束）
- 章节完读后写 99_reflection.md（[[feedback_houdini_reflection]] 5-问）

## Current focus

**2026-05-14 起**: Group 1 → Basics → Getting started 子区
**已完成**: 骨架 + Basics INDEX + Introduction to Houdini
**下次起点**: Basics > Getting started > User interface

## 与其他 Houdini 资产的关系

- 不重复 [[houdini-architect-analysis]]（那是反推 .hip）
- 不重复 [[houdini-pcg-practitioner]]（那是端到端建造 playbook）
- 写完节点会引用 [[houdini_procedural_modeling]] 已有的 36 个 VEX pattern
