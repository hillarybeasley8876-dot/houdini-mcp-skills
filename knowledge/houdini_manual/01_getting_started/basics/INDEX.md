# Basics — Houdini 入门基础

**Manual URL**: https://www.sidefx.com/docs/houdini/basics/
**手册原话**: "The basics of working with Houdini's user interface."

---

## 章节定位

- **整体地位**: 手册第一个正文章节,讲 Houdini 的"三件套基本盘" — UI 操作 / 节点协作范式 / 几何属性体系
- **上游**: 无(手册起点)
- **下游**: Shelf tools, Networks and parameters,以及 Group 2 起的所有"工作流"章节
- **核心概念基础**: procedural networks(节点网络) + cooking model(求值模型) + geometry attributes(几何属性) + digital assets(数字资产)。这四个是后面所有章节的**隐含前提**

## 任务地图(我想搞懂什么 → 看哪些子页)

| 我想搞懂什么 | 看哪些子页 |
|------------|----------|
| Houdini 的核心范式是什么、为什么是 procedural | Introduction to Houdini |
| 怎么操作界面、怎么把节点连起来 | User interface, Tab menu, Networks and parameters |
| 怎么看场景、怎么选东西、怎么用 handle 拖 | Viewing the scene, Selecting, Using handles, Working with objects |
| 节点为什么不重新计算、什么时候才触发 | Cooking, Visualizers, Inspection mode |
| 怎么把界面调成自己的样子 | Customization 子区(8 子页) |
| 场景慢了怎么提速 | Speed up your scene, Memory toolbar, Advanced Viewport Shading |
| 怎么做 multiple variations 不互相覆盖 | Create variations with takes |
| 找节点找不到怎么办 | Tab menu, Dashbox, Radial menus |

## 子页清单(按手册顺序,共 30 个)

### Getting started 子区 (9)

| # | 子页 | 一句话 | 状态 | URL slug |
|---|------|------|------|----------|
| 01 | [Introduction to Houdini](01_introduction.md) | 节点+网络+几何属性+digital asset 四件套范式 | ✅ | basics/intro |
| 02 | User interface | 界面布局/pane/network editor | ⬜ | basics/ui |
| 03 | Viewing the scene | viewport 操作/视角/显示 | ⬜ | basics/view |
| 04 | Selecting objects and components | 选择模式/点边面/component types | ⬜ | basics/select |
| 05 | Using handles | handle 系统(平移/旋转/缩放/自定义) | ⬜ | basics/handles |
| 06 | Working with objects | object level 基本操作 | ⬜ | basics/objects |
| 07 | Tab menu | 节点创建主入口 | ⬜ | basics/tabmenu |
| 08 | Networks and parameters(顶层章节,这里只索引) | 跳到顶层 networks 章 | ⬜ | network/index |
| 09 | MacOS notes | 平台差异 | ⬜ | basics/macosx |

### Next steps 子区 (9)

| # | 子页 | 一句话 | 状态 | URL slug |
|---|------|------|------|----------|
| 10 | Dashbox | 找东西的统一搜索框 | ⬜ | basics/dashbox |
| 11 | Radial menus | 径向菜单 | ⬜ | basics/radialmenus |
| 12 | Using the ladder | 数值 ladder 编辑器 | ⬜ | basics/ladder |
| 13 | **Cooking** | **求值模型(关键概念)** | ⬜ | basics/cooking |
| 14 | HUD handles | 屏幕覆盖式 handle | ⬜ | basics/hud_handles |
| 15 | Visualizers | 调试可视化层 | ⬜ | basics/visualizers |
| 16 | Inspection mode | 几何检视模式 | ⬜ | basics/inspection |
| 17 | Brush tools | 笔刷类工具基础 | ⬜ | basics/brush |
| 18 | Project management | 项目目录/$HIP/$JOB | ⬜ | basics/project |

### Customization 子区 (8)

| # | 子页 | 一句话 | 状态 | URL slug |
|---|------|------|------|----------|
| 19 | Houdini Path | $HOUDINI_PATH 解释 | ⬜ | basics/houdinipath |
| 20 | Configuring Houdini | houdini.env 等配置 | ⬜ | basics/config |
| 21 | Desktops and panes | 工作区与面板布局 | ⬜ | basics/panes |
| 22 | Customize the shelf | 自定义 shelf | ⬜ | shelf/customize |
| 23 | Environment variables | 环境变量参考 | ⬜ | basics/config_env |
| 24 | Customize menus | 菜单自定义 | ⬜ | basics/config_menus |
| 25 | Creating shelf tools | 制作 shelf 工具 | ⬜ | ref/windows/edittool |
| 26 | Configuring hotkeys | 快捷键配置 | ⬜ | basics/hotkeys |

### Guru-level 子区 (4)

| # | 子页 | 一句话 | 状态 | URL slug |
|---|------|------|------|----------|
| 27 | Create variations with takes | takes 系统(参数版本控制) | ⬜ | basics/takes |
| 28 | Speed up your scene | 性能优化总览 | ⬜ | basics/optimize |
| 29 | Advanced Viewport Shading | 视口着色进阶 | ⬜ | basics/viewporteffects |
| 30 | Memory toolbar | 内存监控 | ⬜ | basics/memorytoolbar |

## 本章前置 / 依赖

- **前置**: 无(手册起点)
- **本章会引用、但要在后续章节深拆的概念**:
  - Networks and parameters → 顶层独立子区(本章子页 08 是入口)
  - Geometry / Attributes 完整模型 → Group 2 > Geometry
  - Digital assets 完整制作流程 → Group 2 > Digital assets
  - Wrangle / VEX → Group 6 (Nodes) + Group 9 (VEX 参考)

## 章节通读后做反思

完读 30 子页后写 [99_reflection.md](99_reflection.md),按 [[feedback_houdini_reflection]] 的 5-问模板。
