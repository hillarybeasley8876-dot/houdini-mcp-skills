---
name: houdini-procedural-modeling-patterns
description: Core VEX patterns and structural ideas distilled from the Lake House Houdini project — reusable templates for any procedural modeling work
metadata: 
  node_type: memory
  type: reference
  originSessionId: 21a8adcb-6945-41b8-896f-b327fc5fcd45
---

Reference for Houdini procedural modeling, distilled from `C:\Users\Administrator\Downloads\Lake_House_Prj\Lake_House_Modeling.hip` (191 wrangles, 1701-line topology). Full notes at `Lake_House_Prj/_analysis/` — **Part 4 has the strategic-level insights** (the rest are tactical patterns).

**Expanded corpus (2026-05+)**: Lake House covers static-asset PCG only. The "落于ivi" master collection (660+ project files) extends to sim / animation / growth / CA — patterns now folded into `houdini-architect-analysis` skill (ALGORITHMS A8-A14, PATTERNS section list grew to ~25 patterns) and `houdini-pcg-practitioner` skill (VEX_RECIPES R21-65). Major new categories: edgetransport (graph-distance), Gale-Shapley CA migration, fBm octave noise, volume gradient ascent, two-stage solver bridge, multi-OUT subnet API, color-as-group-token, per-element staggered timing, surface-tangent noise projection, dihedral instancing, sopsolver per-frame state accumulation. **PCG 不只是建筑** — sim+animation 是同一思维框架的延伸。

## Core pipeline structure (any building/structure model)

```
体积生成 → 语义标签 → 标签细化 → 模块挂载 → 程序化纹路 → 整体变形 → 合并
```

Concretely:
1. `scatter → make_grid (rint(P/g)*g) → fuse → delete_edge_points (pcopen+pcnumfound)` — random points snapped to grid
2. `vdbfrompolygons → convertvdb` — boolean union of stacked boxes
3. `init_attributes`: classify each prim by `normal.y` + `pos.y` + `area` into `s@type ∈ {roof, floor, support_full/partial, wall}` ← **the semantic backbone every downstream module reads**
4. Per-module subnet skeleton: `attrib_init → name suffix wrangles → del_too_close/del_unneeded → object_merge → copytopoints`
5. Module path = `modules/<cat>/<cat>_<s@name>_<s@variation>.obj`. Always use `s@name + s@variation + v@scale + @N` quartet.

## 13 must-know VEX patterns

1. **Grid quantize**: `@P.x = rint(@P.x/g)*g` — random snapped to grid
2. **Density filter**: `if (pcnumfound(pcopen(0,"P",@P,r,n)) < threshold) removepoint(...)`
3. **Probability + weighting**: `if (rand(seed+@primnum) > prob + condition_bonus)` — e.g. top-floor windows more likely
4. **Geometry veto**: `intersect()` or `pcopen()` to delete invalid placements *after* random distribution
5. **relbbox**: scale-independent positional logic, returns 0..1
6. **Variable length → integer modules**: `n=round(dist/size); scale=(dist/n)/size` — fills exactly without seams
7. **Topology neighbours**: 17.5+ `polyneighbours(0,@primnum)`; older = manual via `pointprims` + count occurrences (shared-edge if `count%2==0 && count>0`)
8. **Attributed neighbour query**: `pcopen → while(pciterate(handle)) pcimport(handle, "attr", var)`
9. **Single-step iterator**: detail wrangle does ONE thing (mark a pair, set keep=1) + `break`; outer for-loop block reruns until `i@stop=1`
10. **Topo-sort longest path**: for height ranking — `my_h = max(incoming_heights)+1`
11. **2D dihedral angle**: `angle = degrees(acos(dot(N, ref))); if (sign condition) angle = 360-angle`
12. **Axis selection**: `move = abs(cross(@N, {0,1,0}))` → find which component is 1 → operate only on that axis
13. **`uv_prim`**: relative bbox + `uvspace`-normalized random U/V offset → no tile repeats. ⭐⭐⭐ This 30-line pattern solves procedural UV layout permanently.

## 10 thinking constraints

1. Don't translate boxes into place — find positions, label semantics, copytopoints modules
2. ALWAYS use `relbbox` / relative coords (never hard-code `P.x = 5`)
3. Probability = base + condition bonus (gives "top-floor windows more frequent" emergent rules)
4. Post-hoc veto > pre-emptive precision: distribute, then delete invalid via intersect/pcopen
5. `lattice + mountain + group_expression` is the standard regular→organic deformation sandwich
6. `rand(seed + position)` not `rand(seed + ptnum)` — same place = same output, lets neighbouring points jitter together
7. `for-loop block + i@stop` for "unknown iteration count"
8. Variable-length geometry always = `int n + scale comp` to avoid gaps
9. `s@type` (per prim semantic) + `s@name + s@variation` (per point module) is non-negotiable infrastructure
10. Use `pcopen + pciterate + pcimport` to read neighbour attributes directly — don't manually loop and `point()`

