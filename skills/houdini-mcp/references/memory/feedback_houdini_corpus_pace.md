---
name: feedback-houdini-corpus-pace
description: "Houdini 大型工程合集（数百+）必须分多 session 渐进精读，不能一次性\"学完\"。每 session 1-3 工程，跨 session 累积。"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 030e4590-3d99-4174-b6e0-381ccb00a4f6
---

学习 660+ 工程合集的硬约束：

1. **单 session 容量** = 1-3 工程深度精读 + 全 corpus 频率扫描。超过这个数，深度立刻塌成"我看过 = 我懂"的 surface scan。

2. **不能宣称"学完"全 corpus**。可以宣称"扫过 N 工程的频率分布" + "深读了 K 工程"。两者必须诚实区分。

3. **跨 session 累积** 是真实学习路径：
   - Session 1: 频率扫描 → 选 3 个高价值工程精读
   - Session 2: 再精读 3 个，校对前次结论
   - …
   - Session N: 才有覆盖全 corpus 的判断
   - 整体需要 50+ session，不是 1 个

4. **架构 claim 必须 data-backed**：
   - 频率统计前不要写"X 是 ubiquitous"
   - 不要从 sample-of-1 推全工业
   - Audit 自己的旧 claim — 错了就改 / 标 ⚠️

**Why:** 用户多次说"那么多工程你怎么可能一次性学完"，我每次嘴上承认实际上还在偷工减料 — 跨工程频率统计 (CROSS_CORPUS_FREQUENCY_AUDIT.md) 用数据证 11 条 claim 9 条错/夸大。这是结构性 context 限制，不是努力能补的。

**How to apply:**
- 用户给大型 corpus（≥50 工程），先用 grep 做频率扫描，**只**做扫描可支持的 claim
- 选 1-3 工程做精读（按数据上的"高价值"选，不按"我感兴趣"选）
- 写产出时显式标"基于 N 工程深读 / M 工程频率扫描"
- 建立 corpus 索引文件，让后续 session 接着前次进度
- 不写"我已经学完 N 工程的 architecture taxonomy" — 写"截至 session K 的部分理解"
