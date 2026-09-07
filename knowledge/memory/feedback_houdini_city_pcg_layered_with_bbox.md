---
name: feedback-houdini-city-pcg-layered-with-bbox
description: "User's canonical 4-layer architecture for city-scale PCG — roads → spatial plan → bbox → lake-house-style building infill. Bounding box is the contract that bridges large-scale city PCG and small-scale building PCG."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1dcb6f09-0654-4fe2-807e-f9c3ced703ed
---

# 城市 PCG 必须按 4 层组织,bbox 是大小尺度的桥

## 规则

做城市级 PCG 时按 **4 层** 顺序组织,**绝不**直接从地块挤建筑:

1. **道路层** — 先建路网(用 OSM 清理后的拓扑)
2. **空间规划层** — 在路网约束下确定建筑分布 + 地面规划(地块切分 + land use)
3. **Bounding Box 层** — 为每栋建筑树立 bbox,这是上下游的 contract
4. **建筑细节层** — 在每个 bbox 内,按 [[houdini_procedural_modeling]] 36 patterns(湖边小屋方法)生成单栋建筑

## Why

- **小尺度细节(湖屋方法)和大尺度规划(城市仿真)用不同的思维和不同的工具**,直接混在一个流程里会两边都做不好
- bbox 是 **唯一的 stable contract**:上层只需要产出 bbox(尺寸+类型+朝向),下层只需要 fit 到 bbox 内
- 这样 **下层可以完全并行**(每栋建筑独立运行湖屋 PCG),且上层和下层可以分别迭代/换实现
- 直接 footprint→挤出 的城市(腾讯 ref 那种)只能拿 mass model 级别的真实感;走 bbox+湖屋方法 才能拿到单栋建筑细节级别的真实感

## How to apply

- **任何 city/district/街区 PCG 任务**,组织流程都按这 4 层
- bbox 不是简单 AABB,**要带这些字段(contract)**:
  - `pos` 中心 / `size` (W,L,H) / `rotation` (yaw,对齐主路朝向)
  - `type` 建筑类别(住宅 / 办公 / 商业 / 老厂 / 公共)
  - `levels` 层数(从 OSM `building:levels` 来)
  - `facing` 主立面朝向(指向最近主路的法线)
  - `seed` 随机种子(让下层 deterministic)
- **下层是 HDA**:封装湖屋方法成 HDA,接受 bbox attribute 当参数,输出建筑 mesh
- **上层 for-each block**:每个 bbox 调一次下层 HDA,城市循环并行
- 这种组织 = "城市级是 placement orchestrator,建筑级是 detail generator"

## 关联

- 落地手册在 skill [[houdini-pcg-city-pipeline]],该 skill 把这 4 层作为 canonical organization
- 下层细节方法库在 [[houdini_procedural_modeling]] 的 36 patterns
- 跨尺度 PCG 的目标是符合 [[houdini_pcg_practitioner_goal]] 的"做出来"水平
- 腾讯 ref 文档 [[reference-pcg-city-template]] 是"上层做得不错但下层是空的"的反例,刚好是这个架构需要补的下层
