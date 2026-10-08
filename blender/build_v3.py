"""Sunlit Shores v3 — pulau ORGANIK.
- Base tebing: ring bmesh resolusi tinggi + deform noise 3 oktaf (tepian bergelombang).
- Layer bertingkat + overhang, tonjolan batu, rumput menjuntai (lip).
- Semua smooth shading. Warna via VERTEX COLOR (1 material putih) —
  gradasi gelap-dingin bawah -> terang-hangat atas + fake AO.
- Pohon berkelompok (2-3 cluster), tajuk gabungan sphere bergelombang,
  semak, batu kecil, bunga. Skala/rotasi/miring acak.
- Export GLB TANPA rotasi tambahan (glTF native Y-up).
Via bridge."""
import bpy
import bmesh
import math
import random

random.seed(11)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- noise 3 oktaf ----------
def noise2(x, y):
    v = (math.sin(x * 1.7 + math.cos(y * 1.3) * 2.1) * 0.5
         + math.sin(x * 3.3 + y * 2.7 + 1.7) * 0.25
         + math.sin(x * 6.1 - y * 5.3 + 4.2) * 0.125)
    return v / 0.875

# ---------- 1 material putih + vertex color ----------
M = bpy.data.materials.new("M_VC")
M.use_nodes = True
bsdf = M.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
bsdf.inputs["Roughness"].default_value = 0.85
vc_node = M.node_tree.nodes.new("ShaderNodeVertexColor")
vc_node.layer_name = "Color"
M.node_tree.links.new(vc_node.outputs["Color"], bsdf.inputs["Base Color"])

coll = bpy.data.collections.new("SunlitV3")
bpy.context.scene.collection.children.link(coll)

def link(o):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    return o

def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    o.data.materials.append(M)
    return o

def paint(mesh, colors):
    """colors: list rgb per vertex."""
    ca = mesh.color_attributes.new(name="Color", type="FLOAT_COLOR", domain="POINT")
    for i, c in enumerate(colors):
        ca.data[i].color = (c[0], c[1], c[2], 1.0)

def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

# palet
ROCK_DARK = (0.30, 0.36, 0.44)    # dingin gelap (bawah)
ROCK_LITE = (0.60, 0.63, 0.67)    # hangat terang (atas)
GRASS_TOP = (0.52, 0.80, 0.26)    # hijau vivid
GRASS_SIDE = (0.30, 0.52, 0.20)   # olive gelap (sisi/bawah)
SAND_TOP = (0.98, 0.90, 0.66)
SAND_SIDE = (0.78, 0.68, 0.47)
TRUNK = (0.45, 0.32, 0.19)
LEAF_A = (0.30, 0.62, 0.22)
LEAF_B = (0.22, 0.52, 0.20)
FLOWER = [(0.95, 0.45, 0.55), (0.98, 0.85, 0.30), (0.95, 0.95, 0.95)]

