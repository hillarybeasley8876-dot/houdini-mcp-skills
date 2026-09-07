# Introduction to Houdini (Concept Page — Basics > Getting started)

> Houdini 的"四件套基本盘": **Procedural Network + Node System + Geometry Attributes + Digital Assets**

**Manual URL**: https://www.sidefx.com/docs/houdini/basics/intro
**类型**: 概念页(非节点),手册整本书的第一节
**所属**: Group 1 > Basics > Getting started > 第 1 节(共 9)

---

## 1. 是什么 (What)

手册原话(verbatim):

> "Houdini is an advanced procedural modeling, animation, effects, simulation, rendering, and compositing package."

它给出 4 项描述性能力(modeling / animation / fx+sim / rendering+compositing),但**核心定位**只有一个词: **procedural**(过程化)。

这一页本身**不教任何节点**,而是抛出 4 个贯穿全手册的基本概念:

1. **Networks** — 节点的容器(类似文件系统的"文件夹")
2. **Nodes** — 网络里的执行单元("文件"),有 input / output / parameters
3. **Geometry & Attributes** — 几何不只是顶点,而是"几何 + 任意属性数据"
4. **Digital Assets** — 把网络打包成可复用工具,无需写代码

这 4 个概念是后面所有章节的**隐含前提**。Houdini 之所以叫 Houdini,根子在这里。

## 2. 为什么这样设计 (Why procedural)

手册列了 4 个理由,我加上"读法"一栏:

| 手册理由 | 读法(为什么这件事重要) |
|---------|------------------|
| 修改上游节点会自动传播,不用重做 | DAG(有向无环图)求值模型 + 参数化驱动;一处改全局变 |
| 鼓励快速原型,保留可复用网络 | network 本身就是文档+资产;尝试不等于丢弃 |
| 用 procedural generation 管理复杂场景 | 几何 lazy 生成,内存友好;百万 instance 不会爆 |
| 网络可打包成自定义 UI 工具(digital assets) | HDA 是 Houdini 工程化的核心,也是它甩开同类的关键 |

**为什么这种范式诞生在 Houdini**: 它继承自 PRISMS(Side Effects 80 年代的 fluid effects 工具),从一开始就为"程序员-艺术家混合工作流"设计。同时代的 Maya / 3ds Max 走的是"DCC = 几何编辑器 + 时间轴"路线 — 它们后来打补丁加节点系统(Maya 的 Hypergraph、Max 的 Slate)总是别扭,因为不是地基。

**procedural 不是工作流偏好,是 Houdini 的世界观**: 一切几何都是"从某个上游推导出来",而不是"被手画出来"。这点不接受,后面任何节点都学不顺。

## 3. 概念示例 (How to read what the manual says)

### 路径示意

手册原话:
> "the root network includes pre-made networks: the object/scene level network (`/obj`) containing top-level scene objects and the render node network (`/out`)"

读法:
- `/` 是根网络
- `/obj` — 顶层对象网络(放灯/相机/几何对象)
- `/out` — 渲染节点网络(放 mantra / Karma ROP)
- 后续会出现的: `/stage`(LOP)、`/mat`(材质)、`/img`(COP)等

**类比**: 像 unix 文件系统,只是"文件"会被求值产生数据。

### 节点连线的歧义(陷阱)

手册一句关键:
> "Wiring's meaning varies by network type — typically data passes between nodes, though object-level wiring establishes hierarchical relationships."

这句话隐藏一个**陷阱**: 同一根连线,在 SOP 里是"几何流",在 OBJ 里是"父子关系",在 DOP 里是"求值依赖"。新手以为都是数据流,会写错网络。

**实战影响**: 跨 context 调试时,先问"这条线是 data / hierarchy / dependency 哪一种?"

## 4. 跟其他 DCC 范式的对比 (Why not alternatives)

