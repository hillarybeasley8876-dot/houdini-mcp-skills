# Patterns: Loop Blocks, Pipeline Templates, Cross-Subnet Bus

## Loop block patterns (Houdini for-loop block_begin/block_end)

The 3 `method` modes correspond to 3 different algorithmic paradigms. Choosing the wrong one causes silent bugs.

### `feedback` mode = fixed-point iteration

```
state_{n+1} = T(state_n)         # T = single-step transformation
until state_{n+1} == state_n     # i@stop = 1
```

**When to use**: geometry mutates each iteration; next iteration must see the previous output.

**Examples in Lake House**:
- `merge_roof_shapes/repeat_begin1` — merges one pair of adjacent roofs per iteration until none left
- `stacked_boxes/repeat_begin1` — DLA accretion (each iteration adds one box)
- `roof_attribs/height_assign_loop` — relaxation until heights stable
- `closed_balc/repeat_begin1` — process one closed balcony per iteration

**Convergence requirement**: T must be **monotone** w.r.t. some well-founded order, otherwise infinite loop. Concrete: each iteration must either reduce a counter (e.g., "pairs left to merge") or set `i@stop=1`.

**Anti-pattern**: trying to do "all matches at once" inside one wrangle. Race conditions / inconsistent state.

### `piece` mode = data-parallel map

```
output = map(f, [piece_1, piece_2, ..., piece_N])
```

**When to use**: each piece is independently processed; no piece depends on another's output in this loop.

**Examples in Lake House**:
- `roof_attribs/in_out_attribs` — each prim computes its own incoming/outcoming
- `roof_attribs/width_attrib` — each prim computes its own width
- `roof_attribs/get_middle_line` — each prim finds its own midline
- `roof_extrusion/roof_merge_and_sides` — each prim independently extruded

**Note**: pieces are processed **sequentially in Houdini** (not truly parallel), but the algorithm doesn't depend on order. The sequential implementation just simplifies the merge step.

**`chi("primnum")` / `chi("iteration")`** inside a piece-mode wrangle = the current piece index.

### `count` mode = truncated iteration

```
for i in 1..N:
    state = T(state)       # no convergence check
return state
```

**When to use**: convergence not well-defined OR user wants explicit count control.

**Example in Lake House**:
- DLA outer loop "give me 30 boxes" — there's no natural saturation point that's both correct and predictable, so user picks N.

**Tradeoff vs feedback**: count fixes step count, output quality varies; feedback fixes output quality, step count varies.

### Decision matrix

| Question | Answer |
|----------|--------|
| Does each iteration depend on previous? | yes → feedback ; no → piece |
| Is there a natural "done" condition? | yes → feedback (with i@stop) ; no → count |
| Need to process N independent things? | piece |
| Need to converge to a fixed point? | feedback |

## The 5-stage procedural asset template

Any non-trivial procedural asset (building, ship, terrain, dungeon, plant) follows this 5-stage pipeline. Recognizing it lets you map any new project to a familiar shape immediately.

```
┌──────────────────────────────────────────────────────┐
│ Stage 1: Volume / shape generation                   │
│   Decide WHERE things can exist                      │
│   Methods: scatter+grid+filter / VDB / L-system /    │
│            cellular automata / Voronoi / handcrafted │
├──────────────────────────────────────────────────────┤
│ Stage 2: Volume merging → outer hull                 │
│   Produce a watertight envelope                      │
│   Methods: VDB boolean / convex hull / metaball      │
├──────────────────────────────────────────────────────┤
│ Stage 3: Semantic init                               │
│   Assign s@type to each face/point                   │
│   Method: classify by normal+pos+area+neighbours     │
│   ⭐ THIS IS THE KEY DESIGN DECISION FOR THE PROJECT │
├──────────────────────────────────────────────────────┤
│ Stage 4: Refinement + module dispatch                │
│   wall → wall/window/door  ;  s@name → .obj path     │
│   Methods: rand+probability+condition_bonus +        │
│            intersect/pcopen veto + copytopoints      │
├──────────────────────────────────────────────────────┤
│ Stage 5: Pattern + deformation                       │
│   Procedural surface details + global "naturalize"   │
│   Methods: divide+random offset + uv_prim +          │
│            lattice+mountain                          │
└──────────────────────────────────────────────────────┘
```