## Useful helper APIs to remember
- `intersect(input, origin, dir, &pw, &uvw)` returns prim hit or -1
- `intersect_all(...)` returns ALL hits along ray (useful for towers/columns down to ground)
- `relbbox(input, P)` returns `[0..1]^3` relative position in bbox
- `nearpoints(input, pos, radius)` simpler than `pcopen` when no attribute import needed
- `pcfind` returns ALL points in radius vs `pcopen` which gives a handle
- `getbbox(input, &min, &max)` for prim/geo bbox in VEX

## .hip file format note
.hip files are ASCII cpio archives (`magic 070707`). Parse with custom Python (no Houdini needed for read-only inspection). Per-node files: `.def` (topology + inputs), `.init` (`type = <opname>`), `.parm` (parameters incl. wrangle `snippet`).

## ⭐ Strategic-level insights (Part 4 deep dive)

Tactical patterns above are *what to write*. These are *how to think about the whole project*:

1. **Hidden cross-subnet bus** — `object_merge` nodes form 18 horizontal edges between subnets, not just 5 parallel branches. A few "service nodes" (`tower_check`, `stairs_pt`, `support/full_support`, `closed_balc/building_footprint`) are read by 2-3 other subnets — name them well, they become implicit API.
2. **Numerical robustness trinity** — every fuse in the project is `tol3d=0.001 + distancesnap`. Rule: any wrangle modifying `@P`, any VDB→polygon, any merge — **must** be followed by `fuse(0.001, distancesnap)`. Otherwise downstream `pcopen/neighbours/topology` silently corrupts.
3. **`rint(x*100)/100` discrete-key pattern** — when using float position as `rand()` seed key OR as equality test, must quantize first. Three flavors: `rint(x*10)/10` (relbbox boundary), `rint(x*100)/100` (position seed key), `abs(rint(N))` (axis-aligned direction normalization).
4. **Tiny parameter universe** — 191 wrangles share <10 unique `ch()` handles (mostly `seed`, `probability`, `iteration`, `scale`, `uvspace`). Complexity lives in VEX, not in parameters/sliders. Anti-pattern: 50 sliders. Right pattern: 5-10 meaningful knobs + smart VEX.
5. **Decision-tree justifications** — VDB > polybool (handles touching/coplanar geometry); DLA > L-system (organic without grammar); string `s@type` > int (greppable, concatable into paths, extensible); copytopoints+attrib > copy+stamp (per-point control + cacheable); post-hoc veto > precise picking (parallelizable + composable); integer-segments+scale > stretch (no seams).
6. **Failure modes** — grid `(2,3,2)` is hard-coded across 100+ places (radii like `2.1`, `0.1`, `1.5` are all relative to it). To make it tunable, hoist to detail attrib. Module path = `<cat>_<s@name>_<s@variation>.obj` — typos silently produce no geometry; build a validator wrangle. World-position arithmetic loses precision past ~1e5; do all procedural work in local coords.
7. **Five-stage generalization** — 体积分布 → 体积合并 → 语义初始化 → 标签细化+模块挂载 → 纹路+变形. Same structure works for castles, sci-fi ships, dungeons. Stages 4-5 (and 13 VEX patterns) reusable verbatim across projects; only stages 1 and 3 change.
8. **Pre-coding 8-question checklist** — (1) what are the Lego pieces (`s@name` dictionary)? (2) gridded or organic? (3) semantic class criteria (normal/pos/area/neighbour)? (4) which positions+modules need mutual avoidance? (5) which outputs are services consumed by 2+ subnets? (6) what variable-length edges need integer-segment tiling? (7) UV strategy? (8) overall deformation needed?
9. **Complexity conservation** — "few nodes, few parameters, long wrangles" is the maintainable form. Anti-pattern: 100 SOPs wired into a circuit (every change reroutes everything). Right: 1 wrangle of 30 clear lines + ch("seed").

## ⭐ Roof system patterns (Part 5 deep dive)

The roof_base subnet (~30 wrangles, ~7 phases) is the most sophisticated chunk. Patterns reusable beyond roofs:

