---
name: houdini-pcg-city-pipeline
description: City/district-scale PCG pipeline — data-driven (OSM road network + satellite imagery) procedural generation of urban scenes in Houdini, integrated into UE5. Three-stage workflow (data prep → Houdini PCG calc → UE integration), 5km×5km tiling, 5-track parallel decoration (lane decals / street props / traffic splines / building footprints / landscape). Use when user wants to build/做/造/搭 a city, district, urban scene, street block, virtual city, real-city replica, or 城市仿真. TRIGGERS: mentions OSM data, JOSM, real-world coordinates / 经纬度, satellite imagery / Google Earth / 卫星图, road network / 路网, city block / 街区, urban-scale / city-scale procedural, building footprints, lane markings as decals, 5km tiling, traffic AI splines, City Sample / Mass AI, 程序化城市, 把 X 市做出来, OSM 路网导入 Houdini, 用真实数据做城市. Sister skills — `houdini-pcg-practitioner` is generic PCG (any asset class); this one specializes in city scale + real-world data inputs. `houdini-architect-analysis` is for READING existing city projects.
---

# Houdini PCG City Pipeline

## Purpose

Build city/district-scale procedural scenes from real-world data. Distilled from the 腾讯 PCG 城市仿真流程 reference and city-PCG industry conventions.

Defining traits vs. generic PCG:
- **Data-driven, not invented** — OSM + satellite are the ground truth; procedural fills gaps and adds detail
- **Tiled, not monolithic** — 5km×5km is the unit of work; never try to compute 30km² at once
- **Decoration parallelism** — once road surfaces and lots exist, 5 decoration tracks fan out independently
- **decals over geometry** — lane markings, crossings, arrows, lines are decal projection points, not mesh

If user asks for a non-city PCG asset (vegetation, dungeon, vehicle, etc.) → defer to `houdini-pcg-practitioner` instead.

## Canonical 4-layer architecture (use this organization always)

The three-stage data/PCG/UE pipeline below is the *outer* shape. The user's canonical *inner* organization for the PCG side itself is **4 layers, with bounding box as the contract between large-scale and small-scale PCG**:

```
Layer 1 — ROADS                  (build the road network first)
   │
   ▼
Layer 2 — SPATIAL PLAN           (decide building distribution + ground plan: blocks, lots, land-use)
   │
   ▼
Layer 3 — BUILDING BBOXES        (one OBB per building — the contract)
   │       fields: pos, size(W,L,H), rotation(yaw aligned to main road),
   │               type, levels, facing(normal toward nearest main road), seed
   │
   ▼
Layer 4 — BUILDING DETAIL        (run lake-house-style PCG inside each bbox)
           ←  uses houdini_procedural_modeling 36 patterns; per-bbox parallel via for-each
```

**Why this organization is mandatory**:
- Large-scale (city placement) and small-scale (single-building detail) need different toolchains and mindsets — mixing them in one flow does both badly
- The bbox is the **only stable contract** between the two scales; upper layer only emits bboxes, lower layer only consumes bboxes
- Lower layer is then **fully parallelizable** — each building computes independently
- Upper and lower can be iterated/swapped independently (change building style → only Layer 4; change city density → only Layer 2-3)
- Direct `footprint → polyextrude` (the 腾讯 reference doc default) caps at mass-model realism; bbox + lake-house unlocks per-building detail realism

**How Layer 4 is implemented**:
- Wrap the lake-house method into an **HDA** that takes bbox attributes as parameters and outputs the building mesh
- City-level for-each iterates bboxes, calls the HDA once per bbox
- HDA must `fit` itself to the bbox (no hardcoded dimensions; everything `ch()`-driven from bbox size)

This 4-layer view aligns the three-stage pipeline like so:
- Layers 1-2 = stage 2.1-2.3 + 2.7 (roads → blocks → footprints in the three-stage view)
- Layer 3 = the moment you turn footprints into typed bboxes (an attribute-promotion step the reference doc skips)
- Layer 4 = a *new* stage the reference doc doesn't have — replaces "polyextrude footprint" with full building PCG

## When to use

Trigger this skill on any of:

- **Subject**: city, urban, district, block, neighborhood, street; 城市/区域/街区/城区
- **Data inputs**: OSM, OpenStreetMap, JOSM, satellite imagery, Google Earth, real-world coordinates, lat/lon, WGS84
- **Tooling**: City Sample, UE Mass AI, Cesium, Esri, Mapbox, PolyExpand2D, straight skeleton for blocks
- **Goal verbs in Chinese**: 做/造/搭/搭建/复刻 一个城市,城市仿真,虚拟城市,程序化城市,把 X 市做进 UE,用 OSM 路网做城市

## The three-stage pipeline

### Stage 1 — Data preparation (~30% of total work)

The dirtiest, most underestimated stage. New practitioners think PCG = Houdini nodes, but cleaning OSM is where most weeks disappear.

| Step | Tool | Output | Watch out |
|---|---|---|---|
| 1.1 Pick area | Google Earth | lat/lon + bounding box | Note WGS84 vs local projection |
| 1.2 Pull OSM | **JOSM** (not raw Overpass) | Filtered .osm | Filter highway types; drop ferry/junction noise |
| 1.3 Clean | Houdini SOP + manual scripts | Topology-correct polylines | **The hardest step**. Dead-ends, parallel duplicates, bridges/tunnels overlapping at z=0, roundabout encoding, force-orthogonalization for Asian grids |
| 1.4 Tile | Houdini box clip | 5km × 5km tile units | 5km is the empirical sweet spot; bigger blows GPU, smaller has too many seams |
| 1.5 Re-merge | Houdini for-each | Stitched master | Handle seams via overlap-and-trim |