**Key insight**: stages 1 and 3 are where projects diverge. Stages 2, 4, 5 are mostly reusable across projects (the same VEX patterns work).

**The `s@type` dictionary in stage 3 is the asset's soul**:
- House: `{wall, roof, floor, support_full, support_partial}`
- Castle: `{wall, tower, gate, battlement, courtyard, keep}`
- Spaceship: `{hull, deck, engine_mount, antenna_mount, panel, vent}`
- Dungeon: `{floor, wall, door, treasure_zone, monster_zone, secret_wall}`

When applying this template to a new asset, **design the dictionary first**.

## Cross-subnet bus / service node pattern

In any non-trivial procedural project, some sub-networks become "services" — their output is consumed by 2+ other sub-networks via `object_merge`.

### How to identify service nodes

In `00_topology.txt`, grep for `object_merge` and read each `objpath1`:

```
grep -n object_merge 00_topology.txt   # find all object_merge calls
# look up each one's objpath1 in 02_all_node_key_params.txt
```

For each unique `objpath1` consumed by 2+ subnets → that's a service node.

Lake House has 5 service nodes:
- `tower/tower_check` — consumed by body_attribs and roof_modules/setdressing
- `stairs/stairs_pt` — consumed by 3 subnets
- `support/full_support` — consumed by 3 subnets
- `body_attribs` — consumed by stairs/walkway and support/fence
- `Create_body_base/closed_balc/building_footprint` — consumed by 5 subnets

### White-box vs black-box dependency

**White-box** (anti-pattern): `object_merge` points at an internal implementation node:
```
arch/object_merge1 → support/full_support/column/keep_touching_walls
                                                   ^^^^^^^^^^^^^^^^^
                                                   internal node — fragile
```

**Black-box** (correct): `object_merge` points at a public interface node (named `PUB_xxx` or in a `services/` namespace):
```
arch/object_merge1 → support/full_support/column/PUB_column_pts
                                                   ^^^^^^^^^^^^^
                                                   stable interface
```

### Refactoring: from white-box to black-box

For each white-box edge:

1. Inside the producer subnet, add a `null` node named `PUB_<purpose>` connected to the current internal node.
2. Update the consumer's `object_merge.objpath1` to point at the new `PUB_*` node.
3. Now the producer can refactor internals freely as long as `PUB_*` keeps producing the same shape.

**Metric**: count edges where `objpath1` ends in something other than `IN`, `OUT`, or `PUB_*`. Lake House: ~18 / 18 (all white-box). Refactor target: 0.

## Numerical robustness trinity

Three patterns that show up everywhere:

### Pattern 1: rint + fuse(0.001, distancesnap)

Every Lake House `make_grid` (which does `rint(@P/g)*g`) is followed by `fuse(tol3d=0.001, snaptype=distancesnap)`. Without fuse, downstream `pcopen / pointprims / neighbours` get duplicates / float-drift errors.

**Rule**: any wrangle modifying `@P` MUST be followed by `fuse(0.001, distancesnap)`.

### Pattern 2: rint(x*N)/N for stable hash keys

```c
float pos_y_quantized = rint(pos.y * 100) / 100;
float random_offset = fit(rand(seed + pos_y_quantized), 0, 1, -0.04, 0.04);
```

Without quantization, two "logically same" positions get different rand values due to 1e-15 float drift. Three flavors:
- `rint(x*10)/10` — for relbbox boundary tests (0.1 precision)
- `rint(x*100)/100` — for position-as-seed-key (0.01 precision)
- `abs(rint(v))` — for "is this axis-aligned?" tests on direction vectors

### Pattern 3: variable-length integer-segment tiling

```c
int n = (int)rint(dist / module_size);
float scale = (dist / n) / module_size;
// place n modules with scale_z = scale
```

Used everywhere modules are placed along a polyline (railings, roof tiles, stair steps). Avoids gaps and overlaps without modifying .obj files.

## Cross-wrangle attribute protocol

Distinguish two kinds of attributes living on the same prim/point:

