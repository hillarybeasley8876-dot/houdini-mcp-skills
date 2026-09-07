# VEX Recipes: Copy-Paste Snippets for Common PCG Problems

Each recipe = problem statement + minimal VEX + when to use + variations.

## R1: Snap to grid

**Problem**: Random points need to align to a grid (so modules can stack).

```c
// point wrangle
@P.x = rint(@P.x / grid_x) * grid_x;
@P.y = rint(@P.y / grid_y) * grid_y;
@P.z = rint(@P.z / grid_z) * grid_z;
```

**MUST follow with** `fuse(tol3d=0.001, snaptype=distancesnap)` to dedupe.

## R2: Filter sparse points (density threshold)

**Problem**: Remove points that don't have enough neighbors (i.e., remove edge/isolated points).

```c
// point wrangle
int handle = pcopen(0, "P", @P, radius, max_pts);
if (pcnumfound(handle) < min_neighbors) {
    removepoint(0, @ptnum);
}
```

**Tuning**: `radius` ≈ 1.05 × grid step; `min_neighbors` = 5 for "interior" detection in 3D grid; lower for "any neighbor" filtering.

## R3: Compute density score (without deleting)

**Problem**: Get density value per point for downstream weighting (don't filter yet).

```c
// point wrangle
int handle = pcopen(0, "P", @P, radius, max_pts);
i@density = pcnumfound(handle);
// optional: f@density_norm = (float)i@density / max_pts;
```

Better than R2 because it preserves data — downstream wrangles can sort/weight by density.

## R4: Probability with condition bonus

**Problem**: "Top floor windows should be more frequent than bottom."

```c
// primitive wrangle
float prob = ch("base_probability");
float bonus = 0;

vector pos = point(0, "P", primpoints(0, @primnum)[0]);
if (pos.y > top_threshold)  bonus += 0.2;        // top floor: +20%
if (@N.z > 0)              bonus += 0.1;          // south-facing: +10%

if (rand(seed + @primnum) > prob + bonus) {
    // didn't pass — leave as-is
} else {
    s@type = "window";
}
```

**The "+= bonus" pattern** is the universal way to combine multiple soft preferences.

## R5: Geometric veto (post-hoc filtering)

**Problem**: After deciding "this is a window", check if the position is actually viable.

```c
// primitive wrangle, AFTER assigning s@type = "window"
vector center = (sum_of_pts) / npts;
vector normal = point(0, "N", primpoints(0, @primnum)[0]);

vector pw, uvw;
int hit = intersect(input_obstacles, center, normal * check_distance, pw, uvw);

if (hit != -1) {
    s@type = "wall";  // veto — revert
}
```

**Pattern**: distribute liberally → veto via geometry check. Always cleaner than "compute valid positions upfront".

## R6: Pick one element from candidates (detail wrangle)

**Problem**: Choose exactly one prim/point to mark, randomly weighted.

```c
// detail wrangle
int candidates[];
for (int i = 0; i < nprimitives(0); i++) {
    if (prim(0, "is_candidate", i) == 1) {
        append(candidates, i);
    }
}
if (len(candidates) == 0) return;

float seed = ch("seed");
int picked = candidates[(int)rint(fit(rand(seed), 0, 1, 0, len(candidates)-1))];
setprimattrib(0, "selected", picked, 1, "set");
```

Used for "pick the entrance door", "pick the chimney location", etc.

## R7: Module attribute init

**Problem**: At a candidate point, set the module name and variation to load.

```c
// point wrangle
float seed = ch("seed");
int max_var = chi("max_variation");

s@name = s@type;                                           // "window", "door", etc.
s@variation = sprintf("0%d", (int)rint(fit(rand(seed + @ptnum), 0, 1, 1, max_var)));
v@scale = {1, 1, 1};
v@up = {0, 1, 0};
// @N is already set from the source prim
```

Downstream `file` SOP loads `modules/<cat>/<cat>_<s@name>_<s@variation>.obj`.

## R8: Variable-length tiling (no seams)

**Problem**: Place N modules along a polyline of unknown length. Modules can't stretch arbitrarily.

```c
// detail wrangle
vector p1 = point(0, "P", 0);
vector p2 = point(0, "P", npoints(0) - 1);
float dist = distance(p1, p2);
float module_size = ch("module_size");

int n = (int)rint(dist / module_size);
if (n < 1) n = 1;
float scale_z = (dist / n) / module_size;

vector dir = normalize(p2 - p1);
for (int x = 0; x < n; x++) {
    vector pos = p1 + dir * scale_z * module_size * (x + 0.5);
    int pt = addpoint(0, pos);
    setpointattrib(0, "N", pt, dir);
    setpointattrib(0, "up", pt, {0, 1, 0});
    setpointattrib(0, "scale", pt, set(1, 1, scale_z));
    setpointattrib(0, "name", pt, "rail_segment");
}
```

`scale_z` is typically 0.95-1.05 (not visible). Used for railings, roof tiles, stair steps.

## R9: Compute orientation angle (atan2 way, not acos)

**Problem**: Module needs to face along @N. Compute Y-axis rotation in degrees.

```c
// point wrangle
@angle = degrees(atan2(@N.x, @N.z));   // [-180, 180]
// for [0, 360]:
if (@angle < 0) @angle += 360;
```

**Don't use** `acos(dot(@N, ref))` + sign correction — atan2 is unambiguous.

## R10: Apply orientation + position from attributes

**Problem**: Place a module rotated by `@angle` and translated to a target.

```c
// point wrangle
matrix3 rot = ident();
rotate(rot, radians(@angle), {0, 1, 0});
@P *= rot;

vector translation = point(1, "P", 0);  // target position from input #1
@P += translation;
```

Often used inside a copytopoints alternative when full matrix control is needed.

## R11: Find topology neighbours (modern API)

```c
// primitive wrangle
int neighs[] = polyneighbours(0, @primnum);  // direct API in 17.5+

// point wrangle
int point_neighs[] = neighbours(0, @ptnum);
```

Pre-17.5 fallback: see R11b below.

## R11b: Find topology neighbours (manual, pre-17.5)

```c
// primitive wrangle
int pts[] = primpoints(0, @primnum);
int neighs[];
foreach (int p; pts) append(neighs, pointprims(0, p));

int max_nm = max(neighs);
int neigh_prims[];
for (int nm = 0; nm <= max_nm; nm++) {
    if (nm == @primnum) continue;
    int found = 0;
    foreach (int n; neighs) if (n == nm) found++;
    if (found > 0 && found % 2 == 0) {  // shared edge = even count
        append(neigh_prims, nm);
    }
}
```

Parity check on shared vertices. NEVER use distance-based neighbor for topology.

## R12: Read attributes from neighbours (spatial JOIN)

```c
// point wrangle
int handle = pcopen(input_neighbours, "P", @P, radius, max_pts);
while (pciterate(handle)) {
    int neigh_id;
    vector neigh_dir;
    pcimport(handle, "id", neigh_id);
    pcimport(handle, "dir", neigh_dir);
    
    // use neigh_id, neigh_dir to make decisions about @P
}
```

10x faster than `nearpoints + point()` reverse lookup. Use whenever you need neighbor attributes, not just positions.

## R13: Single-step iterator pattern (for-loop block helper)

```c
// detail wrangle, runs inside feedback for-loop block
int found = 0;
for (int i = 0; i < nprimitives(0); i++) {
    if (some_condition(i)) {
        // mark / modify
        setprimattrib(0, "marked", i, 1, "set");
        found = 1;
        break;  // ← critical: only one per iteration
    }
}
if (found == 0) i@stop = 1;  // signal block_end to terminate
```

For "find one, process, repeat" patterns. Used for graph contraction, pair finding, etc.

## R14: Topo-sort longest path (height/level assignment)

```c
// detail wrangle inside feedback for-loop, with chi("primnum") = current prim
int pr = chi("primnum");
int incoming[] = prim(0, "incoming", pr);
int my_h = prim(0, "height", pr);

int in_heights[];
foreach (int in_p; incoming) append(in_heights, prim(0, "height", in_p));
if (len(in_heights) > 0 && max(in_heights) >= my_h) {
    my_h = max(in_heights) + 1;
}
setprimattrib(0, "height", pr, my_h, "set");

// also push outgoing
int outgoing[] = prim(0, "outcoming", pr);
foreach (int out_p; outgoing) {
    if (prim(0, "height", out_p) <= my_h) {
        setprimattrib(0, "height", out_p, my_h + 1, "set");
    }
}
```

Used for layered structures (roof tiers, dependency levels).

## R15: Multi-ray decision tree (geometric branching)

```c
// point wrangle
vector pw1, uvw1, pw2, uvw2, pw3, uvw3;
int inter1 = intersect(input1, @P, @N * 10, pw1, uvw1);
int inter2 = intersect(input1, @P + @N * 0.01, {0,-10,0}, pw2, uvw2);
int inter3 = intersect(input2, @P, @N * 10, pw3, uvw3);

if (inter1 != -1) {
    // direction has neighbor — extend toward it
    @P = pw1;
    i@_p_extended = 1;
}
else if (inter2 != -1) {
    // neighbor below — drop
    @P.y = pw2.y;
}
else {
    // open space — create end cap or sidewall
    int side_pr = addprim(0, "poly");
    addvertex(0, side_pr, @ptnum);
    foreach (int n; neighbours(0, @ptnum)) {
        if (point(0, "P", n).y != @P.y) addvertex(0, side_pr, n);
    }
}
```

For "make this geometry adapt to its environment" cases. Used for roof joining, wall ending, tower capping.

## R16: Quantized seed key (for deterministic noise)

**Problem**: `rand(seed + @P.x)` gives different values for `@P.x = 1.0` and `@P.x = 1.00000001`. You need consistency for points "logically on the same line/plane".

```c
float key_y = rint(@P.y * 100) / 100;        // 0.01 precision
float random_offset = fit(rand(seed + key_y), 0, 1, -0.04, 0.04);
@P.y += random_offset;
```

**Three flavors**:
- `rint(x*10)/10` — for relbbox boundary tests (0.1 precision)
- `rint(x*100)/100` — for position-as-seed-key (0.01 precision)
- `abs(rint(v))` — for "is this axis-aligned?" tests

## R17: Flip face winding (change normal direction)

```c
// primitive wrangle
int pts[] = primpoints(0, @primnum);
removeprim(0, @primnum, 0);  // 0 = keep points, just remove the prim
int new_pr = addprim(0, "poly");
for (int x = len(pts) - 1; x >= 0; x--) {
    addvertex(0, new_pr, pts[x]);
}
```

The ONLY reliable way to flip a normal. Modifying `@N` directly does NOT flip winding.

## R18: Procedural UV (no tile repeats)

**Problem**: Each prim should pull a unique random region from one big texture.

```c
// point wrangle in primitive context
vector uvspace = chv("uvspace");           // size of the source texture in world units
float seed = ch("seed") + ch("iteration");

vector bbx_min, bbx_max;
getbbox(0, bbx_min, bbx_max);
float ws_h = bbx_max.y - bbx_min.y;
float ws_w = bbx_max.x - bbx_min.x;

float uvs_h = ws_h / uvspace.y;
float uvs_w = ws_w / uvspace.x;
float free_h = 1 - uvs_h;
float free_w = 1 - uvs_w;

float rand_u = fit(rand(seed),     0, 1, 0, free_w);
float rand_v = fit(rand(seed + 7), 0, 1, 0, free_h);

vector rel = relbbox(0, @P);
vector2 uv = set(rel.x * uvs_w + rand_u, rel.y * uvs_h + rand_v);

int vtx = pointvertex(0, @ptnum);
setvertexattrib(0, "uv", vtx, -1, uv, "set");
```

The crown-jewel UV pattern. Each prim gets a randomly-placed crop from one texture — eliminates tiling artifacts.

## R19: Cleanup protocol attributes (subnet exit hygiene)

```c
// detail wrangle at subnet OUT
removeprimattrib(0, "_p_stop");
removeprimattrib(0, "_p_keep");
removeprimattrib(0, "_p_raypoint");
// ... or use attribdelete SOP with pattern "_p_*"
```

Adopt convention: protocol attributes (inter-wrangle messages) prefixed with `_p_`. Cleanup at subnet boundary.

## R20: Centroid + normal of a primitive

```c
// primitive wrangle helper
int pts[] = primpoints(0, @primnum);
vector center = {0,0,0};
foreach (int p; pts) center += point(0, "P", p);
center /= len(pts);

vector normal = point(0, "N", pts[0]);  // assume normal is on points
```

Used so often it's worth memorizing. Center for placement, normal for orientation.

## R21: Deformation-to-velocity bridge (two-stage solver)

**Problem**: A solver A (e.g. ripplesolver / cloth) deforms geometry; you want solver B (RBD / particles) to react to that deformation as initial velocity, not at every frame, and only after a trigger.

```c
// Bridge wrangle. Input 0 = current deformed geo, Input 1 = rest geo.
vector shockwave = point(1, "P", @ptnum) - @P;   // delta from rest
@v   = @N * length(shockwave) * ch("velocity_gain");
@v  *= @Frame > chi("trigger_frame");           // gate single-shot energy

// optional: cull weak motion before next solver
if (length(@v) < ch("min_speed")) removepoint(0, @ptnum);
@v *= 1 + rand(@ptnum + 6223) * ch("jitter");   // randomise survivors
```

The frame gate is the trapdoor — without it, you double-inject energy every frame.

## R22: Edge-walked distance + sweep diameter

**Problem**: A branching polyline (vine, root, vein) needs varying tube diameter — fat at root, thin at tip.

```
path geometry  →  edgetransport  (cost = "primintrinsic:measuredperimeter" or 1)
              →  attribremap     (ramp:  dist→pscale)
              →  resample        (subdivide)
              →  sweep           (uses pscale as radius)
```

VEX is minimal — `attribwrangle1: @pscale = @curveu;` or `@P.y = @h;`. The intelligence is in the node choice: edgetransport spreads attribute *along* the graph, not through space.

When you need: trunk-to-tip taper, sap-flow time map, lightning fade, anything with "distance from a designated root."

## R23: Conditional point synthesis at extrema

**Problem**: Add a boundary point/prim only at the start and end of a polyline (not interior).

```c
// point wrangle — fires only on first and last point
if (@ptnum == 0) {
    vector pos = @P - chf('extend_dist') * v@tangentu;
    int p2 = addpoint(0, pos);
    addprim(0, 'polyline', p2, @ptnum);
    setpointattrib(0, 'name', p2, '', 'set');           // anchor name
    setpointattrib(0, 'name', @ptnum, 'piece_0', 'set');
}
if (@ptnum == @numpt - 1) {
    vector pos = @P + chf('extend_dist') * v@tangentu;
    int p2 = addpoint(0, pos);
    addprim(0, 'polyline', @ptnum, p2);
    setpointattrib(0, 'name', p2, '', 'set');
    setpointattrib(0, 'name', @ptnum, sprintf('piece_%d', @numpt-1), 'set');
}
```

The named "" anchor + "piece_N" pattern is **constraint-network preparation** — null-name anchors get treated as world-fixed by Bullet/Vellum, named pieces are RBD bodies. Used in 2401_22 rope bridge.

## R24: Camera-locked anchor via `optransform()` inverse

**Problem**: A floating UI/marker geometry should *appear* fixed in screen space even as the camera moves.

```c
// detail wrangle — input 0 = the marker geo
matrix cam = optransform(chs("cam_path"));   // current camera world matrix
@P *= cam;                                   // bring point into camera-relative frame
```

Anti-pattern: parenting in OBJ context (loses procedural traceability). This pattern keeps everything in SOPs.

Inverse use case: "static camera, animated object" → multiply by `invert(optransform(cam))`.

## R25: Quaternion stacking (additive spin on top of base orientation)

**Problem**: Object should face along `@N` AND spin around its own axis AND wobble.

```c
// Step 1: base orient from N + up
matrix3 m = maketransform(@N, @up);
vector4 base = quaternion(m);

// Step 2: extra rotations as quats
vector4 spin   = quaternion(ch('spin_speed') * @Time, @N);
vector4 wobble = quaternion(set(ch('wob_x'), ch('wob_y'), ch('wob_z')));  // axis-scaled trick

// Step 3: stack via quaternion multiplication (right-to-left = innermost first)
@orient = qmultiply(qmultiply(base, spin), wobble);
```

The `quaternion(vector axis * angle)` shorthand: passing a non-normalised vector treats its length as the rotation angle. Saves a separate `angle, axis` argument.

## R26: Surface-tangent noise projection (noise that flows across, not into, a surface)

**Problem**: A noise displacement should move points *along* the surface, not push them through it.

```c
// point wrangle on a meshed surface with @N defined
vector raw_noise = curlnoise(@P * ch('freq') + @Time * ch('speed'));

// Project away the normal component → keep only tangent component
vector tangent_noise = raw_noise - dot(raw_noise, @N) * @N;

// Apply
@P += tangent_noise * ch('amp');

// To carry colour along the displacement, look up the source colour at the moved position:
@Cd = prim(0, "Cd", xyzdist(0, @P));
```

Behind: `dot(noise, N)` extracts the perpendicular component, multiplied by `N` gives the perpendicular vector; subtract it → only tangent left. Used for water flow, fur grooming, surface paint.

## R27: Direct read from input N via `@opinput<N>_<attr>`

**Problem**: Reading attributes from input 1+ is verbose with `point(1, "...", @ptnum)`.

```c
// Verbose
vector other_P  = point(1, "P", @ptnum);
float other_age = point(1, "age", @ptnum);

// Concise — implicit @ptnum lookup, type inferred for built-in attrs
vector other_P = @opinput1_P;
float other_age = @opinput1_age;     // user attribs default to FLOAT — type if needed:
v@other_v = @opinput1_v;
```

Built-in attrs (P/N/Cd/v/orient/id/name) get the right type automatically; user-defined attribs default to float — declare prefix (`v@`, `i@`, `s@`) when needed. Saves ~5 chars per read; use for short bridge wrangles. Don't use for one-off reads where the verbose form is clearer.

## R28: `@TimeInc` for accumulating solvers (not `@Time%1`)

**Problem**: Inside a `sopsolver`, you want to accumulate rotation angle across frames.

```c
// WRONG — @Time%1 wraps every second, snaps state back to 0
angle = $PI/2 * @Time%1;

// RIGHT — @TimeInc = 1/24s per frame; accumulates monotonically
angle = $PI/2 * @TimeInc;
m = ident(); rotate(m, angle, @up);
@P *= m;
```

Rule: any per-frame delta inside a solver = `@TimeInc`. `@Time` only for sample-the-clock effects.

## R29: Iterative path connection (solver-driven growth)

**Problem**: Grow a polyline outward from a seed point, picking the next neighbour based on a noise-aligned direction.

```c
// Inside a sopsolver — runs each frame
int near[] = nearpoints(0, @P, ch("search_r"));
foreach (int n; near) {
    if (n == @ptnum || point(0, "active", n)) continue;

    vector to_n = point(0, "P", n) - @P;
    vector noise_dir = point(0, "noise_N", @ptnum);

    if (dot(normalize(to_n), noise_dir) >= 0) {  // within 90° of growth direction
        addprim(0, 'polyline', @ptnum, n);
        setpointattrib(0, "active", n, 1);
        setpointattrib(0, "age",    n, @Frame);
        break;                                    // one connection per frame per active point
    }
}
```

Pair with `chramp("color", @age / max_age)` for fade-in trail. Master VEX 121-128 builds 4 variations on this — the search radius, noise field, and "active" propagation rule are the 3 knobs.

## R30: Solver tolerance drift correction

**Problem**: After 1000 solver ticks, accumulated float error makes positions drift off-grid visibly.

```c
// Inside the solver, every cycle
if (abs(sum(@P * axis) - target_slice) <= 0.001) {
    @P = round_to_unit(@P);     // re-snap to nominal grid
}
```

The check `abs(... - target) <= ε` lets solver-state float freely most of the time but pins it back when within ε of the canonical position. Without this, Rubik's-cube-style discrete-motion solvers visibly desync after a minute.

## R31: detail-intrinsic group manipulation (random group cull)

**Problem**: Read the project's primitive groups dynamically, randomly select one each frame, and delete its members.

```c
// detail wrangle, runs each frame
string groups[] = detailintrinsic(0, "primitivegroups");
int idx = int(rand(@Frame) * len(groups));
string victim = groups[idx];
int prims[] = expandprimgroup(0, victim);
foreach (int pr; prims) removeprim(0, pr, 1);   // 1 = remove orphan points
```

`detailintrinsic` reads the *current* group list — works even after upstream changes have added/removed groups. Useful for randomly-revealing assemblies, click-to-shatter UI, etc.

## R32: bbox-corner anchor scaffold

**Problem**: Build N anchor lines from N hand-placed points down to N bbox corners.

```c
// detail wrangle — input 1 = hand-placed anchors, input 2 = bbox-corner geo
for (int i = 0; i < 4; i++) {
    vector top = point(1, 'P', i);
    vector bot = point(2, 'P', i);

    // Optional: inset/offset the bbox corner before connecting
    bot.z += chf('z_offset') * ((i == 0 || i == 1) ? -1 : 1);

    int pt_top = addpoint(0, top);
    int pt_bot = addpoint(0, bot);
    addprim(0, 'polyline', pt_bot, pt_top);
}
```

The `for i in 0..3` loop unrolls 4 anchor lines; per-corner offset modulated by `(i==0||i==1) ? -1 : 1` gives front/back symmetry. Used in 2401_22 rope-bridge tensor cables.

## R33: Sliding-puzzle swap (solver pattern)

**Problem**: A grid where one tile is missing; each beat, swap the missing tile with a random neighbour, sliding it visually.

```c
// detail wrangle inside a sopsolver
int missing  = chi("missing_idx");
int W        = chi("grid_w");
int neighbours[] = array(missing-1, missing+1, missing-W, missing+W);
// Filter: keep only valid (in-grid) neighbours
int valid[];
foreach (int n; neighbours)
    if (n >= 0 && n < npoints(0) && (n != missing-1 || missing % W != 0))
        append(valid, n);

float t   = @Time * ch("rate");
float frac = t - floor(t);
if (frac < 0.05) {
    // Snap-on-beat: pick new target
    int pick = valid[int(rand(@Frame) * len(valid))];
    setdetailattrib(0, "swap_target", pick, "set");
    setdetailattrib(0, "missing_idx", pick, "set");        // missing tile moves
} else {
    // Mid-beat: blend missing tile toward target
    int target = detail(0, "swap_target");
    vector tp = point(0, "P", target);
    vector mp = point(0, "P", missing);
    setpointattrib(0, "P", missing, lerp(mp, tp, frac), "set");
}
```

The mod-time + snap pattern ensures the puzzle "clicks" at integer beats but slides smoothly between. Generalizes to any "discrete state at integer beats, interpolated between."

## R34: Vertex-prim index for reliable curve endpoint detection

**Problem**: Mark the start point of every polyline. Using `uv.x < 0.1` is unreliable.

```c
// point wrangle on resampled curves
int prims[] = pointprims(0, @ptnum);
int prim_id = prims[0];
int verts[] = primvertices(0, prim_id);

// vertexprimindex returns the per-prim vertex index (0 = start, last = end)
int vtx = pointvertex(0, @ptnum);
int vidx = vertexprimindex(0, vtx);

if (vidx == 0)               setpointgroup(0, "start", @ptnum, 1);
if (vidx == len(verts) - 1)  setpointgroup(0, "end",   @ptnum, 1);
```

Use this whenever you need start/end of a curve, especially after `resample`/`fuse` may have shifted UVs. The vertex-prim index is the topology-truth answer.

## R35: chramp + per-point age/distance for color or scale

**Problem**: A common pattern: map an attribute (age, distance, height) into a color OR scale via an artist-authored ramp.

```c
// point wrangle
float t = fit(@age, 0, ch("max_age"), 0, 1);
@Cd      = chramp("color_ramp", t);
@pscale  = chramp("scale_ramp", t) * ch("base_scale");
```

`chramp` UI-edits the curve right in the parameter panel — much faster iteration than fit + if-else cascades. Use for trails, fade-ins, growth animations, vegetation health gradients.

The 落于ivi master collection uses chramp 30+ times — it's the universal "artist control over a single mapping" pattern.

## R36: Uniform-direction sampling (the right way to randomize a vector)

**Problem**: `rand()` returns a vector biased toward the +x +y +z octant — visibly clumpy on instanced geometry.

```c
// point wrangle
v@N    = sample_direction_uniform(rand(@ptnum));        // unit sphere uniform
v@up   = sample_sphere_uniform(rand(@ptnum + 7));       // ditto
v@disk = sample_circle_edge_uniform(rand(@ptnum + 13)); // unit circle edge
```

These 3 functions are the only correct way to get uniformly-random orientations. `rand()` returns ∈ [0,1]^3 — cube biased, NOT spherical. Master VEX 135 spells this out.

When you instance things and they look "more aligned with axes than they should": you used `rand()` instead of these. Switch.

## R37: Dihedral for "rotate Z to N" instancing

**Problem**: A flat disk / decal / patch needs to lay flat on a surface where the normal is `@N` (not necessarily `{0,1,0}`).

```c
// point wrangle — built-in copytopoints assumes Z-aligned source
matrix3 m = dihedral({0,0,1}, @N);   // matrix that rotates {0,0,1} to @N
@orient = quaternion(m);
```

`dihedral(a, b)` returns the **shortest-arc** rotation matrix from a to b. The standard recipe to align Z-aligned source geometry to surface normals — Houdini's copy/instance defaults assume Z is forward.

For "Z to N + spin around N":
```c
matrix3 m = dihedral({0,0,1}, @N);
rotate(m, @Time * ch('spin'), @N);
@orient = quaternion(m);
```

Master VEX 128 is the canonical 2-line form.

## R38: HSV cycle — distinct color per group/index

**Problem**: N groups (or N pieces) need clearly-distinguishable colors, not random-and-occasionally-similar.

```c
// primitive wrangle
int n = chi('numgroups');
i@switch = @primnum % n;
@Cd = hsvtorgb(float(@switch) / n, 1, 1);
```

HSV-cycle gives even hue spacing — 8 groups = 8 colors 45° apart, all clearly distinct. Random Cd often produces two near-identical reds.

Variant — color by group name (stable across renders):
```c
foreach (string g; detailintrinsic(0, 'primitivegroups')) {
    if (inprimgroup(0, g, @primnum) == 1) {
        @Cd = rand(random_shash(g));      // random_shash = stable string→seed
    }
}
```

`random_shash(string)` is the only correct way to seed `rand()` from a string identifier.

## R39: Polar / cylindrical coords + twirl

**Problem**: Apply rotational deformation centered on origin, optionally with twirl-by-distance for spiral effects.

```c
// point wrangle
float angle = atan(@P.x, @P.y);
float r     = length(set(@P.x, @P.y));   // 2D radius — exclude z

float amount = radians(ch('amount'));
float twirl  = r * ch('twirl');           // adds angle proportional to radius

@P.x = sin(amount + angle + twirl) * r;
@P.y = cos(amount + angle + twirl) * r;
```

The `r * twirl` term is the key — without it, plain rotation; with it, **archimedean spiral** (used in galaxy / hurricane / cinnamon-roll deformations).

Use `length(set(@P.x, @P.y))` not `length(@P)` — exclude the axis you're rotating around.

## R40: UV-tile micro-pattern (procedural texture, no raster)

**Problem**: A surface needs a tiling micro-pattern (dots, hex, stripes) authored in VEX, with per-tile randomization. No image texture wanted.

```c
// point wrangle — requires @uv on the geometry
int   tiles = chi('tiles');
float rand  = ch('rand');
float start = ch('dotradius_start');
float end   = ch('dotradius_end');

vector offset = rand(floor(@uv * tiles)) * {1,1,0};   // per-tile random
offset = fit(offset, 0, 1, -rand, rand);
offset.z = 0;

@Cd = smooth(start, end, length( frac(@uv * tiles) * {2,2,0} - {1,1,0} + offset ));
```

Pipeline: `floor(uv*tiles)` = per-tile id (used as rand seed), `frac(uv*tiles)*{2,2,0}-{1,1,0}` = tile-local coords centered on 0, `length()` = radial gradient, `smooth(start, end, ...)` = soft circle, `+ offset` = per-tile jitter.

Variants:
- Replace `length()` with `max(abs())` for square pattern.
- Replace `smooth()` with `chramp("dot", ...)` for artist-controlled falloff.
- Multiply by `rand(floor(uv*tiles))` for per-tile color.

This is the **frac+floor+rand+fit** pipeline — the universal procedural-texture-without-texture template. Master VEX 140-158 walks through 19 progressive refinements of it.

## R41: Edge-axis rotation with pivot (rotate about an arbitrary edge)

**Problem**: Hinge a flap of geometry around a specific edge (door, window shutter, fan blade).

```c
// primitive or point wrangle
int pts[] = primpoints(0, @primnum);
vector p0 = point(0, 'P', pts[0]);
vector p1 = point(0, 'P', pts[1]);

vector axis  = normalize(p0 - p1);          // hinge direction
vector pivot = (p0 + p1) / 2;                // pivot at midpoint of edge
float angle  = radians(ch('angle'));

matrix3 rot = ident();
rotate(rot, angle, axis);

// Move to origin, rotate, move back — the only correct order
@P -= pivot;
@P *= rot;
@P += pivot;
```

The translate-rotate-translate sandwich is mandatory because matrix multiplication rotates around origin; we want to rotate around the edge midpoint. Master VEX 49-62 has the full progression including the `instance(pivot, N, scale, postrot, orient, pivot)` form for full transform.

Used for: doors swinging on hinges, fingers articulating, fan blades, butterfly wings.

## R42: xyzdist + primuv — "snap to surface and inherit attribute"

**Problem**: For each free-floating point, find the closest surface point, snap there, and copy the surface's color/uv/normal.

```c
// point wrangle — input 1 is the surface
int prim;
vector uv;
@d = xyzdist(1, @P, prim, uv);          // get nearest prim+uv on input 1

@P = primuv(1, 'P', prim, uv);          // snap to surface
@Cd = primuv(1, 'Cd', prim, uv);
@N  = primuv(1, 'N',  prim, uv);
i@source_prim = prim;                   // optional: remember source for later
```

This is **point→surface attribute transfer at one shot**. Faster and more controllable than `attribtransfer` SOP because you choose what to copy.

Variant: keep the original `@P`, only inherit attributes:
```c
int prim; vector uv;
xyzdist(1, @P, prim, uv);
@Cd = primuv(1, 'Cd', prim, uv);
```

Used everywhere: scattered points → take surface color, sim points → carry rest-pose color, particle paint → look up base color from a static reference.

## R43: Look-at orient (face the origin, or any target)

**Problem**: A grid of objects should all face a target point.

```c
// point wrangle
vector to_target = chv('target') - @P;
@orient = quaternion(maketransform(normalize(to_target), {0,1,0}));
```

To face the origin: `to_target = -@P`. Used in master VEX `set_orient`. If you also want pitch/yaw/roll on top, stack quaternions per R25.

## R44: Spiral along curve via tangent-axis quaternion

**Problem**: Distribute points along a curve, then have each point spiral around the curve's local tangent direction.

```c
// point wrangle on a resampled curve — needs v@tangentu (or v@N along curve)
float speed  = @Time * ch('speed');
float angle  = speed + @curveu * ch('spirals');   // spirals scales with curve U

vector4 q = quaternion(v@tangentu * angle);       // axis-scaled quaternion
@N = qrotate(q, @N);                              // rotate the existing N around tangent
```

The `quaternion(axis * angle)` shorthand encodes both axis and angle in one vector. `@curveu * spirals` makes denser turns at the curve's end if spirals > 1.

Pair with a `polywire` or `sweep` to render the spiraling normal as visible geometry. Master `spiral_vex` is the canonical form.

## R45: `setprimintrinsic('transform', ...)` for packed-prim scaling

**Problem**: A packed primitive (single point representing a sub-network of geometry) won't respond to `@P *= scale_matrix` because the geometry is hidden inside.

```c
// point wrangle on packed prims (one point per prim)
matrix3 m = ident();
scale(m, chv('scale'));
setprimintrinsic(0, 'transform', @ptnum, m);
```

Packed prims have a hidden internal transform matrix (`primintrinsic`) that controls how their unpacked geometry is rendered. Modifying `@P` only moves the wrapper point; the packed geometry rotates/scales around its own internal pivot via this intrinsic.

Same pattern for rotation: `rotate(m, angle, axis)` then `setprimintrinsic`. Used for instancing, RBD pieces, anything "packed".

## R46: Lifetime decrement + variable-life cull

**Problem**: Particles or instanced points should live for N frames, then disappear. With per-point variation.

```c
// Spawn wrangle (point wrangle, runs once on spawn)
int life    = chi("life");
int lifeVar = chi("lifeVar");
@lifetime = life + int(rint(fit01(rand(@P*342), -lifeVar, lifeVar)));
@creationFrame = @Frame;

// Tick wrangle (inside solver, runs each frame)
if (@lifetime == 0) removepoint(0, @ptnum);
@lifetime--;
```

`fit01(rand(seed), -V, V)` symmetric jitter around mean. The `int(rint(...))` cast ensures whole-frame counts.

`@creationFrame` enables age-based effects:
```c
@P.y += chf("liftRate") * (@Frame - @creationFrame);   // rise over time
@Cd  = chramp("fade", (@Frame - @creationFrame) / @lifetime);
```

Used for sparks, pollen, lightning arcs, anything with a finite life.

## R47: `findattribval` anti-join (dedupe by id across inputs)

**Problem**: Two point sets share an `@id` attribute. Keep only points whose `@id` is NOT present in the other input.

```c
// point wrangle on input 0 — input 1 is the "exclude" set
if (findattribval(1, "point", "id", @id, 0) != -1) {
    removepoint(0, @ptnum);
}
```

`findattribval(input, class, attrname, value, start)` returns the first index where the attribute equals the value, or -1 if absent. The `start=0` is the search starting index.

Use cases:
- "remove already-spawned points" (dedupe across solver iterations)
- "keep only points without a matching twin" (set difference)
- "where does this id live in the other geo?" (lookup)

This is **set-membership test in O(N)**. For large N, prefer building an attribute promotion + `findattribval`.

## R48: Ray-cast spawn (intersect → addpoint at hit, kill original)

**Problem**: Each source point should fire a ray. Where the ray hits, spawn a new point (carrying source attribs); then delete the original.

```c
// point wrangle. Input 1 = collision geometry.
vector hit;
float u, v;

if (intersect(1, @P, @N * chf("range"), hit, u, v) != -1) {
    int newPt = addpoint(0, hit);
    setpointattrib(0, "id",            newPt, @id,    "set");
    setpointattrib(0, "lifetime",      newPt, @lifetime, "set");
    setpointattrib(0, "N",             newPt, -@N,    "set");   // flip — ricochet
    setpointattrib(0, "creationFrame", newPt, @Frame, "set");
}

removepoint(0, @ptnum);
```

Flipping `N` to `-N` makes the spawned point "bounce back" — useful for chained ray hops (lightning, fracture propagation, sound bouncing).

If you want to keep the original point too, drop the final `removepoint`. But typically you spawn-then-kill so the ray-front advances.

## R49: Mutual-handshake cell migration (cellular automaton with safe swaps)

**Problem**: A grid where some cells are occupied and some empty. Each tick, occupied cells want to migrate to a random adjacent empty cell — but two cells must not target the same destination, and a cell shouldn't migrate without consent.

```c
// 1) Occupied → pick random empty neighbour (point wrangle, group='occupied')
int avail[];
foreach (int n; neighbours(0, @ptnum)) {
    if (!inpointgroup(0, "occupied", n) && i@block == 0) append(avail, n);
}
if (len(avail)) i@target = avail[int(rand(@ptnum * @id, detail(-1, "iteration")) * len(avail))];

// 2) Empty → pick random occupied neighbour (point wrangle, group='!occupied')
int avail[];
foreach (int n; neighbours(0, @ptnum)) {
    if (inpointgroup(0, "occupied", n) && point(0, "block", n) == 0) append(avail, n);
}
if (len(avail)) i@target = avail[int(rand(@ptnum, detail(-1, "iteration")) * len(avail))];

// 3) Handshake check (point wrangle on occupied, inputs: 0=self, 1=self, 2=self)
int desired_cell = point(1, "target", @ptnum);
if (desired_cell == -1) return;
int desired_pt   = point(2, "target", desired_cell);
if (@ptnum == desired_pt) {
    // Both sides agree — execute swap
    setpointgroup(0, "occupied", desired_cell, 1);
    setpointgroup(0, "occupied", @ptnum,       0);
    setpointattrib(0, "id", desired_cell, @id);
    @id = -1;
}

// 4) Cooldown to prevent flip-flopping (point wrangle, runs after swap)
if (i@prev_id != @id) { i@swap_iteration = detail(-1, "iteration"); i@block = 1; }
if (detail(-1, "iteration") - i@swap_iteration >= chi("delay")) i@block = 0;
i@prev_id = @id;
```

The handshake is the key: A picks B, B picks A, only then swap. Otherwise A might overwrite B's data while B is being overwritten by C.

The cooldown prevents the same cell from migrating twice in N iterations (would make patterns flicker).

This is **stable-marriage / Gale-Shapley per frame**. Used for crystal growth, traffic simulation, occupancy dynamics. Source: 落于ivi 2403_14.

## R50: Multiplicative mask stacking

**Problem**: An effect should fire only where multiple soft conditions are simultaneously satisfied. Each condition has a continuous strength.

```c
// point wrangle
float mask_noise  = f@mask_noise - f@mask_noise_end;       // ramp difference
float mask_fabric = fit(f@mask_fabric, 0.5, 1, 1, 0);       // INVERTED fit
float mask_dist   = chramp("falloff", fit(length(@P), 6, 10, 0, 1));
float mask_angle  = clamp(dot(@N, {0,1,0}), 0, 1);

float final = mask_noise * mask_fabric * mask_dist * mask_angle;
@P.y += final * ch("amplitude");
```

Multiplicative because: any single mask = 0 must zero the result. (Additive would let one strong mask overpower the rest.)

Three useful sub-patterns:
- `chramp(name, value)` for artist-shaped one-knob masks
- `fit(x, a, b, 1, 0)` (inverted) for "high values fade"
- `clamp(dot(N, target), 0, 1)` for facing-direction masks

Source: 落于ivi 2401_01 polar water wave.

## R51: Polar / cylindrical angle to UV (radial wrap)

**Problem**: Need a 0..1 attribute around the Y axis (so that a ramp drives an effect rotating around the origin).

```c
// point wrangle
float angle = atan(@P.z, @P.x) / $PI;       // [-1, 1]
angle       = fit(angle, -1, 1, 0, 1);      // [0, 1]
float t     = (angle + ch("rotate") * @Time) % 1;   // time-rotated wrap
@Cd         = chramp("ring", t);
```

`atan(z, x)` not `atan2(x, y)` — Houdini's `atan(y, x)` returns [-π, π]; divide by π for [-1, 1].

For cylindrical: also include `@P.y`:
```c
float u_ring  = (atan(@P.z, @P.x) / $PI + 1) / 2;
float v_axis  = relbbox(0, @P).y;
v@uv = set(u_ring, v_axis, 0);   // cylinder UV unwrap
```

Source: 2401_01 — drives rippling water wavefront expanding outward.

## R52: Blend toward reference geometry (procedural morph target)

**Problem**: Geometry should smoothly transition to a target shape based on a per-point mask.

```c
// point wrangle. Input 1 = target geometry (must have matching @ptnum).
float bias = chramp("ramp", fit(length(@P), 7.5, 10, 0, 1));
@P = lerp(@P, point(1, "P", @ptnum), bias);
```

Two-target morph (input 1 + input 2):
```c
float bias = chramp("ramp", @blend);
@P = lerp(@P, point(1, "P", @ptnum), fit(bias, 0,   0.5, 0, 1));
@P = lerp(@P, point(2, "P", @ptnum), fit(bias, 0.5, 1,   0, 1));
```

The two-target form is the core of multi-stage shape morphing (used in 2310_3101 weaving — a 7-stage transition between deformed curves).

Combine with R50 (mask stacking) to make the morph fire only in specific regions.

## R53: Prefix sum stacking (place items on top of each other)

**Problem**: A column of objects with different heights — each should sit on top of the previous one without gaps.

```c
// point wrangle on a polyline whose primintrinsic carries an array attribute "height"
float h[] = prim(0, 'height', i@primnum);   // array of per-segment heights
v@P.y = sum(h[0:i@ptnum]);                  // cumulative sum up to this point's index
```

`sum(arr[0:i])` is the **prefix sum** — `arr[0] + arr[1] + ... + arr[i-1]`. Each point's Y becomes the running total, so points stack exactly without overlap regardless of variable heights.

Generalizes to any 1D layout problem: stair steps with variable rise, beads on a string with variable size, layered shells with variable thickness.

Source: 落于ivi 2402_09 stacking objects.

## R54: Trail visualization (motion-blur-style streaks)

**Problem**: Visualize moving particles' direction as short tail lines.

```c
// point wrangle on a copy of the particles
@P = @P - (@v * chf("trailLength")) * @TimeInc;
```

Move each point backward along its velocity by `trailLength * dt`. Connect the original and trail point with a `polyline` for visible streaks. Combine with `pscale = chramp("trail", curveu)` to taper the line.

`@TimeInc` (frame duration in seconds) keeps the trail length frame-rate-independent — at 24 fps and 48 fps, the trail looks the same length.

## R55: Stage progression via blend chain (multi-stage shape morph)

**Problem**: A geometry should transition through N distinct shapes over time, blending smoothly between consecutive stages.

```c
// Each stage has 4 wrangles repeated with subscripts:
// 1. Stage-N deformation (sin / matrix / etc — defines shape)
// 2. f@pscale = chramp("Scale", @curveu - @Time * 0.1) * 4;          // scale envelope
// 3. v@P = lerp(@P, v@opinput1_P, chramp("Blend", @curveu - @Time * 0.1));   // blend to next stage
// 4. (optional) extra blend to a third stage:
//    v@P = lerp(@P, v@opinput1_P, fit(rblend, 0,   0.5, 0, 1));
//    v@P = lerp(@P, v@opinput2_P, fit(rblend, 0.5, 1,   0, 1));
```

Two key tricks:
1. **`@curveu - @Time * 0.1`** as the ramp X-axis — makes the blend wave sweep along the curve, giving directional progression instead of synchronous transition.
2. **3-way blend via `fit(t, 0, 0.5, 0, 1)` + `fit(t, 0.5, 1, 0, 1)`** — the first half blends to stage A, the second half blends to stage B. Smooth handoff at t=0.5.

Source: 落于ivi 2310_3101 weaving (7 progressive stages).

## R56: fBm — fractal noise loop (octave layering)

**Problem**: Need natural-looking noise (mountains, clouds, terrain). Single `noise()` is too smooth.

```c
// point or volume wrangle
vector npos    = @P / 1.0 + set(0, 666, 0);   // arbitrary offset to avoid origin
float namp     = 1.0;
float nval     = 0.0;
float nweight  = 0.0;
int   oct      = chi("octaves");                      // typically 4-9

for (int i = 0; i < oct; i++) {
    float n = abs(-0.5 + noise(set(npos.x, npos.y, npos.z, @Time)));   // 4D for animation
    nval    += n * namp;
    nweight += namp;
    npos    *= 2.132433;                              // lacunarity (avoid integers)
    namp    *= 0.666;                                 // persistence (gain)
}

float final = nval / nweight;                         // normalize
@Cd = pow(final, 0.8765);                             // gamma for visual punch
```

- `lacunarity` = 2.132433 (NOT 2.0 — exact powers create visible grids)
- `persistence` = 0.666 (controls roughness; <0.5 smooth, >0.7 noisy)
- `abs(noise - 0.5)` flips the noise into "turbulence" (sharp valleys) — drop the abs for plain fBm
- Normalize by `nweight` so amplitude is independent of `oct`

When `unifiednoise` SOP is too rigid, this is the manual recipe.

Source: 落于ivi VEX整理03 wrangle 47.

## R57: Mitered inset (uniform corner offset on polylines)

**Problem**: Inset a polyline by a fixed distance, but corners need extra inset (proportional to `1/sin(half_angle)`) so the offset distance is uniform.

```c
// point wrangle on a polyline (interior points only — pin endpoints separately)
float inset = chf("inset");
int nb[] = neighbours(0, @ptnum);
if (len(nb) != 2) return;          // skip endpoints / branch points

vector pos_0 = point(0, "P", nb[0]);
vector pos_1 = point(0, "P", nb[1]);

vector a = normalize(@P - pos_0);
vector b = normalize(@P - pos_1);
vector c = normalize(a + b) * -inset;       // bisector direction
float halfsine = sqrt((1.0 - dot(a, b)) / 2.0);   // sin of half-angle

@P += c / halfsine;
```

Why `1/halfsine`: at a 90° corner, walking the bisector by `inset` only moves you `inset * sin(45°) ≈ 0.707 * inset` perpendicular to the edge. Dividing by `sin(half_angle)` undoes the projection.

For 180° corners (straight line), `halfsine = 1` and the divide is a no-op. For acute angles, the divisor approaches 0 — clamp to avoid blowups.

Source: VEX整理03.

## R58: Cylindrical wrap (flat → tube)

**Problem**: A flat strip should wrap into a cylinder around the Y axis.

```c
// point wrangle
float rot    = chf("rotate");                   // 1 = full wrap, 0.5 = half wrap
float angle  = relbbox(0, @P).y * $PI * 2 * rot;

@P.z = cos(angle) * @P.x;
@P.x = sin(angle) * @P.x;
```

`relbbox.y * 2π` parametrizes Y from 0 to one full turn. `@P.x` becomes the radius (preserves the strip's width). `@P.z` is built fresh.

Inverse — cylinder back to flat:
```c
float angle = atan(@P.z, @P.x);
@P.x = length(set(@P.x, 0, @P.z));
@P.z = angle / (2 * $PI) * radius;
```

## R59: Smooth tangent via central difference (per-point curve normal)

**Problem**: Compute a smooth tangent direction along a polyline, with proper handling at endpoints.

```c
// point wrangle
vector pos;
if (@ptnum == 0) {
    @N = point(0, "P", @ptnum + 1) - @P;                                   // forward diff
} else if (@ptnum == npoints(0) - 1) {
    @N = @P - point(0, "P", @ptnum - 1);                                   // backward diff
} else {
    @N = (point(0, "P", @ptnum + 1) - point(0, "P", @ptnum - 1)) / 2;      // central diff
}
@N = normalize(@N);
```

Central difference is more accurate than `@N = next - current` (forward only), especially at curves. Endpoints use one-sided differences because there's no "before -1" or "after last".

This is the **finite-difference tangent** — discretized first derivative. Accurate to O(h²) for central; O(h) for forward/backward.

## R60: HSV adjustment (shift hue/saturation/value as one operation)

**Problem**: Shift the entire palette of `@Cd` by deltas in hue, saturation, value space (not RGB).

```c
// point wrangle
@Cd = hsvtorgb(rgbtohsv(@Cd) + set(ch("hue"), ch("sat"), ch("val")));
```

Useful for color theme variations, day/night palette shift, faded/saturated UI variants. Hue is angular: shift by 0.5 inverts colors (red ↔ cyan).

Hue-only shift on negative-N faces (handles back-face coloring):
```c
@Cd = @N;
if (sign(sum(@N)) < 0) {
    vector hsv = rgbtohsv(-@N);
    hsv.x -= 0.5;            // half-rotation = complementary color
    @Cd = hsvtorgb(hsv);
}
```

Source: master VEX `set_face_colour`.

## R61: Random alphabet pick (string array sampling)

**Problem**: Need random chars/strings per point.

```c
// point wrangle
string alphabet[] = string[](array(
    "A","B","C","D","E","F","G","H","I","J","K","L","M",
    "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"));

s@text = alphabet[int(fit01(rand(@ptnum), 0, len(alphabet) - 1))];
```

`string[](array(...))` is the verbose array-literal cast. `fit01(rand, 0, len-1)` maps rand to valid index range. `int()` truncates.

Use for procedural keyboard, runes, hex, license plates. Substitute `array("0".."F")` for hex chars, etc.

## R62: Hanging wire / catenary builder (detail wrangle)

**Problem**: Build a sagging cable between two anchor points, shape controlled by a ramp.

```c
// detail wrangle. Input 0 = 2 anchor points (start, end).
int N = chi("number_of_points");
vector A = point(0, "P", 0);
vector B = point(0, "P", 1);

for (int i = 1; i <= N; i++) {
    float t = float(i) / (N + 1);
    vector p = lerp(A, B, t);
    p.y -= chramp("Shape", t);          // sag controlled by ramp
    addpoint(0, p);
    if (i == 1) addprim(0, "polyline", 0, 2);                        // start segment
    else if (i == N) addprim(0, "polyline", N + 1, 1);                // end segment
    else addprim(0, "polyline", i + 1, i + 2);                        // interior segments
}
```

The chramp lets the artist draw the shape — drop a parabola for catenary, an asymmetric curve for off-balance hangs, multiple humps for tangled wire.

Source: 落于ivi VEX整理04.

## R63: Centroid pivot via stored inverse transform

**Problem**: Center a model at origin, do something, then return it to original position. (Used for rotation around centroid, scaling about centroid, etc.)

```c
// Wrangle 1: capture + center (point wrangle)
vector min, max;
getpointbbox(0, min, max);
vector centroid = (max + min) / 2.0;

matrix xform = invert(maketransform(0, 0, centroid, {0,0,0}, {1,1,1}));
@P *= xform;

// Save the matrix on every point so we can undo later
4@xform_matrix = xform;

// ... do work in centroid-relative coords ...

// Wrangle 2: restore (point wrangle)
@P *= invert(4@xform_matrix);
```

The matrix attribute lives on every point, which is wasteful for large meshes — promote to detail with `attribpromote` if memory matters.

Source: 落于ivi VEX整理04. Cleaner than `xform → ... → xform-with-negative-translate`.

## R64: Fan-open via per-prim rotation by index U

**Problem**: A line of N prims should fan out — rotated symmetrically around the center.

```c
// point or primitive wrangle
float spread = chf("spread");
v@P -= prim(0, "P", i@primnum);   // local pivot at prim centroid

float u = i@primnum / float(i@numprim - 1);   // 0..1 along the row
float amount = (u - 0.5) * spread;             // -spread/2 to +spread/2

matrix3 m = ident();
rotate(m, amount, {0,0,1});
v@P *= m;

v@P.z = u * 0.1;                  // slight Z stagger so they don't overlap
```

Combine with **modulo z-fold** for accordion fans:
```c
@P.z += (relbbox(0, @P).x * chi("steps")) % 2;   // 0/1 alternating fold
@P.z *= chf("depth");
```

Source: 2402_08 fan model.

## R65: Cumulative arc length along polyline

**Problem**: Per-point attribute `length_partial` = arc length from polyline start to this point.

```c
// primitive wrangle
int pts[] = primpoints(0, @primnum);
float length = 0;
addattrib(0, "point", "length_partial", 0.0);

for (int i = 1; i < len(pts); i++) {
    vector pa = point(0, "P", pts[i - 1]);
    vector pb = point(0, "P", pts[i]);
    length += distance(pa, pb);
    setpointattrib(0, "length_partial", pts[i], length);
}
f@length = length;            // total arc length on the prim
```

The `length_partial / @length` ratio gives a more accurate "how far along the curve am I" than `@curveu` (which is parametric, not arc-length-based, so it bunches at high-curvature regions).

Use whenever animation speed should be uniform along a non-uniform curve (cars on winding roads, walks along a path).

## How to use this catalog

When facing a new PCG problem:
1. Identify the problem in plain language ("filter sparse points", "pick one entrance", etc.)
2. Find matching recipe(s) above
3. Copy → adapt to context → done

Don't reinvent. These 20 recipes cover ~80% of the VEX in a typical PCG project.
