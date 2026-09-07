# Methodology: Sequential Manual Deepdive

## 一次会话的标准 6 步

### Step 1: Locate
读 `~/.claude/projects/C--Users-nieyi/houdini_manual/PROGRESS.md`，找下一个 🟡 或 ⬜ 子主题。规则：
- 严格手册顺序（MANUAL_TOC.md 为准）
- ⏭ 标记的章节直接跳过（动态内容 / 已被其他记忆覆盖）
- **每会话最多 3 个子主题**（[[feedback_houdini_corpus_pace]]）

### Step 2: Fetch
WebFetch 该子主题对应的 URL。如果 URL 不在 PROGRESS 里，先去手册顶页找到再 fetch。

**禁止**凭训练数据写节点页 —— 必须以真实页面为准。

### Step 3: Walk and Write
- **节点页**: 套用 [templates/NODE.md](templates/NODE.md) 7 段写
- **章节总览页**: 套用 [templates/CHAPTER.md](templates/CHAPTER.md) 写到 `<chapter>/INDEX.md`
- 写法语气向 [[houdini-architect-analysis]] 看齐 —— 表格/topology/为什么 > 散文/参数表

### Step 4: Reflect on chapter completion
当一个二级子区（如 Basics 下的 Getting started 子区）所有子页都覆盖后，按 [templates/REFLECTION.md](templates/REFLECTION.md) 做 5-问反思，存为 `<subsection>/99_reflection.md`。

### Step 5: Update PROGRESS
- 完成项标 ✅ + 写 `<absolute path>` 到该项后
- 下次起点标 🟡 + 更新文末 "Next session 起点" 段

### Step 6: Report
chat 输出格式：
```
本次推进:
- ✅ {item 1} → {file}
- ✅ {item 2} → {file}

下次起点:
- 🟡 {item 3}
- URL: {link}
```

## Auto-continue 规则（来自 [[feedback_houdini_learning_style]]）

- 用户说 "继续" / "下一节" / "go on" → 直接接着写下一个，**不要问** "要哪一节？"
- 推进 1-3 个子主题后自然停下（pace 约束硬上限是 3）
- **不要在末尾问** "要不要 a / b / c ?" 这种选择题

只有在以下情形才停下来问：
- 两个非平凡分支等价（如 "下一节是 X 还是先做 Y 章节的 Z?"）
- 需要破坏性操作（删文件、改其他 skill）
- 用户明确提问

## 单节点的写作目标

让一个不熟该节点的 PCG practitioner 看完后能：
1. 知道**何时**用它
2. 知道**何时**绕开（替代节点为什么不行；自己实现可不可行）
3. 写出 1 个最简 demo
4. 理解**关键参数**的可视化后果

**不是**让人能背出每个参数的默认值。

## 数据真实性

- 每个节点 / 章节 必须先 WebFetch 真实页面
- 参数名 / 默认值 / 标签 / tab 排序，以官方页面为准
- 如手册某段含糊或与版本相关：标注 "Manual 措辞含糊；按 Houdini 21.0.x 实测：…"
- 涉及 VEX / Python 代码示例：测过的标 ✅，未测的标 ⚠️ "未实测，按手册推断"

## 章节顺序硬约束

按 MANUAL_TOC.md 严格走：
1. Group 1: Getting started → 完成才能进 Group 2
2. Group 2: Using Houdini → ...
3. ...

**唯一例外**：Group 6 (Nodes) 可以和 Group 2-5 交错 —— 因为 Using Houdini 章节会引用 SOP/VOP 节点，临时跳到对应 Node 页深拆是合理的（标注 "[OUT-OF-ORDER, prerequisite for Using Houdini > X]"）。

## 知识库目录命名约定

- 顶层目录：`01_getting_started`, `02_using_houdini`, …, `09_reference`（共 9，因 Group 6/7/8 合并）
- 二级子区：`basics/`, `geometry/`, `copying_and_instancing/` 等（snake_case，无前缀编号）
- 节点文件：`{node_internal_name}.md`（例：`copytopoints.md`, `attribwrangle.md`）
- 章节总览：`INDEX.md`
- 反思：`99_reflection.md`

## 跨 skill 协作

写到知识库时尽量用 `[[wiki-link]]` 引用：
- [[houdini_procedural_modeling]] 的 36 个 VEX pattern
- [[houdini-pcg-practitioner]] 的 5-stage pipeline
- [[houdini-architect-analysis]] 的 6 个算法 catalog
- [[houdini_environment]] 的安装路径

避免重复写已有内容；引用即可。