# ---------- builder cakram berlapis ----------
def layered(name, cx, cy, profile, segs=56, seed=0.0, top_cap=True):
    """profile: list (z, r, amp). Return (obj, z_top)."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    link(obj)
    bm = bmesh.new()
    rings = []
    for (z, r, amp) in profile:
        ring = []
        for i in range(segs):
            a = i / segs * math.pi * 2
            n = noise2(math.cos(a) * 1.6 + seed + cx * 0.15,
                       math.sin(a) * 1.6 + seed * 1.3 + cy * 0.15)
            rr = r * (1.0 + amp * n)
            ring.append(bm.verts.new((cx + math.cos(a) * rr, cy + math.sin(a) * rr, z)))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for ri in range(len(rings) - 1):
        for i in range(segs):
            j = (i + 1) % segs
            try:
                bm.faces.new((rings[ri][i], rings[ri][j], rings[ri + 1][j], rings[ri + 1][i]))
            except ValueError:
                pass
    # tutup bawah mengerucut (pulau melayang)
    zb = rings[0][0].co.z
    tip = bm.verts.new((cx, cy, zb - 1.6))
    for i in range(segs):
        j = (i + 1) % segs
        try:
            bm.faces.new((tip, rings[0][j], rings[0][i]))
        except ValueError:
            pass
    if top_cap:
        zt = rings[-1][0].co.z
        cen = bm.verts.new((cx, cy, zt))
        for i in range(segs):
            j = (i + 1) % segs
            try:
                bm.faces.new((cen, rings[-1][i], rings[-1][j]))
            except ValueError:
                pass
    bm.to_mesh(mesh)
    bm.free()
    return smooth(obj)

def vcolor_gradient(obj, c_bottom, c_top, ao_strength=0.30):
    me = obj.data
    zs = [v.co.z for v in me.vertices]
    zmin, zmax = min(zs), max(zs)
    cols = []
    for v in me.vertices:
        t = (v.co.z - zmin) / max(zmax - zmin, 1e-5)
        c = lerp(c_bottom, c_top, t ** 0.8)
        ao = 1.0 - ao_strength * (1.0 - t)          # celah bawah lebih gelap
        cols.append((c[0] * ao, c[1] * ao, c[2] * ao))
    paint(me, cols)

def island(name, x, y, r, h, sand=False, seed=0.0):
    # tebing: melebar ke bawah, bibir menggantung di atas
    prof = [
        (0.0, r * 0.45, 0.10),
        (h * 0.30, r * 0.68, 0.09),
        (h * 0.55, r * 0.82, 0.08),
        (h * 0.80, r * 0.94, 0.07),
        (h * 0.94, r * 1.00, 0.06),   # bibir paling lebar -> overhang
        (h, r * 0.96, 0.06),
    ]
    rock = layered(f"{name}_rock", x, y, prof, seed=seed, top_cap=False)
    vcolor_gradient(rock, ROCK_DARK, ROCK_LITE)
    # rumput: menjuntai keluar (lip)
    cap = 0.8
    gprof = [
        (h - 0.15, r * 0.97, 0.05),
        (h + cap * 0.45, r * 1.06, 0.055),   # menjuntai
        (h + cap, r * 1.01, 0.05),
    ]
    top_c = SAND_TOP if sand else GRASS_TOP
    side_c = SAND_SIDE if sand else GRASS_SIDE
    grass = layered(f"{name}_grass", x, y, gprof, seed=seed + 9.0, top_cap=True)
    me = grass.data
    zs = [v.co.z for v in me.vertices]
    zmin, zmax = min(zs), max(zs)
    cols = []
    for v in me.vertices:
        t = (v.co.z - zmin) / max(zmax - zmin, 1e-5)
        c = lerp(side_c, top_c, t ** 0.7)
        # tepi atas lebih terang (sun-kissed rim)
        if t > 0.85:
            c = lerp(c, (min(c[0] + 0.08, 1), min(c[1] + 0.08, 1), c[2]), (t - 0.85) / 0.15)
        cols.append(c)
    paint(me, cols)
    return h + cap

def rock_lump(x, y, z, s, seed):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=s, location=(x, y, z))
    o = smooth(link(bpy.context.active_object))
    for v in o.data.vertices:
        n = 1.0 + 0.22 * noise2(v.co.x * 2 + seed, v.co.y * 2 + v.co.z)
        v.co.x *= n; v.co.y *= n; v.co.z *= n * 0.85
    vcolor_gradient(o, (0.30, 0.35, 0.42), (0.58, 0.61, 0.65), ao_strength=0.2)
    return o

# ---------- vegetasi ----------
def canopy_blob(x, y, z, s, seed, palette):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=s, location=(x, y, z))
    o = smooth(link(bpy.context.active_object))
    for v in o.data.vertices:
        n = 1.0 + 0.20 * noise2(v.co.x * 1.8 + seed, (v.co.y + v.co.z) * 1.8)
        v.co.x *= n; v.co.y *= n; v.co.z *= n * 0.9
    me = o.data
    zs = [v.co.z for v in me.vertices]
    zmin, zmax = min(zs), max(zs)
    cols = []
    for v in me.vertices:
        t = (v.co.z - zmin) / max(zmax - zmin, 1e-5)
        base = palette[0] if noise2(v.co.x * 3, v.co.y * 3 + seed) > 0 else palette[1]
        c = lerp(tuple(b * 0.72 for b in base), base, t)
        cols.append(c)
    paint(me, cols)
    return o

def tree(x, y, z, s=1.0, idx=0, lean=None):
    lean = lean if lean is not None else random.uniform(0, 0.12)
    la = random.uniform(0, math.pi * 2)
    # batang melengkung: 3 segmen
    px, py, pz = x, y, z
    for i in range(3):
        bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.15 * s * (1 - i * 0.18),
                                            depth=0.9 * s,
                                            location=(px, py, pz + 0.45 * s))
        seg = smooth(link(bpy.context.active_object))
        seg.name = f"Tree{idx}_trunk{i}"
        seg.rotation_euler = (math.cos(la) * lean, math.sin(la) * lean, 0)
        paint(seg.data, [TRUNK] * len(seg.data.vertices))
        px += math.sin(la) * lean * 0.9 * s
        py += math.cos(la) * lean * 0.9 * s
        pz += 0.85 * s
    # tajuk: 4-5 blob menyatu di ujung lengkung
    nblob = random.randint(4, 5)
    for b in range(nblob):
        a = random.uniform(0, math.pi * 2)
        rr = random.uniform(0.2, 0.9) * s
        canopy_blob(px + math.cos(a) * rr, py + math.sin(a) * rr,
                    pz + random.uniform(-0.1, 0.6) * s,
                    random.uniform(0.55, 0.9) * s,
                    seed=idx * 3.1 + b, palette=(LEAF_A, LEAF_B)).name = f"Tree{idx}_canopy{b}"

def bush(x, y, z, s):
    o = canopy_blob(x, y, z + s * 0.4, s, seed=x + y, palette=(LEAF_A, LEAF_B))
    o.name = "Bush"
    o.scale.z = 0.7

def flower(x, y, z, idx):
    c = FLOWER[idx % len(FLOWER)]
    bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.03, depth=0.35, location=(x, y, z + 0.17))
    st = smooth(link(bpy.context.active_object)); st.name = f"Flower{idx}_stem"
    paint(st.data, [(0.25, 0.45, 0.2)] * len(st.data.vertices))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.11, location=(x, y, z + 0.4))
    hd = smooth(link(bpy.context.active_object)); hd.name = f"Flower{idx}_head"
    paint(hd.data, [c] * len(hd.data.vertices))

def scatter_cluster(cx, cy, cz, trees_n, spread, idx0, flowers_n=3):
    idx = idx0
    for _ in range(trees_n):
        a = random.uniform(0, math.pi * 2)
        rr = random.uniform(0.5, spread)
        tree(cx + math.cos(a) * rr, cy + math.sin(a) * rr, cz,
             s=random.uniform(0.7, 1.3), idx=idx,
             lean=random.uniform(0, 0.105))  # 0-6 derajat
        idx += 1
    for f in range(flowers_n):
        a = random.uniform(0, math.pi * 2)
        rr = random.uniform(1.0, spread + 1.2)
        flower(cx + math.cos(a) * rr, cy + math.sin(a) * rr, cz, idx + f)
    # semak + batu kecil
    for _ in range(3):
        a = random.uniform(0, math.pi * 2)
        rr = random.uniform(0.5, spread + 0.8)
        bush(cx + math.cos(a) * rr, cy + math.sin(a) * rr, cz, random.uniform(0.3, 0.55))
    return idx

# ---------- props (adaptasi v2, vertex color) ----------
def solid_paint(obj, rgb):
    paint(obj.data, [rgb] * len(obj.data.vertices))

def lighthouse(x, y, z):
    parts = [(1.5, 1.6, 1.2, (0.96, 0.95, 0.92), 0.6), (1.3, 1.5, 1.8, (0.85, 0.24, 0.25), 2.1),
             (1.1, 1.3, 1.8, (0.96, 0.95, 0.92), 3.9), (0.95, 1.1, 1.4, (0.85, 0.24, 0.25), 5.5)]
    for r1, r2, h, col, lz in parts:
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=1, depth=1, location=(x, y, z + lz))
        o = smooth(link(bpy.context.active_object))
        for v in o.data.vertices:
            t = v.co.z + 0.5
            s = r1 * t + r2 * (1 - t)
            v.co.x *= s; v.co.y *= s
        o.scale.z = h
        solid_paint(o, col)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0, location=(x, y, z + 6.9))
    dome = smooth(link(bpy.context.active_object)); dome.name = "LH_dome"
    dome.scale = (1.0, 1.0, 1.3)
    solid_paint(dome, (0.47, 0.53, 0.60))

def hut(name, x, y, z):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 0.75))
    base = link(bpy.context.active_object); base.name = f"{name}_base"
    for p in base.data.polygons:
        p.use_smooth = False
    base.scale = (2.0, 1.6, 1.5)
    base.data.materials.append(M)
    solid_paint(base, (0.85, 0.45, 0.22))
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.7, depth=1.2, location=(x, y, z + 2.1))
    roof = link(bpy.context.active_object); roof.name = f"{name}_roof"
    for p in roof.data.polygons:
        p.use_smooth = False
    roof.rotation_euler = (0, 0, math.pi / 4)
    roof.data.materials.append(M)
    solid_paint(roof, (0.50, 0.35, 0.20))

def bridge(name, ax, ay, az, bx, by, bz):
    import mathutils
    a = mathutils.Vector((ax, ay, az)); b = mathutils.Vector((bx, by, bz))
    n = max(3, int((b - a).length / 0.45))
    for i in range(n):
        t = i / (n - 1)
        p = a.lerp(b, t); p.z += math.sin(t * math.pi) * 0.25
        bpy.ops.mesh.primitive_cube_add(size=1, location=(p.x, p.y, p.z))
        plank = link(bpy.context.active_object); plank.name = f"{name}_plank{i}"
        for pg in plank.data.polygons:
            pg.use_smooth = False
        plank.scale = (0.28, 1.3, 0.12)
        plank.rotation_euler = (0, 0, math.atan2(by - ay, bx - ax) + math.pi / 2)
        plank.data.materials.append(M)
        solid_paint(plank, (0.50, 0.35, 0.20))

def boat(name, x, y, rot=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=8, radius=1, location=(x, y, 0.5))
    hull = smooth(link(bpy.context.active_object)); hull.name = f"{name}_hull"
    hull.scale = (1.0, 2.0, 0.55)
    for v in hull.data.vertices:
        if v.co.z < -0.2:
            v.co.z = -0.2
    hull.rotation_euler = (0, 0, rot)
    solid_paint(hull, (0.50, 0.35, 0.20))
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.07, depth=3.4, location=(x, y, 2.2))
    mast = smooth(link(bpy.context.active_object)); mast.name = f"{name}_mast"
    solid_paint(mast, (0.50, 0.35, 0.20))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x + 0.9, y, 2.4))
    sail = link(bpy.context.active_object); sail.name = f"{name}_sail"
    for p in sail.data.polygons:
        p.use_smooth = False
    sail.scale = (1.6, 2.2, 1)
    sail.rotation_euler = (0, math.pi / 2 - 0.35, rot)
    sail.data.materials.append(M)
    solid_paint(sail, (0.96, 0.95, 0.92))

# ---------- layout ----------
yc = island("Center", 0, 0, 5.5, 6.0, seed=1.0)
yr = island("Right", 7.5, 2.0, 4.2, 8.5, seed=2.0)
yl = island("Left", -6.5, -1.0, 4.2, 5.0, seed=3.0)
yf = island("Beach", -1.5, -6.5, 4.5, 2.0, sand=True, seed=4.0)
ym = island("Mid", 4.5, -5.0, 3.2, 3.0, sand=True, seed=5.0)
island("Back", -3.0, 5.5, 4.0, 6.5, seed=6.0)
island("Far1", -16, 11, 2.2, 4.0, seed=7.0)
island("Far2", 15, 13, 2.6, 5.0, seed=8.0)

# tonjolan batu di tebing
for i, (bx, by, bz, bs) in enumerate([
        (5.0, 1.5, 4.0, 1.1), (-4.5, 3.0, 3.5, 0.9), (9.5, 4.5, 5.5, 1.0),
        (-9.5, -2.5, 3.0, 0.8), (2.0, -8.5, 1.2, 0.7)]):
    o = rock_lump(bx, by, bz, bs, seed=20 + i)
    o.name = f"Lump{i}"

# cluster pohon (2-3 gerombol + ruang kosong)
ti = 0
ti = scatter_cluster(-1.0, -0.5, yc, 4, 2.6, ti, flowers_n=2)   # gerombol tengah
ti = scatter_cluster(-7.0, -1.0, yl, 3, 2.2, ti, flowers_n=4)   # gerombol kiri (dekat hut)
ti = scatter_cluster(7.0, 2.5, yr, 3, 2.0, ti, flowers_n=1)    # gerombol mercusuar
# palem tunggal di pantai
tree(-2.5, -6.5, yf, s=1.25, idx=ti, lean=0.06); ti += 1
tree(4.5, -5.5, ym, s=1.05, idx=ti, lean=0.09); ti += 1

lighthouse(7.5, 1.0, yr - 0.8)
hut("HutLeft", -7.5, 2.0, yl)
bridge("BridgeR", 2.5, 1.0, yc, 5.2, 2.0, yr - 0.2)
bridge("BridgeL", -3.5, 0.0, yc - 0.2, -4.8, -0.5, yl)
bridge("BridgeF", -4.8, -3.5, yl - 0.5, -4.0, -5.0, yf + 0.4)
boat("Boat", -12, -10, rot=0.7)

# tangga batu sisi tengah
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.5 + i * 0.55, 3.8, yc - 0.4 - i * 0.55))
    st = link(bpy.context.active_object); st.name = f"Stairs{i}"
    for p in st.data.polygons:
        p.use_smooth = False
    st.scale = (0.9, 1.2, 0.35)
    st.data.materials.append(M)
    solid_paint(st, (0.55, 0.58, 0.62))

# sun + kamera
bpy.ops.object.light_add(type="SUN", location=(25, -15, 35))
sun = bpy.context.active_object; sun.name = "Sun"; sun.data.energy = 2.0
bpy.ops.object.camera_add(location=(34, -38, 28))
cam = bpy.context.active_object; cam.name = "DioramaCam"
import mathutils
d = mathutils.Vector((0, 0, 3.5)) - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

bpy.ops.wm.save_as_mainfile(
    filepath=r"D:\ObsidianVault\The Abyssal Archive\sunlit-shores-clone\blender\sunlit_shores_v3.blend")

result = {"built": True, "objects": len(coll.objects)}