| 工具 | 核心范式 | 跟 Houdini 的差别 |
|------|---------|-----------------|
| **Maya / 3ds Max** | 几何对象 + 历史栈 + 节点(Hypergraph/Slate)叠加 | 手册原话: "differs from Maya and 3D Studio Max, which consolidate nodes at a single level"。Houdini 是**多层网络**(obj 含 SOP 子网),Maya 把所有 node flatten 在一个图里;Houdini 网络结构本身承载语义,Maya 不行 |
| **Blender Geometry Nodes** | 节点 + 几何 attributes(架构最像 Houdini) | 但 GN 没有 Cooking 模型(全 eager)、没有 contexts(SOP/DOP/LOP 隔离)、没有 packed primitives、VEX 远不如 |
| **Unreal PCG** | 节点 + spatial 数据 | 偏 game runtime,没有动力学/渲染统一;无 attribute 自由扩展 |
| **Substance Designer** | 节点 + 像素/参数 | 二维资产专精,几何 weak |
| **Grasshopper(Rhino)** | 节点 + 曲线/几何 | CAD 起家,没有动画/动力学/渲染管线;运行时不如 Houdini |

**为什么 Houdini 仍然是 procedural 之王**: 同一套节点范式覆盖建模 → 动力学 → 渲染 → 合成,且在每个 context 都达到生产级。GN / PCG / Substance 在某一段做得也好,但拼不出全链路。

## 5. 这个范式能不能用别的方式替代 (Can it be replaced)

- **VEX 等价**: ❌ VEX 是节点内部的工具,不能替代节点系统本身
- **Python (HOM) 等价**: ⚠️ 可以**操控**网络(脚本建网),但不能**绕过** — 求值仍然走节点 cook
- **手搓 SOP 子网**: ✅ 这其实是"用 Houdini 的方式做 Houdini 没现成节点的事" — 是 procedural 的扩展,不是替代
- **代价**: 想绕过节点系统的人,本质上是不需要 Houdini

**唯一可替代场景**: 一次性的、不需要变体、不需要重新 cook 的几何 → 直接 Maya/Blender 雕出来更快。但只要"会改一次以上",节点系统就回本了。

## 6. 关键概念递归拆解 (Recursive concept breakdown)

### 6.1 Networks (网络)

- **是什么**: 节点的容器;有自己的 context(SOP/DOP/LOP/...);可嵌套(subnet)
- **隐喻**: 文件系统的文件夹
- **关键性质**:
  - 每个网络有一个 "context type",决定能放哪些节点
  - subnet 可暴露 input/output 接口,变成"虚拟节点"
  - 跨 context 通过 reference / object merge / pcimport 等桥接
- **PCG 关键**: [houdini-pcg-practitioner](../../../../../houdini-pcg-practitioner/SKILL.md) 的 5-stage 流水线,每个 stage 都是一个 subnet

### 6.2 Nodes (节点)

- **是什么**: 单个执行单元,有 input / output / parameters
- **角色分类**:
  - **Generator** — 凭空生成(box, line, scatter, points from volume)
  - **Processor** — 处理输入(transform, polyextrude, attribwrangle)
  - **Combiner** — 合并多输入(merge, boolean, copy to points)
  - **Utility** — 不改几何只控流(switch, null, output)
- **生命周期**: created → wired → parameters set → cooked → produced result → optionally cached
- **后续深拆**: Group 6 整组 ~2000 节点都是这个抽象的实例化

### 6.3 Geometry (几何)

- **支持类型**: polygons / NURBS / Bézier / 几何原语 / metaballs
- **关键术语陷阱**:
  - Houdini 的 **Primitive** = "几何 piece"(一个多边形、一个 NURBS 面片、一个 metaball)
  - 这跟 Maya 里 "primitive = sphere/cube" **不是一个概念!**
- **底层模型**: SOP 几何对象 = `[points] + [vertices] + [primitives] + [detail]` 四层
- **后续深拆**: Group 2 > Geometry 整章

### 6.4 Attributes (属性)

- **手册原话**: "scenes 中的信息以 attribute 形式存在,绑在 model/primitive/point/vertex 上"
- **隐藏属性举例**:
  - `P` (position) — 在 point 上,几何最基础
  - `N` (normal) — 法线
  - `Cd` (color) — 颜色
  - `id` / `name` / 任意自定义
