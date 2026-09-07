# {Node Name} ({Context: SOP/VOP/LOP/DOP/...})

> **一句话定位** — 它在 cook 流程里干什么

**Manual URL**: https://www.sidefx.com/docs/houdini/nodes/{context}/{node}.html
**Internal name**: `{internal_name}`
**Category**: {category}

---

## 1. 是什么 (What)

- **节点 context / category**: 在哪个 context、属于哪类（generator / processor / utility / volume / instance / ...）
- **输入需求**: geometry? attribute pre-conditions? prim type? 几个输入？
- **输出形态**: 几何变换？添加属性？产生新 geometry？
- **网络中常出现的位置**: 数据流的哪一段（早期生成？中段处理？末段烘焙？）

## 2. 为什么存在 (Why this exists)

- **它解决什么任务**（用户视角，例: "把 A 复制到 B 的每个点上"）
- **它代表的算法 / 数学操作**（受 [[houdini_procedural_modeling]] 启发: 多 ray? KDE? level-set? spatial join?）
- **SideFX 为什么把它做成独立节点**而不是一句 wrangle / 一段 SOP 子网

## 3. 怎么用 (How — 至少 3 个 recipe)

### Recipe A — 最简

**任务**: ...
**Topology**:
```
[upstream]
    ▼
[{node}]
    ▼
[null OUT]
```
**关键参数**: ...
**结果**: ...

### Recipe B — 进阶

**任务**: ...
**Topology**: ...
**关键参数 / VEX**: ...
**结果**: ...

### Recipe C — 跨子网协同 / 跨 context

**任务**: ...
**Topology**: ...
**协作关键**: ...
**结果**: ...

## 4. 替代方案为什么不行 (Why not alternatives)

| 替代节点 | 看似可替代场景 | 为什么不行 / 适用边界 |
|---------|--------------|-------------------|
| ... | ... | ... |

## 5. 能不能用别的方式替代 (Can it be replaced)

- **VEX 等价实现**: {若可能，给最小代码}
- **Python / HOM 等价**: {若可能}
- **手搓 SOP 子网**: {若可能}
- **替代代价**: 性能 / 表达力 / 可读性 / 工程性

## 6. 参数递归拆解 (Recursive parameter breakdown)

按 tab 分节。每个 param 必给 4 项：
- **是什么**
- **默认值意义**
- **改后的可视化效果**
- **底层引擎做了什么**

### Tab: ...

- **{Param 1}**
  - 默认: `...`
  - 是什么: ...
  - 改后: ...
  - 引擎: ...

- **{Param 2}**
  - ...

### Tab: ...

- ...

## 7. 底层逻辑 (Engine logic)

- **cook 时引擎做了什么**: 每帧 / lazy / cache?
- **attribute pass**: 输入需要什么属性 / 产出什么属性 / 属性 promote / 删除哪些?
- **内存 / 性能**: 是否做几何复制？是否走 packed / instance 路径？
- **与 packed primitive / instance 的相互作用**
- **time-dependency**: 是否 time-dependent? 当上游 time-dependent 时如何传递?

## 与上下游协作

- **典型上游**: ...
- **典型下游**: ...
- **跨 context 用法**: ...

## PCG Practitioner Take

- **在做 {asset class} 时**: 这个节点扮演什么角色
- **何时该用**: 哪些 PCG 任务这是首选
- **何时该绕开**: 哪些情况不要用它（指向更合适的节点 / 自己写 wrangle）
- **关联 pattern**: 在 [[houdini_procedural_modeling]] 的哪些 pattern 里出现

## Cross-references

- 相关章节: [[...]]
- 相关 wrangle pattern: [[...]]
- Practitioner playbook: [[...]]