### Stage 2 — Houdini PCG computation (~35% of total work)

Single-tile workflow, run inside `For-Each Tile` block. 8 sub-steps; first 3 are sequential (skeleton), last 5 are **parallel decoration tracks**.

```
2.1 OSM road network (input polylines with highway attribute)
        │
        ▼
2.2 Road surface + main blocks    ← PolyExpand2D with width-by-attribute
        │
        ▼
2.3 Sub-block subdivision         ← Straight skeleton → area-threshold split
        │
        ├──▶ 2.4 Lane DECALS       ← Scatter points + type enum (crossing/arrow/divider)
        ├──▶ 2.5 Street PROPS      ← Scatter along curves (lights/poles/bins)
        ├──▶ 2.6 Traffic SPLINES   ← Lane curves with direction → for UE Mass AI
        ├──▶ 2.7 Building FOOTPRINT ← OSM building polygons + procedural fill, height from `building:levels`
        └──▶ 2.8 Landscape FILL     ← Land-use classification (grass/water/dirt) → color codes for UE Foliage
```

Output to UE: a single export per tile containing point clouds (decals/props), splines (traffic), polygon meshes (road surface), building footprints with metadata, and land-use plots.

### Stage 3 — UE integration & rendering (~35% of total work; mostly outside Houdini)

| Sub-step | Owner | Notes |
|---|---|---|
| Asset library | Art | Building meshes by type, props, vegetation. **PCG is just placement orchestrator.** |
| Houdini Engine import | TA | Or HDA + parameter exposure |
| World Partition | TA + Level | Tile = WP cell |
| LOD strategy | TA | HLOD per tile |
| Lumen / lighting | DP | UE5 GI for the City Sample look |

## Critical decision points (ask up front)

1. **Scale & coverage** — single district (5km), city center (5×5 tiles), or whole city (10+ tiles)?
2. **Real-world fidelity** — must replicate (need GIS pipeline) or "inspired by" (can fudge data)?
3. **Vertical complexity** — flat city (Asia grid), hills (SF/Chongqing), or mixed?
4. **Traffic AI requirement** — if yes, traffic SPLINES (step 2.6) becomes critical and needs `lanes`/direction encoding upfront
5. **Engine target** — UE5 City Sample style? Unity? Custom? Determines export format and decal pipeline

## Anti-patterns (5 reflexes from the reference doc)

- ❌ **Underestimating data cleanup** → schedule >25% of timeline for it
- ❌ **Trying to compute the whole city in one Houdini scene** → always tile
- ❌ **Lane markings as polygon meshes** → 30km² will explode poly count; use decal points
- ❌ **Coupling decoration tracks** → keep decals/props/splines/buildings/landscape independent so artists can iterate one without rebuilding others
- ❌ **Polishing in Houdini viewport** → Houdini will look like a kindergarten color collage; UE+Lumen makes it real. Optimize for topology correctness, not visual polish

## Tool stack reference

| Layer | Tool | Why |
|---|---|---|
| Area selection | Google Earth Pro | Free, easy lat/lon copy |
| OSM editing | **JOSM** (Java OpenStreetMap) | Visual filter, preserves way/relation topology |
| Tiling + PCG | Houdini SOP + Compile Block + For-Each | Tiled iteration |
| Road surface | `PolyExpand2D` | Width-by-attribute, no degenerate verts (vs Polywire) |
| Block subdivision | Straight skeleton (custom or Labs) | Topology-aware |
| Decoration scatter | `Scatter` + `Copy to Points` | Per-track instancing |
| Engine | UE5 + Lumen | City Sample reference visuals |
| AI traffic | UE Mass + ZoneGraph | Consumes traffic SPLINEs |

## Output expectation when this skill activates

When user describes a city-PCG task, the response shape should be:

1. **Clarify** the 5 critical decision points above (only ask the unanswered ones)
2. **Three-stage breakdown** — what they need to do in data prep / Houdini / UE
3. **Tile sizing** — recommend 5km×5km unless they push back
4. **Network skeleton** — list the SOPs they need, in order, with the parallel-decoration fan-out clearly drawn
5. **Asset library checklist** — what art needs to deliver before PCG matters
6. **First-pass milestone** — get one ugly tile end-to-end before iterating; resist the urge to design 7 features in parallel

## Sister skills

- `houdini-pcg-practitioner` — generic PCG for any asset class; **invoke for Layer 4** when designing the per-building HDA itself, or when user wants vegetation/dungeon/vehicle (non-urban)
- `houdini-architect-analysis` — read EXISTING city or PCG projects; this skill is for WRITING new ones
- `houdini-manual-deepdive` — for learning a specific Houdini node/concept that comes up during city PCG (e.g., "how does PolyExpand2D handle T-junctions?")
- `houdini-mcp` — if the user wants you to actually drive Houdini live to demonstrate

## Related memories

- `feedback_houdini_city_pcg_layered_with_bbox.md` — **the canonical 4-layer organization** (this is non-negotiable for city PCG tasks)
- `reference_pcg_city_template.md` — original notes from the 腾讯 reference doc with workload breakdown (a reference example, but its building layer is too thin — replace with bbox+lake-house)
- `houdini_procedural_modeling.md` — 36 reusable VEX patterns (this is what Layer 4 draws from)
- `houdini_pcg_practitioner_goal.md` — the meta-goal: become a PCG practitioner, not just an analyst