10. **"Attribute-first, geometry-last" pipeline** — entire 7-phase pipeline (合并→主方向→宽度→有向图→高度→抬升→几何) does NOT modify geometry until the final extrusion. All semantic info (dir, width, incoming/outcoming, height, elevation, platform) is accumulated as prim attributes first. Lets each step be debugged independently.
11. **For-loop block `method` matrix** — `feedback` (output is next input, used when geometry changes), `piece` (process one prim per iteration, output merged), `count` (pure repetition). Default to `piece`; only use `feedback` when truly needed.
12. **Multi-input wrangles** — `incoming` wrangle has 4 inputs (self, midline, edges, neighbour-cloud). When one wrangle needs multiple kinds of context, use 4 inputs not 1 input + workaround. Use `point(N, ...)` / `prim(N, ...)` to pull from any input.
13. **`pcimport` for neighbour attributes** — `pcopen + pciterate + pcimport(handle, "attr", var)` reads neighbour attributes directly without `point()` reverse lookup. Zero overhead inside the open handle, automatically distance-sorted. Strictly preferred over `nearpoints + point()`.
14. **Cycle detection + fallback in directed graphs** — `check_for_height_conversion` detects A→B→C→A cycles in incoming/outcoming, clears the edges, and marks `i@convert=1` so downstream `elevation_platform` makes that prim a flat platform instead of trying to assign height. Any directed-graph algorithm in procedural geometry needs this.
15. **Geometric fallback for isolated elements** — `assign_dir_to_separate_roofs` handles roofs with no neighbours by using the longer edge of the prim itself as `dir` (or `rand` for square prims). Always plan for "what if this element has no context?"
16. **Multi-ray decision trees** — `normals_and_ray` is the canonical pattern: cast 3-4 rays in different directions, decide branch based on which hit. 4 branches for: hit perpendicular roof / hit same-direction lower roof / hit wall / hit nothing. Each branch modifies `@P` AND sets a flag (`i@raypoint`) for downstream consumption.
17. **Vertex-order rewind to flip face winding** — to flip a prim's normal, don't change `N`; rebuild the prim with `removeprim(0, @primnum, 0)` (keep points) + `addprim` + `addvertex` in reverse order. This is the only way to actually change winding.
18. **Same-position neighbour disambiguation** — when a point has multiple neighbours, use a secondary criterion (e.g. `pos.y == @P.y` to find "ridge endpoint") rather than just taking neighbour[0]. Especially important after fuse merges.
19. **"Cross-wrangle event-flag" attributes** — `i@stop`, `i@keep`, `i@convert`, `i@raypoint`, `i@side` are not geometric — they are inter-wrangle protocol flags. Document explicitly which attributes are "public protocol" (consumed by downstream) vs "private internal".
20. **Architectural domain rules embedded in VEX** — roof system encodes 30°-60° angle limits as hard constants in `get_roof_elevation`. When the math says 70°, code carves out a platform instead. Procedural realism = real-world physical constraints in VEX, not pure rand.

## ⭐ Cross-project distillation: 落于ivi 大合集 (660 .hip files)

Confirms and extends the Lake House lessons. The collection's master file `Houdini vex 整理.hip` is itself a curated 232-wrangle/181-stickynote VEX textbook by ruoyu.zhang@miHoYo.com — the daily mini-projects are applications.

### Patterns the master VEX file confirmed (already known)
- pcfilter neighbour blur, fit/rand/length/distance, matrix-rotation idiom, integer-segment tiling — all reproduced in master VEX 49-55, 25-44.

### Patterns NEW to the collection (added to skill files)

21. **Two-stage solver bridge** — solver A (deformation) → wrangle converts (rest_P − cur_P) into velocity, **gated by frame** → solver B (RBD/POP). 2401_10 wave-fracture is the canonical case. The bridge wrangle is always the project's single most important node. (Recipe R21, Algorithm A9)

22. **`edgetransport` for graph-distance attribute** — `findshortestpath → edgetransport → attribremap → sweep` is the standard "vine/root/branch with tapered diameter" pipeline. Edgetransport spreads attribute *along* topology, not through space. (Recipe R22, Algorithm A8)

23. **HDA-style multi-OUT subnet** — name 5+ output nulls `OUT_BRIDGE`, `OUT_GEO`, `OUT_CON`, `OUT_BBOX`, etc. External consumers read only OUT_*; internals are refactor-safe. Mirror with `IN_*` for parameter inputs (2401_30 spring rebound). Mandatory once a subnet > 50 nodes.

24. **Cellular automaton on `±1, ±W` grid** — solver wrangle reads `point(1,"alive",@ptnum±1)` and `±W` for grid neighbours; transition rule = local lattice CA. Master VEX 121. Cheapest emergent-pattern engine; remember to mask wrap-around at row boundaries. (Algorithm A10)

