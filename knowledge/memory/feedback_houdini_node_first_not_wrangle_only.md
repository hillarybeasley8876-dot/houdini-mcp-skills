---
name: feedback-houdini-node-first-not-wrangle-only
description: Houdini 程序化建模必须以专用 SOP 节点为主，wrangle 只补缺；不要一个 wrangle 包打包
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 691c81d3-231d-4dde-8a91-78ae91423e78
---

程序化建模 = **节点编排**，不是 = **写 wrangle**。每个组件优先用 Houdini 的专用 SOP（语义清晰、viewport 可视、可中断 debug），wrangle 只在 SOP 拼不出的地方补缺。

**Why:** 用户明确指出"思路有问题，应该是各种群组节点的使用，你面前怎么就一个 wrangle 做完了"。把几何构造塞进单个 wrangle (addpoint/addprim 8 corners) 是黑盒 + 无法中间检查 + 参数全 ch() + 失去 Houdini 节点流水线的价值。

**How to apply:** 任何组件设计先列"应该用哪些专用节点 + 它们的拼接顺序"，再决定哪些缝隙必须 wrangle。

## 节点优先 (按使用频率)

- **几何构造** — `box` / `tube` / `circle` / `grid` / `line` / `curve` / `polyextrude` / `sweep` / `polywire` / `revolve` (替代 wrangle 里手算 corners + addprim)
- **复制/实例** — `copytopoints` / `copytotransforms` / `copy` / `instance` (替代循环 addpoint)
- **分组** — `groupcreate` (by bounds/expression/attribute) / `groupbyrange` / `groupexpression` / `partition` / `connectivity`
- **筛选/分支** — `blast` (group 删除) / `split` / `delete` (反向 blast) / `switch`
- **变换** — `transform` / `mirror` / `xform` / `pivot` / `align`
- **属性** — `attribcreate` / `attribrandomize` / `attribfrommap` / `attribtransfer` / `attribpromote` / `attribdelete`
- **拓扑** — `divide` / `subdivide` / `fuse` / `clean` / `polyreduce` / `dissolve`
- **布尔** — `boolean` / `polyclip` / `cookie`
- **循环** — `block_begin/end` / `foreach_begin/end` (替代 wrangle 里 for 循环 N 次塑造 N 个实例)
- **合并** — `merge` / `union`

## Wrangle 应该负责的事

仅限以下场景:
- **属性计算** — 算 Cd / @id / @name / @ftype 等 tag
- **筛选条件** — 复杂 group expression 写不出的 selection
- **位置/法线后处理** — sample 邻居、平滑、重投影
- **生成 ramp 决定的连续 metric** — 楼层完工度、高度衰减

不应该写 wrangle 的事:
- 用 addpoint/addprim 手画 box / cylinder / 多边形 → 用专用 SOP
- 用循环复制 N 份几何 → 用 copytopoints
- 用 if-else 删 prim → 用 blast + group

## 反例 (我刚刚犯的错)

塔吊 crane_build 是一个 200 行 wrangle,用 addpoint 5 次手画 box (mast / cab / a-frame / jib / counter-jib) + addprim polyline 4 条索. 

**正确做法**: 
1. 一个 wrangle 只算 candidates[] 锚点 + 每个塔吊的 base+ang+pitch attribute
2. `box` SOP × 5 (mast/cab/a-frame/jib/counter-jib) 各自一个 prototype
3. `copytopoints` 用每种 prototype 复制到对应锚点 (用 transform attribute 控制旋转/缩放)
4. `add` SOP 或 `polywire` 配合 `attribwrangle` 算的 endpoint 画拉索

[[houdini_procedural_modeling]] [[houdini_pcg_practitioner_goal]]
