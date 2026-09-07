# Performance Triage

Common performance pitfalls in PCG and how to fix them. When cooks get slow, check these in order.

## Performance budget targets

For interactive iteration:
- Cook time per seed change: < 5 sec
- Polygon count: < 100k for viewport, < 1M for final render
- Memory peak: < 1 GB
- VDB voxel grid total cells: < 10M

If you exceed by 2x, fix it. By 10x, it's broken.

## Diagnosis: where is the time going?

Houdini's **Performance Monitor** (Windows menu) tells you exactly. Order of operations:

1. Open Performance Monitor (Windows → Performance Monitor)
2. Hit "Begin Recording"
3. Trigger a cook (change a parameter)
4. Hit "End Recording"
5. Look at "Cook Statistics" — sorted by cook time

The top 1-3 nodes account for 80% of cook time. Fix those.

## Top 10 perf issues (in order of frequency)

### Issue 1: VDB voxel size too fine

**Symptom**: `vdbfrompolygons` or `convertvdb` takes 5+ seconds.

**Root cause**: voxel_size default is often 0.1, but for grid_step=2 you only need ~0.5 (4x coarser → 64x fewer voxels).

**Fix**: set `vdbfrompolygons` voxel_size to `grid_step / 4` or `grid_step / 8`. For Lake House: 0.5 instead of 0.1.

**Speedup**: typically 8-64x.

### Issue 2: Scatter density too high

**Symptom**: `scatter` SOP shows N > 1000, then most points get filtered.

**Root cause**: artist mindset "more is better". But Stage 1 only needs enough points to populate the candidate grid post-fuse.

**Fix**: For grid-based pipelines, calculate target = `volume / (grid_step^3)` and use 4-5x of that. Lake House: ~80 grid cells × 5 = 400 points (matches actual config).

**Speedup**: 2-10x.

### Issue 3: For-loop block over too many iterations

**Symptom**: `for-loop block_end` cook time scales linearly with iterations and is slow.

**Root cause**: Each iteration cooks all internal nodes from scratch. K iterations × N nodes = K×N cooks.

**Fix options**:
- Reduce iteration count if possible (`itermethod=count` with smaller N)
- Replace with a single-pass detail wrangle if algorithm allows
- Add `i@stop` early termination (`feedback` mode)

**Speedup**: depends on algorithm. Sometimes 10-100x.

### Issue 4: Object_merge causing redundant cooks

**Symptom**: Two object_merge nodes pulling from the same source — that source is cooked twice.

**Root cause**: Houdini caches per-node, but if multiple object_merge instances exist, each may trigger separate cooks.

**Fix**: Pull through a single null node, then split. Or use the `Source Group` parameter to limit cook scope.

**Speedup**: 2x for the duplicated source.

### Issue 5: Wrangle with O(N²) inner loop

**Symptom**: A wrangle is slow, code has nested loop over all points.

```c
// BAD
for (int i = 0; i < npoints(0); i++) {
    for (int j = 0; j < npoints(0); j++) {
        // distance check
    }
}
```

**Fix**: Use `pcopen` / `nearpoints` (KD-tree, O(log N)).

```c
// GOOD
int handle = pcopen(0, "P", @P, radius, max_pts);
while (pciterate(handle)) { ... }
```

**Speedup**: 100-1000x for N>1000.

### Issue 6: Heavy VEX inside `piece` mode for-loop

**Symptom**: `for-loop block_end (piece)` slow with many iterations.

**Root cause**: piece mode creates many tiny "geometry" inputs, each cooked separately.

**Fix**: Combine into a single detail wrangle if logic allows. Or batch pieces (process N at a time).

**Speedup**: 5-20x.

### Issue 7: Copytopoints with many large modules

**Symptom**: `copytopoints` is the top cook time.

**Root cause**: Each module being copied has high poly count. N points × M polys = N×M output polys.

**Fix options**:
- Reduce module poly count (artist task)
- Use `instance` instead of `copytopoints` for far-away / non-deformed cases
- Use `pack` SOP to convert modules to packed primitives (rendered without geometry expansion)

**Speedup**: 10-100x for memory; render speed depends on engine.

### Issue 8: Unnecessary `fuse` calls

**Symptom**: Many `fuse` SOPs, each adding 100-500ms.

**Root cause**: copy-pasted "fuse after every wrangle" mentality.

