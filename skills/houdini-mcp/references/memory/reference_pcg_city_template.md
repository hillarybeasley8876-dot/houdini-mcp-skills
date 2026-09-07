---
name: reference-pcg-city-template
description: "City-scale PCG pipeline template distilled from the 腾讯 PCG城市仿真流程简介 doc — OSM + Google + JOSM + Houdini + UE5, three-stage workflow with 5km tiling and 5-track decoration parallelism"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 1dcb6f09-0654-4fe2-807e-f9c3ced703ed
---

# 城市级 PCG 七层模板(腾讯 PCG 城市仿真流程)

源文档:`C:\Users\nieyi\Downloads\PCG城市仿真流程简介.docx`(腾讯文档 `DZXJGWFRTcUdJdUNx`)。文字稀疏,信息全在 22 张图;已展开解读为下面的模板。

## 三阶段骨架

1. **数据处理**(~30% 工作量) — Google Earth 选区 → JOSM 拉 OSM 路网 → **规则化脚本+人工清理**(最重的脏活)→ 5km×5km 切片 → 拼合
2. **PCG 计算**(~35% 工作量,Houdini SOP) — 路网输入 → `PolyExpand2D` 出道路面 + 主地块 → 子地块切分(直骨架)→ 5 路装饰层 **并行**(车道线 decals / 路灯 props / 车道 SPLINEs / 建筑 footprint / 景观填充)
3. **UE 集成 + 出图**(~35%) — 资产库映射 + Lumen 渲染

## 5 个反常识 / 易踩坑

- **数据清理 > Houdini 节点编排**:OSM 原始路网进 Houdini 几乎不可用,断头/平行重复/拓扑断裂全要修;这一段工作量被新手严重低估
- **5km×5km 是切片黄金值**:再大 GPU 顶不住建筑实例化;再小集成接缝多;城市级 PCG 必切片(Houdini Compile Block + For Each)
- **decals 优于几何**:车道标线、斑马线、转向箭头、双黄线全部用 decal 投影,做成 mesh 在 30km² 尺度会爆 polygon
- **5 路装饰层并行**:道路面+地块做完后,decals/props/splines/buildings/landscape 5 条线互不依赖,经典 dependency tree
- **Houdini 里"丑"= UE 里"真"**:Houdini 视口看到的彩色色块拼图(land-use plots)到 UE 出来就是细节饱满的城市;不要在 Houdini 阶段追求美观

## 工作量分布(我的判断)

| 阶段 | 占比 | 谁干 | 周期最长环节 |
|---|---|---|---|
| 数据采集+清理 | 30% | TA | 路网清理(规则化脚本) |
| Houdini PCG | 35% | TA | 道路面+地块切分参数调试 |
| 资产库 | 15% | 美术 | 建筑 mesh 库 + 材质 |
| UE 集成 | 15% | TA + 关卡 | LOD / WorldPartition |
| 渲染镜头 | 5% | 摄影 | Lumen 调光 |

## 关联

补 [houdini_procedural_modeling](houdini_procedural_modeling.md)(36 patterns 来自小尺度 Lake House)在 **大尺度 / 数据驱动** 维度的空白。和 [houdini_pcg_practitioner_goal](houdini_pcg_practitioner_goal.md) 一致 — 看完了不算完,要能自己搭。
