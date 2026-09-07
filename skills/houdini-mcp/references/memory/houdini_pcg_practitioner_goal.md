---
name: houdini-pcg-practitioner-goal
description: "User's actual goal for studying the Lake House project — become an excellent Houdini PCG practitioner, not just an analyst"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4ef14c78-2ed0-4800-813d-d56ddcda3d7d
---

用户学习湖边小屋工程的**真正目标**：成为**出色的 Houdini PCG（Procedural Content Generation）师**。

这是个**实践者**目标，不是分析师目标。区别：

| 分析师能力（我已建立）| PCG 师能力（用户真正想要）|
|------|------|
| 读懂别人的 .hip | 从 0 写自己的 .hip |
| 识别算法名 + 复杂度 | 选用合适算法解决新问题 |
| 找出架构债 | 设计无债的新架构 |
| 走逐层 walkthrough | 给出节点级布线 + VEX 实现 |
| 写"功能契约/已实现/未实现"分析报告 | 接到需求 → 出可运行 .hip + 模块库规范 |
| 看到 wrangle 知道是 KDE | 接到"删除稀疏点"立刻写 pcopen+pcnumfound |

**Why:** 用户原话："我让你学这个工程是为了让你成为出色的 Houdini PCG 师"。这是 2026-05-13 之前所有学习活动（part1-5 笔记 + 6 层协同分析 + houdini-architect-analysis skill）的**终极目标**——前面那些都是手段，不是目的。

**How to apply:** 
- 任何关于 Houdini 的对话，**默认假设用户想做 / 想学怎么做**，不是想分析。
- 提到具体程序化资产需求时，**直接出方案**：节点链 + 关键 VEX + 参数设计，不要先长篇分析。
- 当用户说"分析"明显时才走分析模式（用 houdini-architect-analysis skill）。
- 配套 skill：`houdini-pcg-practitioner` 是分析 skill 的**实践补丁**——一个读、一个写。
- 永远记得：**能把湖边小屋分析得头头是道 ≠ 能自己做出湖边小屋**。后者才是目标。