**Fix**: Only fuse when needed (after `rint`-based position changes, after VDB output, after merge). Most other places don't need it.

**Speedup**: minor per fuse (200ms × N), but adds up.

### Issue 9: Cooking the entire OBJ on every parameter change

**Symptom**: Even tiny parameter changes trigger 5-second cook.

**Root cause**: All nodes downstream of the parameter need re-cook. Some are expensive but rarely change (e.g., the module library).

**Fix**: Cache stable nodes with `cache` SOP set to "always cache":
- After Stage 1 volume generation (rarely changes if seed is stable)
- After loading module library (only changes if .obj swap)

Then small parameter tweaks only re-cook downstream of the cache.

**Speedup**: 5-20x for iterative work.

### Issue 10: Foreach `attributewrangle` with high-overhead body

**Symptom**: Detail wrangle iterating over all primitives is slow.

**Root cause**: Every iteration is O(N) — total O(N²).

**Fix**: Convert to primitive wrangle (parallel by default).

**Speedup**: 4-16x on multi-core CPU.

## Memory issues

### Issue 11: VDB volume too large

**Symptom**: Memory peaks at 5+ GB during cook.

**Root cause**: VDB grid covers entire bounding box, even sparse regions.

**Fix**: 
- Crop input geometry tightly before vdbfrompolygons
- Use sparse VDB (default in modern Houdini, verify it's not converting to dense)
- Increase voxel_size

### Issue 12: Geometry attribute bloat

**Symptom**: Final geometry has 30+ attributes per prim/point.

**Root cause**: Protocol attributes never cleaned up (see DEBT_CHECKLIST.md item 3).

**Fix**: `attribdelete` at subnet boundaries with pattern `_p_*` or specific dead attribute names.

**Memory saving**: linear in N × |dead_attrs|. For 100k prims × 20 dead attribs × 16 bytes ≈ 32 MB.

### Issue 13: Modules loaded redundantly

**Symptom**: Same .obj file loaded by multiple `file` SOPs.

**Root cause**: Each module category subnet loads its own copy.

**Fix**: Use `object_merge` from a single global "modules library" subnet. One load, many references.

## Render-time issues (post-Houdini)

### Issue 14: Tessellation explosion in Unreal

**Symptom**: Asset cooks fine in Houdini but Unreal viewport drops to 5 fps.

**Root cause**: Each module is a unique mesh; engine can't instance.

**Fix**:
- Pack modules into a small library, use mesh instance components
- Bake to Unreal HLOD if it's a static asset

### Issue 15: Material count explosion

**Symptom**: Asset has 200+ materials in Unreal.

**Root cause**: Each module has unique material IDs.

**Fix**:
- Standardize materials: artist provides "wood material" / "metal material" / etc.
- Use vertex color or attribute to drive shader variations

## Performance-aware authoring habits

### Habit 1: Profile early, profile often

Don't wait until the end to optimize. Run Performance Monitor after each major addition.

### Habit 2: Strip non-essential subnets when iterating

If you're tweaking only the roof, temporarily disable the body / setdressing subnets via `null` switch. Iterate fast, re-enable when done.

### Habit 3: Use `null` separators

Add `null` SOPs at major stage boundaries. Lets you debug what each stage outputs without re-cooking the whole pipeline.

### Habit 4: Document slow paths

If a node is slow but unavoidable, note it in a sticky note: "VDB takes 3s — necessary for boolean union, can't reduce."

### Habit 5: Optimize what's measured

Don't guess. Performance Monitor before fixing. Often the "obviously slow" node isn't the bottleneck.

## When to give up optimizing

Some assets just take time to cook. If after fixing the top 3 issues you're at:
- 10 sec per cook for a 1M-poly building
- 30 sec per cook for a 10M-poly city

That's reasonable. Don't kill yourself over the last 20%. Focus on **interactive iteration speed** (which means caching), not absolute cook time.

## Performance checklist (run before shipping)

- [ ] Performance Monitor shows top node < 2 sec
- [ ] Total cook < 5 sec at default parameters
- [ ] Memory peak < 1 GB
- [ ] No O(N²) loops detected
- [ ] VDB voxel size sane (`grid_step / 4` or coarser)
- [ ] Stage boundaries have caches for fast iteration
- [ ] Protocol attributes cleaned at subnet exits
- [ ] Render-time costs verified in target engine (if applicable)