- **作用域(class)**:
  - **Detail** — 整个几何一份(全局变量)
  - **Primitive** — 每个 prim 一份
  - **Point** — 每个 point 一份(最常用)
  - **Vertex** — 每个 vertex(prim-point 配对)一份
- **可视化工具**: Geometry spreadsheet + Visualizers
- **PCG 核心**: [houdini_procedural_modeling](../../../../../houdini-mcp/references/memory/houdini_procedural_modeling.md) 几乎所有 pattern 都是"用 attribute 编码语义,下游按 attribute 分支" — 这就是 Houdini 的"协议"

### 6.5 Digital Assets (HDA)

- **是什么**: 把 subnet 网络打包成可复用、可分发、可锁参数的"工具"
- **特点**:
  - 无需写代码,GUI 制作
  - 自定义 UI(spare params, callback, help text)
  - 可版本管理、共享
- **后续深拆**: Group 2 > Digital Assets 整章

## 7. 底层逻辑 (Engine logic)

### Cooking 模型(本页只暗示,Cooking 子页深拆)

- **节点 cook = 求值**: input + parameters → output geometry/data
- **默认 lazy**: 只在被需要(显示、被下游引用、export)时才 cook
- **依赖追踪**: 改一个上游节点,它和所有下游被标记 dirty
- **缓存**: cook 结果缓存在节点上,下次未 dirty 直接拿
- **time-dependency**: 显式或隐式依赖时间的节点,每帧 re-cook

### 网络 = DAG

- 节点 + 连线 = 有向无环图(DAG)
- 求值: 从 display flag(或 export 节点)向上反向追踪、按拓扑序 cook
- 这是 Houdini "改上游全自动更新"的数学基础

## 与上下游协作

- **本章后续直接深拆 4 件套的子页**:
  - User interface（待学习生成：`02_userinterface.md`） — 怎么操作上述抽象
  - Networks and parameters（待学习生成：`08_networks.md`） — 网络结构详解
  - Cooking（待学习生成：`13_cooking.md`） — DAG 求值的细节
- **跨章引用**:
  - Group 2 > Geometry — 几何与属性的完整模型
  - Group 2 > Digital Assets — HDA 的制作
  - Group 6 — 所有 contexts 的节点参考

## PCG Practitioner Take

这一页教的是**世界观**,不是工具。读完它要带走的不是术语,而是 4 个心智习惯:

1. **遇到几何先问"它是从哪个节点产出的"**,而不是"它是哪个对象"
2. **遇到数据先问"它绑在哪个层级"**(detail/prim/point/vertex,见 [houdini_procedural_modeling](../../../../../houdini-mcp/references/memory/houdini_procedural_modeling.md) 第 5 节)
3. **遇到重复需求先问"能不能 HDA 化"**,不要复制网络
4. **遇到性能问题先看 cook 树**,不要瞎调参数

**跟现有资产的关联**:
- [houdini-pcg-practitioner](../../../../../houdini-pcg-practitioner/SKILL.md) 的 5-stage 流水线 = 4 件套的工程化运用
- [houdini_procedural_modeling](../../../../../houdini-mcp/references/memory/houdini_procedural_modeling.md) 36 个 VEX pattern = 4 件套的高级用法
- [houdini-architect-analysis](../../../../../houdini-architect-analysis/SKILL.md) = 反推他人怎么用 4 件套搭 .hip

**读完这一节我应该能做到**: 看到一个 .hip 文件能用 4 概念把它分类(网络结构 + 节点类型 + 属性流 + HDA 边界),不被术语吓到。

## Cross-references

- 下一节: User interface（待学习生成：`02_userinterface.md`）
- 4 件套深拆位置:
  - Networks → Group 1 > Networks and parameters 章节
  - Nodes → Group 6 (整组 ~2000)
  - Geometry / Attributes → Group 2 > Geometry 章节
  - Digital Assets → Group 2 > Digital Assets 章节
- 相关 wrangle pattern: [houdini_procedural_modeling](../../../../../houdini-mcp/references/memory/houdini_procedural_modeling.md)
- Practitioner playbook: [houdini-pcg-practitioner](../../../../../houdini-pcg-practitioner/SKILL.md)