25. **`@TimeInc` not `@Time%1`** in accumulating solvers — modulo wraps state; TimeInc accumulates monotonically. Master VEX 162 spells this trapdoor out inline. (Recipe R28)

26. **Tolerance drift correction** — every M cycles, `if (abs(state - target) <= ε) state = round_to_grid(state)` to pin float drift. Mandatory for any 1000+-step discrete-motion solver. (Recipe R30)

27. **Surface-tangent noise projection** — `noise - dot(noise, N) * N` keeps displacement on the tangent plane (no normal-direction push-through). Master VEX 178-179. (Recipe R26)

28. **Quaternion stacking with axis-scaled trick** — `quaternion(axis * angle)` shorthand: vector length = rotation angle. Stack rotations via `qmultiply`. Master VEX 149-151. (Recipe R25)

29. **`optransform()` for camera-locked anchor** — multiply `@P *= optransform(cam_path)` to lock geo into camera-relative frame. Master VEX 125-131. (Recipe R24)

30. **`@opinput<N>_<attr>`** shorthand — implicit `point(N, attr, @ptnum)`. Built-in attrs auto-typed; user attrs default float. Master VEX 63-67. (Recipe R27)

31. **Conditional point synthesis at extrema** — `if (@ptnum==0 || @ptnum==@numpt-1)` to add boundary anchors with named-anchor / piece-name attribs for constraint networks. 2401_22 rope bridge. (Recipe R23)

32. **Auxiliary geometry as parameter source** — N positional parameters → N points on a small input-2 geo, accessed via `point(2, 'P', i)`. Better than 3N sliders; gizmo-controllable. (PATTERNS.md "Auxiliary-geometry-as-parameters")

33. **detail-intrinsic group manipulation** — `detailintrinsic(0, "primitivegroups")` to read live group list; `expandprimgroup` to act on a randomly-picked group each frame. Master VEX 117-120. (Recipe R31)

34. **Sliding-puzzle swap pattern** — beat-snapped state change + interpolated mid-beat motion. Master VEX 167. Generalizes to any "discrete state at beats, smooth between." (Recipe R33)

35. **`vertexprimindex`** for reliable curve start/end — topology-truth answer; UV-based detection is unreliable post-resample. Master VEX 173-174. (Recipe R34)

36. **`chramp` over fit+if-else** — author the curve in the parameter panel; iterate visually. Master collection uses 30+ times. (Recipe R35)

### Architecture rule (new)
When VEX wrangle has > 3 noise composites → switch to VOP. When VOP has > 5 if-branches → switch to VEX. Confirmed by 落于ivi: stained_glass uses VOP, bridge uses VEX, spring rebound uses CHOP. Pick the context with lowest friction for each task. (PATTERNS.md "When VEX, when VOP, when CHOP")

### Author's pedagogical pattern (worth absorbing)
Master VEX 100-107: same effect refactored 7 times in succession (`length(@P)*scale → sin → +1 → /2 → *0.5 → inline`). Author teaches **progressive compression** — write it long and clear first, then collapse. Anti-pattern: writing the dense form upfront.

The 660-file collection's structural lesson: **most procedural recipes are 1 specialised node (findshortestpath / ripplesolver / curlnoise / vellumcloth) + 1-3 small bridge wrangles**. The wrangles are short; the smarts is in node choice. When analysing such a project, name the central node first, then read the bridge wrangles — that's 90% of the effect understood.

## Project reflections (反思五问 applied to 12 representative projects)

Full reflections at `C:\Users\Administrator\houdini_study\PROJECT_REFLECTIONS.md`. Each project follows the 5-question template (why built this way / project meaning / per-node role / per-attribute role / reproduction recipe + variations).

The 12 covered: 路径搜索分支管 / 波纹激活碎裂 / 物理桥B(HDA) / 彩色玻璃(VOP) / 弹簧回弹(CHOP) / 极坐标水波 / 编织 / 互相握手迁移 / 线条收缩(梯度) / 珊瑚生长 / 桥 ABC 演化 / 前缀和堆叠.

### Cross-cutting architectural lessons (the elite-architect reflexes)