- **Geometric**: `@P, @N, @Cd, @uv` — describe the geometry itself
- **Protocol**: `i@stop, i@keep, i@convert, i@raypoint, s@type` — inter-wrangle "event flags"

**Anti-pattern**: leaving protocol attributes alive past their consumer. Lake House never cleans them up → final geometry carries 30+ attributes, ~2/3 of which are dead protocol flags.

**Refactor**: at each subnet's output, insert `attribcleanup` to delete `_p_*` prefixed attributes (assuming you adopted the prefix convention).

## "Service-consumer" architectural mantra

Every procedural project has the shape:
```
Foundation layer (nobody depends on the consumers)
   ↓
Service layer (the building-blocks: footprint, semantic types, occupancy)
   ↓
Consumer layer (multiple subsystems consuming services)
   ↓
Output / final merge
```

When debugging "why does changing X break Y?", the answer is almost always: **X is silently a service of Y**, but its service status was never declared. Make it explicit.

## HDA-style multi-OUT subnet (named-port API surface)

When a subnet generates multiple downstream-consumed outputs (geometry + constraints + handrails + ropes + low-poly proxies …), expose each via a separately-named `null` node prefixed `OUT_`:

```
Rope_Bridge (subnet)
  ├── OUT_BRIDGE      — final assembled bridge
  ├── OUT_GEO         — pre-fracture geometry (for backup re-sim)
  ├── OUT_CON         — constraint network
  ├── OUT_HANDRAIL_CURVE
  ├── OUT_ROPE_HIGH
  ├── OUT_BBOX        — bbox-only proxy for placement
  └── OUT_BBOX_not_XForm
```

Rules:
1. **Every external consumer reads only `OUT_*` nulls** via object_merge — never internal nodes. The OUT_ nulls are the public API; internals are implementation.
2. **Naming carries semantics**: `OUT_BRIDGE` = the headline product; `OUT_BBOX` = lightweight proxy; `OUT_GEO` = pre-finalize state for re-use. A reader can scan the null names and immediately know what the subnet provides.
3. **`IN_*` mirrors on the input side**: `IN_BODY`, `IN_POINTS` for parameters supplied from outside (see 落于ivi 2401_30 spring rebound).
4. **The subnet is now refactor-safe**: as long as the OUT_ nulls produce the same shape, internals can be rewritten freely.

Anti-pattern: a single output port carrying merged geometry where downstream nodes have to `blast` to extract pieces — that throws away semantic info and forces every consumer to re-discover what's what.

This pattern is the Houdini-native equivalent of "exporting a public interface from a module." For any subnet that becomes 50+ nodes, it's mandatory.

## Solver-accumulation patterns (3 trapdoors)

Inside a `sopsolver` / `dopnet`, three patterns repeatedly bite people. Each has a stable fix.

### Trapdoor 1: `@Time%1` vs `@TimeInc`

```c
// WRONG inside an accumulating solver — modulo wraps at 1.0s, snaps state
angle = $PI/2 * @Time%1;

// RIGHT — TimeInc = 1/24s per frame, accumulates monotonically
angle = $PI/2 * @TimeInc;
```

