"""Dijalankan DI DALAM Blender via bridge (bukan bpy langsung).
Membangun diorama Sunlit Shores: 7 pulau, lighthouse, palm, hut, bridge, boat.
Akhiri dengan result = {...} (wajib dict, JSON-serializable)."""
import bpy
import math

# --- bersihkan default ---
for o in list(bpy.data.objects):
    if o.type in {"MESH", "LIGHT", "CAMERA"} and o.name in {"Cube", "Light", "Camera"}:
        bpy.data.objects.remove(o, do_unlink=True)

def mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.9
    return m

M_GRASS = mat("M_Grass", (0.44, 0.79, 0.37))
M_ROCK = mat("M_Rock", (0.55, 0.56, 0.64))
M_DARK = mat("M_RockDark", (0.42, 0.43, 0.52))
M_SAND = mat("M_Sand", (0.95, 0.89, 0.70))
M_WOOD = mat("M_Wood", (0.61, 0.42, 0.24))
M_TRUNK = mat("M_Trunk", (0.48, 0.32, 0.19))
M_LEAF = mat("M_Leaf", (0.18, 0.62, 0.36))
M_LEAF2 = mat("M_Leaf2", (0.27, 0.75, 0.44))
M_WHITE = mat("M_White", (1, 1, 1))
M_RED = mat("M_Red", (0.88, 0.29, 0.29))

coll = bpy.data.collections.get("SunlitShores") or bpy.data.collections.new("SunlitShores")
if coll.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(coll)

def link(o):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    return o

def flat(o):
    for p in o.data.polygons:
        p.use_smooth = False
    return o

def cyl(name, r_top, r_bot, h, loc, material, verts=7):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r_top, depth=h, location=loc)
    o = link(bpy.context.active_object)
    o.name = name
    # taper: scale bottom verts
    import bmesh
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    zmin = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        if abs(v.co.z - zmin) < 1e-4 and r_top > 0:
            v.co.x *= r_bot / r_top
            v.co.y *= r_bot / r_top
    bm.to_mesh(me)
    bm.free()
    me.update()
    o.data.materials.clear()
    o.data.materials.append(material)
    return flat(o)

def box(name, dims, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = link(bpy.context.active_object)
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.clear()
    o.data.materials.append(material)
    return flat(o)

tops = {}

def island(name, x, z, r=4.0, h=4.0, sand=False):
    cyl(f"{name}_rock", r * 0.92, r * 0.68, h, (x, 0, h / 2), M_ROCK)
    cyl(f"{name}_grass", r, r * 0.92, 0.9, (x, 0, h + 0.35), M_GRASS)
    if sand:
        cyl(f"{name}_sand", r * 1.3, r * 1.4, 0.5, (x, 0, 0.25), M_SAND, verts=9)
    box(f"{name}_stairs", (1.2, 1.6, h), (x + r * 0.55, 0, h / 2), M_DARK)
    tops[name] = h + 0.8
    return tops[name]

def palm(x, z, y, s=1.0, idx=0):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18 * s, depth=2.2 * s,
                                        location=(x, z, y + 1.1 * s))
    t = link(bpy.context.active_object)
    t.name = f"Palm_{idx}_trunk"
    t.data.materials.clear(); t.data.materials.append(M_TRUNK)
    flat(t)
    for i in range(6):
        ang = i / 6 * math.pi * 2
        lx = x + math.cos(ang) * 0.7 * s
        lz = z + math.sin(ang) * 0.7 * s
        bpy.ops.mesh.primitive_cone_add(radius1=0.32 * s, depth=1.8 * s,
                                        location=(lx, lz, y + 2.3 * s))
        leaf = link(bpy.context.active_object)
        leaf.name = f"Palm_{idx}_leaf_{i}"
        leaf.rotation_euler = (0, math.pi / 2.4, ang)
        leaf.data.materials.clear()
        leaf.data.materials.append(M_LEAF if i % 2 else M_LEAF2)
        flat(leaf)

def lighthouse(x, z, y):
    cyl("LH_base", 1.4, 1.5, 1.2, (x, z, y + 0.6), M_ROCK, verts=8)
    cyl("LH_w1", 0.95, 1.0, 1.4, (x, z, y + 1.9), M_WHITE, verts=8)
    cyl("LH_red", 0.8, 0.85, 1.2, (x, z, y + 3.0), M_RED, verts=8)
    cyl("LH_w2", 0.65, 0.7, 1.0, (x, z, y + 4.0), M_WHITE, verts=8)
    bpy.ops.mesh.primitive_cone_add(radius1=0.7, depth=0.7, location=(x, z, y + 5.0))
    roof = link(bpy.context.active_object); roof.name = "LH_roof"
    roof.data.materials.clear(); roof.data.materials.append(M_RED)
    flat(roof)