1. **第一眼盯中央特化节点** — 90% 工程是"1 specialised node + 几行桥 wrangle"。`findshortestpath` / `ripplesolver` / `curlnoise` / `volumesamplev` / `edgetransport` / `straight_skeleton_3d` 都是。"桥 wrangle"在节点链中央，是项目灵魂，删了项目废。
2. **属性必须分四层**：geometric (P/N/Cd) / protocol (i@stop, s@constraint_name) / scratch (ramp 输出) / control (group_fixed)。混合放就乱。
3. **子网 50+ 节点必须 OUT_*** API — 没 OUT_* 的子网是定时炸弹，下游谁都不敢碰内部。
4. **VEX/VOP/CHOP 的 dual 选择**：3+ 噪波合成切 VOP；5+ if 切 VEX；时间序列滤波切 CHOP。
5. **Solver 架构铁则**：`@TimeInc` 不要 `@Time%1`；`Prev_Frame` 读源；容差矫正每 N 帧 `rint`；多 solver 串联中央 wrangle 是桥。
6. **复现配方不是 5-8 步算讲清楚** — 这才是把"思路"变"能力"的关键产出。

### 元反思 (meta-pattern from reading 12 reflections)

The 12 reflections clustered into 7 algorithm families (graph / solver-coupling / HDA-architecture / VOP-CHOP-selection / coordinate-conversion / morph-chain / distributed-algorithm). When facing a new procedural requirement, **first ask which family it falls in** — that decides 80% of the architecture. The rest is parameter tuning.

## ⭐ Theory groundwork + Cross-tool comparison + Deep reflections (master-tier write-up)

External files at `C:\Users\Administrator\houdini_study\`:

- **THEORY_GROUNDWORK.md** — 4 大数学补课：Eikonal/FMM、MCMC/Metropolis-Hastings、谱噪波 vs hash、DDG (cotangent Laplacian)。每节包含：连续 PDE/分布/spectral/operator 的形式定义、4 种 discrete 实现的统一骨架、何时哪个赢、落于ivi 缺席度。**核心 punchline**: 看 wrangle 问 4 题：解什么 PDE？采样什么分布？谱性质？收敛到什么连续算子？
- **CROSSTOOL_COMPARISON.md** — Houdini SOP vs Unreal PCG vs Geometry Nodes vs Substance Designer。5 个落于ivi 工程 × 4 工具矩阵 + 战略综合：Houdini 护城河 = 仿真链 + 图算法 + 状态迭代 + 跨上下文（DOP/SOP/POP/CHOP/COP）；商品化能力 = 噪波 + 简单聚合（Substance / GN 持平或更优）。**职业方向**：避免做与 Substance/GN 重叠的 commodity 技能；专注 solver coupling、graph algorithms、HDA API 设计。
- **PROJECT_REFLECTIONS_DEEP.md** — 3 个标杆深度反思（路径搜索 / 波纹碎裂 / 互相握手迁移）。每个包含：连续数学层面在做什么 PDE/算法、节点必要性的因果诊断、属性数据流的主属性识别、量化失败模式、master ceiling 是什么数学手段（不只是"还能做 X"），跨学科算法谱系（4-5 领域映射）。这是 master-tier 反思的标准模板，未来分析任何 .hip 都该按此格式而不是 5-步配方。
- **TASK1_MCMC_SOPSOLVER.md** — Metropolis-Hastings sopsolver 完整模板 + 5 种 energy 函数库 + 退火 schedule + 4 个真实应用（stippling / Wang tile / 家具布局 / phyllotaxis with constraints）+ 调参手册（接受率 0.2-0.5、parallel tempering、Gibbs/HMC 选型）。落于ivi 全空白能力。MCMC 是 Houdini master 跟 cookbook 作者的分水岭之一 — 把 "问题转 energy + 让 M-H 找解" 当一般化框架。Punchline：未来用 HDA 形式包成 `MCMC_Solver.hda`，参数化 energy 切换。
- **TASK2_EIKONAL_APPLICATIONS.md** — edgetransport 的 10 种非平凡用法（多源 Voronoi / 帧推进生长波前 / 流方向估计 / 末梢剪枝 / 距离驱动 scatter / 测地 UV / 反向 source 恢复 / time-of-arrival 切片 / 分支检测 / bridge 检测）。落于ivi 660 工程里 30+ 次 edgetransport 全部是同一种用法（ramp+sweep）— 用了 1/11。**核心心智：把 `f@dist` 当成跟 `@P/@N` 同等的第一公民属性，每个 edgetransport 上游可以接 N 个不同 consumer**。打包成 `distance_field_consumers` HDA 集是个人 IP。

每个 wrangle 必问 4 个数学问题：
1. 它在解什么 PDE / 离散方程？
2. 它在采样什么分布？
3. 它的谱性质是什么？
4. 它的离散化收敛到什么连续算子？

Cookbook 作者只能答第 0 题（"这段 VEX 干什么"）。能答 1-4 才是 master。
