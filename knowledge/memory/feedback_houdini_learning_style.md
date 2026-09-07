---
name: houdini-learning-style
description: "User's preferred way of learning Houdini procedural modeling — interactive layered walkthrough, not summary docs"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4ef14c78-2ed0-4800-813d-d56ddcda3d7d
---

学习 Houdini 工程时，**架构师思维**，不是代码注释员思维。

**核心问题永远是 4 个：**
1. **这一层（这组节点）想实现什么功能**？(capability framing)
2. **它实现了哪部分**？(what's delivered)
3. **它没实现哪部分**？(what's missing — 故意不做 vs 留给下游 vs 完全没考虑)
4. **如果要补齐没实现的，应该在哪一层、用什么节点/wrangle 来做**？(where would the extension live)

**怎么做：**

1. **拓扑视图 + 代码同时看** — 每个 wrangle 都先列出它在哪、谁喂它、谁读它（用 ASCII 拓扑图 / `_analysis/00_topology.txt` 摘录），再贴代码
2. **节点的用法跟 VEX 同样重要** — `isooffset/scatter/fuse/copytopoints/blast` 这些节点选择本身是架构决策，不只是"调用 API"
3. **一层一层往下推** — 一层结束停下等用户反馈再继续，别一次甩 500 行总结
4. **每个 wrangle 都问"功能边界"**，不是"代码做啥"
5. **Why** 比 **What** 重要 — 代码做啥 spreadsheet 一看就懂；为啥这样设计才是教学价值
6. **Trace 下游影响链** — 这个输出被谁怎么消费，才是架构价值

**反例（错的方式）：**
- 解释 `rint` vs `floor/ceil` 的差别（这是函数手册，不是架构）
- 列举 ch handle 数量（这是统计，不是架构）
- "为什么 X 用 2 / Y 用 3"（这是参数注释，不是架构）

**正例（对的方式）：**
- "pcloud 子网提供的能力是『给定体积，返回网格对齐的候选种子点』，它没提供『语义化种子』（比如塔角应该在哪），这一职责被推到了 init_attributes 阶段"
- "init_attributes 用法线分类的方式把"是不是屋顶"压成 s@type 字符串，这是把『几何特征 → 语义标签』的映射收敛在一个点；如果换成下游每个 module 自己用法线判定，会冗余 N 次"
- "这一段没做『反聚集惩罚』，所以会出现 box 挤成一团的情况；想要均匀分布需要在 pcloud 后插一个 poisson disk 节点"

**Why:** 用户原话："我要培养的是你架构师的思维，而不是琢磨每个函数的用法，当然节点的用法你也要注意，以及这些节点要实现什么功能，没实现什么功能，要怎么样才能实现功能"

**How to apply:** 任何"继续学习"/"深入"/"再讲讲" 这工程或类似项目时：
- 默认走交互式逐层模式，不要直接写 partN 总结文档
- 每层用"功能契约 → 已实现 → 未实现 → 如何补齐"四段式
- 节点选择跟 VEX 同等重要
- ~~单层结束停下问用户要不要继续~~ — **改：自动连续推下去，不要每层等用户喊"继续"。** 用户原话："你自动继续呀，不要让我来提醒你"。一次输出 1-3 层，直到把目标范围（这次是整个 stacked_boxes → init_attributes 主管线）走完为止。
- **结尾别给用户出选择题**。不要写"你想继续 a/b/c 哪个"——用户已经说了不要被催，意味着也不要被问。**自己选一个最自然的方向继续**。只有真正有 mutually exclusive 的重大分支（比如要不要写代码 vs. 只看架构）才停下问。