def hut(name, x, z, y, rgb=(0.88, 0.47, 0.25)):
    m = mat(f"M_{name}", rgb)
    box(f"{name}_base", (1.8, 1.6, 1.2), (x, z, y + 0.6), m)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.6, depth=1.0,
                                    location=(x, z, y + 1.7))
    roof = link(bpy.context.active_object); roof.name = f"{name}_roof"
    roof.rotation_euler = (0, 0, math.pi / 4)
    roof.data.materials.clear(); roof.data.materials.append(M_TRUNK)
    flat(roof)

def bridge(name, ax, az, ay, bx, bz, by):
    import mathutils
    a = mathutils.Vector((ax, az, ay)); b = mathutils.Vector((bx, bz, by))
    mid = (a + b) / 2
    length = (b - a).length
    box(f"{name}_deck", (length, 1.2, 0.18), (mid.x, mid.y, mid.z), M_WOOD)
    deck = bpy.data.objects[f"{name}_deck"]
    deck.rotation_euler = (0, 0, math.atan2(b.y - a.y, b.x - a.x))
    n = max(2, int(length / 0.7))
    for i in range(n + 1):
        t = i / n
        px, pz, py = a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t
        for side in (-0.55, 0.55):
            box(f"{name}_post_{i}_{side}", (0.12, 0.12, 0.7), (px, pz + side, py + 0.4), M_WOOD)

def boat(name, x, z, rot=0.0, sail=False):
    box(f"{name}_hull", (1.6, 0.7, 0.5), (x, z, 0.3), M_TRUNK)
    bpy.data.objects[f"{name}_hull"].rotation_euler = (0, 0, rot)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=1.8, location=(x, z, 1.2))
    mast = link(bpy.context.active_object); mast.name = f"{name}_mast"
    mast.data.materials.clear(); mast.data.materials.append(M_WOOD)
    if sail:
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(x + 0.5, z, 1.3))
        s = link(bpy.context.active_object); s.name = f"{name}_sail"
        s.dimensions = (0.9, 0.02, 1.1)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        s.data.materials.clear(); s.data.materials.append(M_WHITE)

# --- layout (sumbu Blender: x kanan, y depan; peta dari three.js x->x, z->-y) ---
yc = island("Center", 0, 0, 5.5, 5.0)
yl = island("Left", -6.5, 1, 3.6, 3.6)
yr = island("Right", 6.2, -0.5, 3.8, 4.2)
yb = island("Beach", 0.5, -7.5, 4.5, 1.6, sand=True)
island("Far1", -14, 10, 1.6, 2.5)
island("Far2", 12, 9, 1.8, 3.0)
island("Far3", -11, -9, 1.4, 2.2)

lighthouse(0, 1, yc - 0.4)
palm(-1.5, 0.5, yl, 1.0, 1); palm(-7.2, -0.5, yl, 0.9, 2)
palm(6.0, 0.0, yr, 1.0, 3); palm(7.2, -1.2, yr, 0.85, 4)
palm(-2.0, -6.5, yb, 1.0, 5); palm(2.2, -8.0, yb, 1.1, 6); palm(0.0, -9.2, yb, 0.9, 7)
palm(-6.0, -2.0, yc, 0.9, 8); palm(5.0, -2.5, yc, 1.0, 9)
hut("HutBeach", -1.5, -7.8, yb)
hut("HutRight", 8.0, 1.0, yr, rgb=(0.61, 0.36, 0.90))
bridge("BridgeL", -3.2, 0.5, yl, -1.2, 0.5, yc - 0.3)
bridge("BridgeR", 1.5, -0.8, yc - 0.3, 3.2, -0.8, yr - 0.2)
bridge("BridgeB", -0.5, -3.5, 2.2, 0.2, -5.2, yb + 0.4)
boat("Sailboat", 14, 4, rot=0.6, sail=True)
boat("Rowboat", 6, -9.5, rot=-0.5, sail=False)

# sun + kamera diorama
bpy.ops.object.light_add(type="SUN", location=(20, -10, 30))
sun = bpy.context.active_object; sun.name = "Sun"; sun.data.energy = 3.0
bpy.ops.object.camera_add(location=(18, -22, 16),
                          rotation=(math.radians(60), 0, 0))
cam = bpy.context.active_object; cam.name = "DioramaCam"
bpy.context.scene.camera = cam

result = {
    "built": True,
    "objects_in_collection": len(coll.objects),
    "tops": tops,
}
