---
name: houdini-vex-deepread-2026-05-14
description: "First systematic deep-read of Houdini official VEX docs — 28 counter-intuitive insights + 5 selection tables across language, @ syntax, noise/random, attrib I/O & spatial queries"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 204f5c3b-21f7-4f43-95ad-8dbf3261ef3f
---

第一次系统精读 Houdini 官方 VEX 文档(https://www.sidefx.com/docs/houdini/vex/)的产出。4 轮共覆盖 VEX 章节 8 个子页面,出 28 个反常识知识点 + 5 张选型表。配套 [[houdini_procedural_modeling]] 36 patterns + 10 思维约束使用——这一篇是"语言层底座",patterns 是"算法层应用"。

学习模式:扫描 vs 精读区分(Houdini 21 docs 64 章节顶层图 + VEX 章节 20 子页面图先扫描);按"逐层 why + 影响链"风格,只挑反常识/有杠杆的料,对准 36 patterns 解读。

---

## 精读覆盖

| 轮 | 子页面 | 产出 |
|---|---|---|
| 1 | `vex/lang.html` + `vex/contexts/index.html` | 7 个反常识(语言层) |
| 2 | `vex/snippets.html` + `vex/geometry.html`(traversal) | @ 语法表 + 4 模式语义表 |
| 3 | `vex/random.html` + `functions/noise` + `functions/random` + `functions/curlnoise` | 6 noise 选型表 + 8 个反常识 |
| 4 | `functions/point` + `functions/setpointattrib` + `functions/xyzdist` + `functions/intersect` | 7 个反常识 + 2 张选型表 |

---

## 第一轮:VEX 语言层 7 个反常识

### 1. ⭐⭐⭐ "你不是在写 SOP wrangle,你在写 cvex"

contexts 文档把 `sop` context 明确标为 obsolete。日常 attribwrangle 实际是 `cvex` context 在 SOP 节点里被特殊调度,通过 4 种 "run over" 模式(Detail/Points/Primitives/Vertices)决定循环边界。`@P` `@ptnum` 是 SOP wrangle 节点为 cvex 绑定进去的隐含变量。

### 2. ⭐⭐⭐ run-over 模式下 `@ptnum`/`@primnum` 是「借用」语义

| 模式 | `@ptnum` | `@primnum` |
|---|---|---|
| Points | 当前点 | 含此点的任意一个 prim(或 -1) |
| Primitives | 当前 prim 的第 0 号 vertex 连接的点 | 当前 prim |
| Vertices | 当前 vertex 连接的点 | 拥有此 vertex 的 prim |
| Detail | 没意义(全局只跑一次) | 同上 |

Primitive wrangle 里 `@ptnum` 不是"该 prim 的所有点",只是它第一个点 —— 要全部得用 `primpoints()`。

### 3. ⭐⭐⭐ `@` 自动转型有白名单,不在表上的会被当 float

vector 白名单(节选):`@P @N @Cd @v @scale @force @up @uv @rest @torque @center @accel`
vector4:`@orient @rot @backtrack`
int:`@id @ptnum @primnum @numpt @numelem @ix/iy/iz @resx/y/z`
string:`@name @instance`

写 `@myforce = {1,2,3}` 不会得到 vector,会被当 float。必须 `v@myforce`。

### 4. ⭐⭐⭐ 函数参数默认 by-reference,改了就改了调用方的

```vex
void scale_it(vector v) { v *= 2; }   // 这会改外面的 v!
void scale_it(const vector v) {...}   // 只读
void scale_it(export vector v) {...}  // 打算回写到 geometry
```

来自 C/Python 的人会以为是局部副本——错。VEX 等于全 inline,所有参数 = 引用。

### 5. ⭐⭐⭐ 没有递归 —— compiler inline,必须迭代或借 shadercall

文档原话:"Recursion will not work" because of automatic inlining。要递归只能拆两个 cvex 用 shadercall 互相调。36 patterns 里的"最长路径/树遍历/决策树"全部迭代版本是被语言强制的。

### 6. ⭐⭐ vector4 quaternion 顺序是 x/y/z/w(不是 w/x/y/z)

跟 Eigen / ROS / GLM 习惯顺序相反。任何从外部导入的四元数都要重排。`p@orient` 的 .w 是第 4 位,记忆"VEX 里 w 永远是最后一个"。

### 7. ⭐⭐ `@group_‹name›` 是虚拟属性,group 当 attribute 读

```vex
if (@group_inner) { ... }  // 当前元素是否在 inner group
i@group_inner = 1;          // 加入 group
```

不需要先 unpack。比 `inpointgroup()` 调用更快。

---

## 第二轮:@ 类型语法 + 4 模式语义

### @ 属性类型前缀完整表

| 前缀 | 类型 | 例 |
|---|---|---|
| `f@` | float | `f@mass` |
| `u@` | vector2 | `u@uv2d` |
| `v@` | vector | `v@force` |
| `p@` | vector4 | `p@orient` |
| `i@` | int | `i@id` |
| `2@` | matrix2 | `2@xform2d` |
| `3@` | matrix3 | `3@rot` |
| `4@` | matrix(4×4) | `4@xform` |
| `s@` | string | `s@name` |
| `d@` | dict | `d@data` |
| `@` | auto-cast(白名单内)/默认 float | `@P` `@Cd` |

### 4 种 run-over 模式

详见上面表 2。

### 声明 vs 自动创建

显式声明可指定类型 + 默认值(右侧必须常量):
```vex
float @mass = 1;
vector @up = {0, 1, 0};
```

自动创建首次赋值即建,默认 0/空。

---

## 第三轮:noise & random 8 个反常识 + 选型

### 1. ⭐⭐⭐ VEX `noise()` 范围是 0-1 中位 0.5,不是 [-1,1]

跟 GLSL/Substance/Blender 教程的 Perlin 公式不同。要对称信号:`noise(...) * 2 - 1`。要 displacement 不偏移:`noise(...) - 0.5`。高维 noise 还会趋向 Gaussian。

### 2. ⭐⭐⭐ `random()` 是 position-based hash,不是流式 PRNG

position 本身就是种子。无内部状态。要多个独立通道:换 position(加偏移、串字符串 hash)。

### 3. ⭐⭐⭐ `random()` 只对整数变化敏感(等价 `noise(floor(p))`)

为什么 random 散布有"格子感"——浮点输入被 floor。要平滑用 `rand()` 或 `noise()`。

### 4. ⭐⭐⭐ 6 种 noise 选型表

| 函数 | 类型 | 视觉 | cost | 何时用 |
|---|---|---|---|---|
| `noise()` | Perlin(改良) | 柔和起伏 | 1.0 | 默认通用 |
| `onoise()` | Original Perlin(1985) | 略带网格 | 1.1 | 跟老资产对齐 |
| `wnoise()` | Worley 元胞 | 元胞/裂纹 | 1.8 | 石头/岩纹/voronoi |
| `vnoise()` | Voronoi 元胞 | 元胞 | — | 同上,API 不同 |
| `snoise()` | Sparse Convolution | 颗粒/斑点 | 2.1 | 噪点纹理 |
| `anoise()` | Alligator | 鳄鱼皮纹 | 2.3 | 特化,少用 |

默认 `noise()`,要元胞才换 wnoise/vnoise。

### 5. ⭐⭐⭐ Perlin 没有周期版,要 tileable 必须 `pnoise()`

`noise()` 在空间无限延伸不重复。做无缝贴图、循环动画必须 `pnoise()`(接受 period 参数)。

### 6. ⭐⭐⭐ `curlnoise()` 是 divergence-free 向量场

```vex
v@dir = curlnoise(@P * 0.5);   // 永远不汇聚不发散——像无源流体
```

散布物体方向、毛发流向、烟雾运动用它,而不是 `vector(noise(),noise(),noise())`(那是带源场,粒子会聚)。兄弟:`curlnoise2d` `curlxnoise`(simplex,更便宜) `cwnoise`(Worley 出元胞流)。

### 7. ⭐⭐ `nrandom()` 不可重现 —— procedural 通常不用

无 seed 控制,只用于调试/无所谓重现的场合。

### 8. ⭐⭐ `random_shash()` 哈希字符串

按 `s@name` 等字符串 attrib 当 seed,做"按物体名分类着色"等。

### 选型决策树

```
要随机数?
├─ 离散,position 即 seed         → random(int|vec)
├─ 连续浮点也要变化              → rand(float)
├─ 字符串当 seed                 → random_shash(s)
├─ 完全无所谓重现                 → nrandom()       ← 罕用
└─ 跟 hscript expression 对齐    → hscript_rand()  ← 跨平台不要

要噪声?
├─ 标量场 (mask/density/disp)    → noise(p)              [0,1]
├─ 元胞/裂纹                    → wnoise(p) / vnoise(p)
├─ 流向场 (无源)                 → curlnoise(p)
├─ 必须无缝循环                  → pnoise(p, period)
└─ 颗粒/斑点                    → snoise(p)
```

---

## 第四轮:读写 attrib + 表面/射线 7 个反常识 + 2 张选型表

### 1. ⭐⭐⭐ `point()` 读不存在的属性返回 0,不报错

静默 bug 之王。typo `point(0,"Cdd",@ptnum)` 不报,你以为是黑色其实是 0 当 vector。明确"是否存在"用 `pointattrib()`(带 success flag)。

### 2. ⭐⭐⭐ `setpointattrib()` 的 mode 参数 8 选 1,是并行写入聚合命脉

```vex
setpointattrib(0, "Cd", @ptnum, color, "set");      // 默认覆盖
setpointattrib(0, "weight", @ptnum, w, "add");      // 累加,并行安全
setpointattrib(0, "max_h", @ptnum, h, "max");
setpointattrib(0, "min_d", @ptnum, d, "min");
setpointattrib(0, "xform", @ptnum, m, "mult");      // 矩阵相乘
setpointattrib(0, "tags", @ptnum, "x", "append");   // 字符串/数组追加
setpointattrib(0, "group_in", @ptnum, 0, "toggle"); // 翻转,group 切换
```

"set" 多线程同点竞争是 last-write-wins(不可预测)。"add/min/max/mult" 是 reduction,并行确定。

### 3. ⭐⭐⭐ `setpointattrib()` 自动创建,但默认值是 0/空

要控默认值得先 `addattrib()`。sparse 写入(if 条件下才 set)未访问的点会保持默认 0。

### 4. ⭐⭐⭐ 标准名(Cd/N/P/orient)自动设 type info,自定义名要 `setattribtypeinfo()`

`v@N` 自动 type info 是 "normal";自定义 `v@up` 默认 "vector"。差别在 transform——只有 normal 类型在 SOP transform 下才正确旋转。修法:`setattribtypeinfo(0, "point", "up", "vector"|"normal"|"point"|"color"|"quaternion")`。

### 5. ⭐⭐⭐ `xyzdist()` 返回 distance + out param 给 prim+uv —— 配 `primuv()` 拿任意属性

```vex
int prim;
vector uv;
float d = xyzdist(1, @P, prim, uv);
vector surf_P = primuv(1, "P", prim, uv);
vector surf_N = primuv(1, "N", prim, uv);
```

"投影 + 在投影点上读任意属性"的标准三段式。⚠️ packed prim 和非均匀缩放 sphere/tube/circle 距离不准。`xyzdist` vs `minpos`:后者只给 3D 位置不给 prim。

### 6. ⭐⭐⭐ `intersect()` 的 dir 向量长度 = 最大搜索距离(不是 normalized)

文档:"uses the length of the vector as the maximum distance to search."

99% 教程没说清。写 `intersect(1, @P, normalize(dir), ...)` 默认 max=1,只能 1 单位。要无限远:`normalize(dir) * 1e6`。

### 7. ⭐⭐⭐ 三种穿透模式

| 函数 / 选项 | 返回 |
|---|---|
| `intersect()` | 第一次命中 |
| `intersect_all()` | 沿射线全部命中 |
| `intersect()` + `"farthest"` | 最远命中 |

厚度测量用 `intersect_all`。"对面那一面"用 `farthest`。metaball 特殊:返回 prim count 而不是 hit prim。

### 选型表 — 读写 attrib

| 你想 | 用 |
|---|---|
| 读其他输入的 point 属性 | `point(input, "name", ptnum)` |
| 同上但要"是否存在" | `pointattrib(input, "name", ptnum, exists)` |
| 读 prim/vertex/detail 属性 | `prim()` / `vertex()` / `detail()` |
| 写当前几何 point attrib | `setpointattrib(0, "name", ptnum, val, mode)` |
| 并行写同点不冲突 | mode 用 `add`/`min`/`max`/`mult` |
| 控默认值/类型 | 先 `addattrib()` 或 `setattribtypeinfo()` |

### 选型表 — 表面/射线

| 你想 | 用 |
|---|---|
| 表面最近距离 | `xyzdist(geo, P)` |
| 上 + prim+uv | `xyzdist(geo, P, prim, uv)` |
| 上 + 拿落点属性 | + `primuv(geo, "attr", prim, uv)` |
| 仅 3D 位置 | `minpos(geo, P)` |
| 射线第一次相交 | `intersect(geo, orig, dir*maxlen, p, u, v)` |
| 沿线全部 | `intersect_all(...)` |
| 最远 | `intersect(...)` + `"farthest"` flag |

---

## 反思五问总结(对应 [[feedback_houdini_reflection]])

1. **为什么 VEX 这么设计?** —— 为并行写入而生:position-based hash、reduction mode、属性自动创建、不可递归——全是"每个元素独立计算 + 偶尔聚合"模式服务的
2. **意义?** —— 36 patterns 里那些"看起来像 SQL/NumPy 但又不是"的 idiom 全有底层解释:数据并行编程范式
3. **节点角色?** —— attribwrangle = cvex 在 SOP 调度下的 "run over" 包装;不是独立 context
4. **属性角色?** —— `@P` 是真物理量,`@ptnum`/`@primnum` 是当前迭代游标(借用语义),`@group_xxx` 是虚拟 0/1 视图
5. **复现配方?** —— 任何 36 pattern 现在都能拆成「context 类型 → run-over 模式 → 用什么 attrib 读 / 用什么 mode 写 / 用什么 spatial query」四要素

---

## 还没读到(下次 session 候选,按 PCG 命脉排序)

1. ⭐⭐⭐ `model/` 章节 —— Houdini geometry 数据模型本身(point/vertex/primitive/detail 4 级 + packed prim + intrinsics)
2. ⭐⭐⭐ `vex/groups.html` + `halfedges.html` —— 拓扑高效路径(half-edge 是 36 patterns 里"边邻接"的官方解)
3. ⭐⭐⭐ `assets/` 章节(HDA) —— 直接对准 PCG 师交付物
4. ⭐⭐ `network/` 章节 —— 节点网络与参数引用
5. ⭐⭐ `vex/cookbook.html` —— 官方"答案集",对照 36 patterns 找空白

跟 [[houdini_procedural_modeling]] 36 patterns + 10 思维约束配套使用。
