---
name: feedback-houdini-reflection
description: "When studying Houdini projects, do reflection-by-five-questions per project — not just VEX pattern extraction"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 030e4590-3d99-4174-b6e0-381ccb00a4f6
---

学每个 Houdini 工程必须做"反思五问"：
1. **为什么这样建？** 作者为什么选择这个节点链 / 算法 / 拓扑？背后的约束是什么？
2. **工程的意义是什么？** 它解决了什么问题？产出什么效果？为什么这个效果有价值？
3. **每个节点起什么作用？** 不只识别节点类型，要说清"如果删掉这个节点会怎样"。
4. **每个属性/数组承担什么角色？** geometric / protocol / scratch / output —— 它在数据流里干嘛？
5. **应用场景 + 复现配方** — 以后什么需求会用到？怎么从零搭一遍？

**Why:** 用户明确指出，光抽 VEX idiom 是浅层学习；架构师视角是逐工程做反思 + 把"思路"消化成可复用的复现配方。如不做反思，只是知识点列表，遇新需求没法直接套。

**How to apply:** 每读一个 .hip，输出至少必须包含：
- 一段"工程意义"（1-2 句话）
- "节点链中央那个特化节点 + 两边 bridge wrangle"是什么、为什么必须存在
- 关键属性的角色（is geometric / is protocol / is scratch）
- "复现公式" — 5-8 个 bullet 步骤，写完一个新人能照着搭
- 可选：变体 (variation) — "如果想要 X 效果，改 Y 节点的 Z 参数"

不要做的事：
- 不要写百科全书式平铺各 wrangle 内容（那是手册）
- 不要简单复述 stickynote
- 不要只列 VEX idiom 而不联系到工程意图