Master VEX 162 (Rubik's cube) has the inline comment explaining this exact mistake. Rule: anywhere state must accumulate frame-to-frame (rotation, integration, growth), use `@TimeInc`, not `@Time%1`.

### Trapdoor 2: float drift accumulation → tolerance reset

After many iterations, rotated/translated positions drift away from "should be on the integer grid." Inject a tolerance-snap each cycle:

```c
// Inside a sopsolver, every cycle
if (abs(sum(@P*axis) - slice) <= 0.001) {
    @P = round_to_grid(@P);  // re-snap to integer position
}
```

This is the "rubber-band correction" pattern — accumulate freely, but pin to the nominal grid each cycle. Without it, 1000-step solvers drift visibly.

### Trapdoor 3: `Prev_Frame` vs `Current_Frame` in CA

Cellular automata read neighbours from the previous frame, write to current. Don't read from input 0 (current state being written) and write to it — race condition.

```
sopsolver inputs:
  [0] = current state (write target)
  [1] = Prev_Frame (read source)        ← always read neighbours from here
```

Master VEX 121 wires Prev_Frame explicitly through `dop_geometry`. If you ever see `point(0, "alive", neighbour)` inside a CA, it's wrong — should be `point(1, ...)`.

## When VEX, when VOP, when CHOP

Three different evaluation contexts, three different sweet spots. Naming the right one for each task is half the architect's job.

| Need | Best tool | Why |
|------|----------|-----|
| Sequence of attribute math, conditional logic, addpoint/addprim | **VEX wrangle** | Concise, type-safe, readable; ifs and loops are first-class |
| Compose multiple noises, displace along normal, complex VOP recipes (curlnoise, displacenml, anti-aliased noise) | **VOP** (attribvop / volumevop) | Pre-built nodes for noise handling; visual debugging via render flags; easier to fiddle iteratively |
| Smooth/damp/spring an animation channel over time without DOP | **CHOPnet** with `spring` / `lag` / `filter` | Cheaper than DOP; integrates with parameter channels directly |
| Per-frame rigid-body / cloth / particles | **DOPnet** | Only context with proper time integration |

Concrete examples from 落于ivi 合集:
- 2401_15 (stained glass): VOP — recolor + displace via VOP graph; no per-element conditionals needed
- 2401_16 (curve→noise→particles): VOP for the velocity field (`cross(curlnoise, tangent)`); VEX would be 5 lines but VOP makes the noise tweaks visual
- 2401_30 (spring rebound): CHOP `spring1` damps the body's animated channels; VEX/DOP would be overkill for "make it bounce on stop"
- 2401_22 (rope bridge): VEX everywhere — addpoint/addprim primitive construction needs imperative loops

**Architect rule**: when a VEX wrangle has more than 3 noise functions composited, switch to VOP. When VOP has more than 5 if-branches, switch to VEX. They are dual; pick the one with the lower friction for the job.

## Auxiliary-geometry-as-parameters

`create_tensors` in 落于ivi 2401_22 reads four bbox corner points from input 2 to seed four anchor lines. The bbox geometry is **the parameter source** for the wrangle — cleaner than 12 hard-coded `chf` sliders for x,y,z of each corner.

```c
// Detail wrangle — input 2 is a 4-point bbox proxy
vector pos = point(1, 'P', 0);      // anchor target 0
vector posbbx = point(2, 'P', 0);   // bbox corner 0

int pt1 = addpoint(0, pos);
int pt2 = addpoint(0, set(posbbx.x, posbbx.y, posbbx.z - chf('dist')));
addprim(0, 'polyline', pt2, pt1);
// ... repeat for corners 1,2,3
```

Generalization: when a wrangle needs N positional parameters, ask "could these be points on a small auxiliary geometry instead?" Benefits:
- The auxiliary geo is interactively transformable in viewport (vs. tweaking sliders blind)
- N corner points = 1 input wire, vs. 3N sliders
- The auxiliary geo can itself be procedural (driven by yet another node) → composable

This is how procedural assets *should* expose layout: gizmo-like control geometry, not parameter spam.

## Color-as-group token in solver (verified 4 projects)

Vellum / Bullet / FLIP solvers can't directly modify constraint groups mid-sim — the solver assumes constant group membership. Solution: **use color attribute as a group token**, then convert color → group inside the solver per-frame.

```
Inside sopsolver / multisolver / inside vellumsolver forces:
  dop_geometry → color (current color)
                    ↓
  external object_merge → groupcopy → recolor → output
                    ↓
  Solver reads → group recomputed every frame from color
```

Verified in:
- 0017 cloth pin release (vellum dynamic pin)
- 0540 RBD lesson template (constraint coloring per piece type)
- 0322 vellum biscuit tear (`group basegroup="@Cd.r>0.5"` for pingroup)
- 0497 ground explosion (color carries force region info)

**Why color**: it's a built-in attribute every solver respects without special config. `attribtransfer` of color is fast. Threshold expressions on `@Cd.r>0.5` work in groupcreate.

**Architectural implication**: when you need "dynamic group inside sim", reach for color + groupcreate expression first, before considering custom attribute / sopsolver hack.

## Per-frame active group accumulation via sopsolver (verified 4 projects)

Pattern for "things gradually transition state" — release / activate / dissolve / infect / spread:

```
sopsolver (outer or inner):
  Read Prev_Frame state (which points/prims are already "active")
  Per frame:
    Find new candidates (nearpoints, intersect, threshold, etc)
    Mark them with @active = 1 OR add to "active_grp"
    Output: union of (old active + new active)
```

Verified in:
- 0454 anim→dynamic (BFS via nearpoints + setpointgroup)
- 0488 drying crack (per-island staggered timing)
- 0628 RBD→FLIP (接触侦测 via solver1)
- 0017 cloth pin release (color accumulation)

**Critical property**: monotonic state — once active, never reverts (single-direction transition). For bidirectional you need full FSM.

**Cost**: O(K^t) until saturate (K = neighbors found per iteration). Typically 5-10 frames to cover N=10K mesh.

## Per-element staggered timing formula family (verified 4 projects)

A family of formulas for "ID-driven temporal sequencing" — each element starts/completes animation at different time based on its ID.

Three variants seen:

```c
// Variant A: wavefront blending (0509 AB morph)
float myPt = float(@ptnum + 1) / @numpt;
float shift = fit(@Frame, start_frame, end_frame, 0, 1);
@blend = myPt - 1 + 2 * shift;          // mid value [0,1] = blending zone

// Variant B: staggered grow with offset (0526)
float t = clamp(@Time * speed - offset * @ptnum, 0, 1);
float morph = chramp("ramp", t);

// Variant C: per-island independent window (0488)
float start = rand(@island) * duration_min;
float end   = rand(@island) * duration_max + duration_max * 0.4;
float duration = fit(@Frame, start + frame_offset, end + frame_offset, 0, 1);

// Variant D: linear release by ID (0497, similar)
if (@id < @Frame * release_rate) i@active = 1;
```

All four implement "elements start/complete at different times, ordered by ID/index/spatial position". Mathematically equivalent but different control surfaces.

**Sort SOP determines order direction**: sort by Y → wavefront from low-Y to high-Y. Sort by distance from center → radial expansion.

**When to use each**：
- A (wavefront): smooth two-state morph
- B (staggered grow): single-direction grow with curve
- C (per-island): heterogeneous timing per discrete piece
- D (linear ID release): simple sequential release for RBD activation

## Reference-blend pattern with mask (verified 5 projects)

The most common attribute-driven deformation idiom in 落于ivi corpus:

```c
// Generic form
@P = lerp(@P, point(1, "P", @ptnum), mask);
```

Or with VOP:
```
mix(geometryvopglobal_P, importpoint_P, mask)
```

Variants:
- mask from distance: `fit(length(@P), inner, outer, 0, 1)` (0001)
- mask from chramp on age: `chramp("blend", @nage)` (0180)
- mask from group + condition: `inpointgroup(...) ? 1 : 0` (0454)
- mask via attribute named `@blend`, `@mask_noise`, `@bias`, etc.

**Critical assumption**: input 0 and input 1 must have **matching point order** (`@ptnum` must align). Use `attribtransfer` or `pointdeform` if inputs have different topology.

**Use cases**:
- Visual blend (0001 polar wave)
- Animation morph (0467 vellumrestblend writes to vellum rest pose)
- POP source correction (0180 attribvop fixes gap)
- Anim→sim handoff (0454 deformation reflects to active group)
- Geometry→FLIP source bridge (0628)

This is **the** mask-driven deformation template across the corpus.

## Timeshift to lock reference frame (verified 3 projects)

**Pattern**: `geometry → timeshift (frame=1) → projection/scatter/reference`. Locks downstream operations to a specific reference frame.

Use cases verified:
- **0001 polar wave**: `blast4 → timeshift1 → uvproject1` — UV projected on rest pose so texture doesn't swim during deformation
- **0322 vellum biscuit**: `timeshift_frame1_lock` for `pointdeform` reference — sim reflects to original mesh topology
- **0628 RBD→FLIP**: `timeshift1` on dopimport for stable rest pose reference

**Why frame 1 specifically**: that's the rest pose / pre-deformation state. Some projects use `$F-1` for previous frame ref.

This is **production wisdom** — animated assets without timeshift'd UV / reference shows visible texture swimming or topology drift. Demo authors typically miss this.

## Expression-based group membership (verified 3 projects)

Instead of hand-painting groups, use `groupcreate` with `basegroup = "<expression>"`:

```
groupcreate:
  basegroup = "@Cd.r>0.5"        # color threshold
  basegroup = "@P.y>2.0"          # position threshold
  basegroup = "@class==2"         # class match
  basegroup = "@mask>0"           # mask non-zero
  boundtype = usebsphere          # combined with bbox
```

Verified in 0540, 0322, 0628. Plus 0497 uses `boundtype = usebsphere` (3D sphere bounds for spatial group).

**Why expression**: declarative + auto-updates when upstream attribute changes. Manual paint groups need re-paint when source changes.

## Sopsolver attribtransfer from external null (verified 2 projects)

Cross-subnet bus pattern for sim:

```
Inside sopsolver in dopnet:
  dop_geometry  ← current sim state
  object_merge  ← /obj/.../external_null  (carries new attributes)
  attribtransfer (dop_geometry, object_merge) → output
```

Verified in 0497 ground explosion (transfers @v from "force" null), 0628 RBD→FLIP (transfers attributes for state).

**Why**: lets external SOP processing inject attributes into sim each frame without rebuilding sim. The external null is a "mailbox" the sim polls.

**Architectural significance**: sim is no longer black box — its inputs are continuously updatable from outside. Production patterns where users tweak parameters that need to influence already-running sim use this.

## Fit non-[0,1] mapping to prevent zero-jump (verified 2 projects)

Subtle but important fit pattern:

```c
// ❌ Risky: starts at exactly 0
fit(@age, 0, max_age, 0, 1)

// ✅ Safer: starts at 0.3 (non-zero base)
fit(@age, 0, max_age, 0.3, 1)
```

When the fit output drives `chramp` or `lerp`, starting at exactly 0 causes "zero-state moment" (ramp returns chramp[0] which often is 0 or default → discontinuity).

Starting at 0.3 means even at t=0, output is at 30% of ramp → smooth start.

Verified in 0519 viscosity (`fit(@age, 0, 2, 0.3, 1)`), 0467 vellumrestblend.

Combine with `+ chf("offset")` floor (e.g. `chramp(...) + 0.1`) for additional safety.

## Nested foreach piece (verified 2 projects)

Two-level foreach:
```
foreach_begin1 (piece, by outer connectivity)
  foreach_begin2 (piece, by inner connectivity)
    Per-inner-piece processing
  foreach_end2 (merge, pieces)
foreach_end1 (merge, pieces)
```

Verified in 0488 drying crack (大块→小块), 0322 vellum biscuit (cluster→sub-piece).

**Multiplicative cost**: N_outer × N_inner × body_cost. Innocuous body becomes expensive when both N's grow.

**No cross-piece communication**: inner pieces are processed independently per outer piece. If you need cross-talk, precompute detail attribs before outer foreach.

**Use cases**: hierarchical processing — large fragments containing small fragments, clusters with sub-clusters, regions with sub-regions.

## Incremental refinement showcase layout (corpus signature, NOT production)

**This is落于ivi 's signature pedagogical pattern, not a production architecture.**

Multiple parallel `solver / popnet / subnet` instances in one project, each testing a different parameter / variant:

Verified in 8+ projects: 0017 (7 vellumsolver), 0049 (6 popnet), 0188 (multi findshortestpath), 0277 (4 book subnet), 0510 (multi solver), 0540 (7 rbdbulletsolver), 0519 (4 dopnet), 0013 (3 popnet), 0180 (8 popnet).

**Mental model when reading**: "1 solver + N alternative versions" — only one is the final output, others are educational refinement steps the author kept for clarity.

**Production audit**: replace N parallel solvers with 1 solver + switch SOP, delete alternatives. Or wrap as HDA with version parameter.

**Why falling-on-ivi keeps them**: pedagogical — viewer can see "if I use this version vs that, here's the visual difference". Production rigs don't do this.

When you see N parallel solvers in any 落于ivi project, **don't assume complexity** — assume incremental refinement. Read just one to understand intent.

## Spatial-control-gizmo pattern (transformable boxes as art handles)

Generalization of "auxiliary geometry as parameters" — when artists need to control **where** an effect happens (not just amount), expose **physically draggable proxy geometry** in the viewport, then read its position via `distancefromgeometry` or `xyzdist`.

落于ivi 2401_01 polar water wave is the canonical example:
- `box1` + `transform1/2/3` = 3 separate control gizmos (artist drags in viewport)
- `enumerate → distancefromgeometry1 (input1=transform1) → distancefromgeometry2 (input1=transform2) → distancefromgeometry3 (input1=transform3)` = chained distance field accumulation
- Combined distance signal drives downstream blending mask
- Result: artist drags box → wave appears around that location, real-time

Architectural significance:
1. **Spatial control without UI design** — artist uses Houdini's existing transform handles in 3D viewport, no custom panel needed
2. **Multiple control points are trivially additive** — chain another `distancefromgeometry`, done. No code changes.
3. **The number of controls is a parameter** — replace `transform1/2/3` with a `copytopoints` of N templates, you have N gizmos
4. **Reads as data flow** — distance field IS the control signal, not a hidden ch()

When to use: any effect where "where" is more important than "how much" — wave sources, magnetic poles, attention attractors, gravity wells, brush strokes.

When NOT to use: when the control needs to be a curve (use a `curve` SOP instead), an area (use volume), or a parameter sweep (use channel).

## Connectivity-driven map-reduce (foreach piece pattern)

When you have multiple disconnected geometry components and want to process each independently, the canonical structure is:

```
upstream_geom
  → connectivity                    ← classifies pieces with @class
  → foreach_begin (method=piece)
      ↓
      [body — per-piece processing]
      ↓
  → foreach_end (method=merge, itermethod=pieces)
```

Critical recursive properties of this pattern:

1. **Loop count = number of connected components** — auto-adapts to input topology. Add a piece in upstream → loop runs one more time. **The piece count is NOT a parameter; it's emergent from the input.**

2. **`@ptnum` inside the loop is piece-local** — first point of each piece is `@ptnum=0`. Useful for "mark first point" tricks (like `blend_center_point` in 2401_01). Surprising for new readers — every new piece restarts ptnum at 0.

3. **No cross-piece communication inside the loop** — each piece is processed in isolation. If piece B needs to know about piece A, you must (a) precompute a `detail` attribute before the loop, or (b) collect data after the loop and feed it back.

4. **Cost multiplier is N_pieces × body_cost** — innocuous-looking body operations (revolve with 240 segments, fuse with tight tolerance) get multiplied by piece count. Profile per-piece cost first.

5. **Output topology is union of bodies' outputs** — `method=merge` with `itermethod=pieces` does the union. If body produces N_body points, output has N_pieces × N_body points (assuming no de-dup).

Use cases:
- **Surface of revolution**: per-piece curve → revolve each independently → multi-shell output
- **Per-cluster smoothing**: per-piece mesh → smooth each → preserve cluster boundaries
- **Per-shape voronoi**: per-piece bound → voronoi inside each → independent shatter patterns
- **Per-arm tree generation**: per-piece skeleton → grow leaves → don't cross-pollute arms

This is the Houdini-native equivalent of GPU `kernel<<<N_pieces, ...>>>` — embarrassingly parallel structure.

## Reference-frame UV locking (timeshift + uvproject)

Problem: animated geometry needs static-looking UV. If you `uvproject` per frame, UV slides as the geometry deforms — texture appears to swim across the surface (artifact).

Solution: lock UV to a single reference frame.

```
deformed_geom_per_frame
  → timeshift (frame=1 or static)   ← capture rest pose
  → uvproject                       ← project UV in rest pose
  → wrangle: v@uv = vertex(1, 'uv', @vtxnum)
                                    ← read UV from rest pose, paste onto current frame
```

Architectural significance:
- **Decouples UV from geometry deformation** — texture stays anchored to material, not to current vertex positions
- **Required for any animated character / cloth / wave with textures** — universally applicable production pattern
- **Subtle production trick** — only people who shipped animated assets know to do this; demo authors typically miss it

落于ivi 2401_01 uses this pattern (`blast4 → timeshift1 → uvproject1`). It's the kind of pattern that signals the author has production experience even when the rest of the project is demo-grade.
