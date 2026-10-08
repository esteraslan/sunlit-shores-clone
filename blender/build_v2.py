"""Sunlit Shores v2 — bangun di Blender: smooth-shaded, organik, siap export GLB.
Dijalankan via bridge. Tanpa sea (air dari Three.js)."""
import bpy
import math
import random

random.seed(7)

# --- bersihkan scene ---
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, rgb, rough=0.9):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
    return m

M_GRASS = mat("M_Grass", (0.45, 0.72, 0.22))
M_GRASS2 = mat("M_Grass2", (0.38, 0.62, 0.20))
M_ROCK = mat("M_Rock", (0.47, 0.53, 0.60))
M_SAND = mat("M_Sand", (0.94, 0.85, 0.58))
M_WOOD = mat("M_Wood", (0.50, 0.35, 0.20))
M_LEAF = mat("M_Leaf", (0.25, 0.60, 0.22))
M_RED = mat("M_Red", (0.85, 0.24, 0.25))
M_WHITE = mat("M_White", (0.96, 0.95, 0.92))

coll = bpy.data.collections.new("SunlitV2")
bpy.context.scene.collection.children.link(coll)

def link(o):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    return o

def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o

def flat(o):
    for p in o.data.polygons:
        p.use_smooth = False
    return o

def island(name, x, y, r=4.0, h=5.0, sand=False):
    top_mat = M_SAND if sand else M_GRASS
    # batu: taper melebar ke bawah + noise organik ringan
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=1, depth=1, location=(x, y, h / 2))
    rock = smooth(link(bpy.context.active_object))
    rock.name = f"{name}_rock"
    for v in rock.data.vertices:
        t = v.co.z + 0.5  # 0 bawah .. 1 atas
        s = (r * 0.92) * t + (r * 1.18) * (1 - t)
        wob = 1.0 + 0.06 * math.sin(v.co.x * 5.0 + x) * math.cos(v.co.y * 5.0 + y)
        v.co.x *= s * wob
        v.co.y *= s * wob
    rock.data.materials.append(M_ROCK)
    # topi rumput/pasir
    cap_h = 0.7
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=1, depth=1, location=(x, y, h + cap_h / 2))
    cap = smooth(link(bpy.context.active_object))
    cap.name = f"{name}_cap"
    for v in cap.data.vertices:
        t = v.co.z + 0.5
        s = r * (1.0 * t + 0.96 * (1 - t))
        v.co.x *= s
        v.co.y *= s
    cap.data.materials.append(top_mat)
    # rim bevel (torus) agar tepian membulat
    bpy.ops.mesh.primitive_torus_add(major_radius=r * 0.99, minor_radius=cap_h / 2,
                                     major_segments=28, minor_segments=12,
                                     location=(x, y, h + cap_h / 2))
    rim = smooth(link(bpy.context.active_object))
    rim.name = f"{name}_rim"
    rim.data.materials.append(top_mat)
    return h + cap_h

def palm(x, y, z, s=1.0, idx=0):
    # batang melengkung: 4 segmen silinder offset
    for i in range(4):
        t = i / 3
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8, radius=0.16 * s * (1 - t * 0.25), depth=0.8 * s,
            location=(x + t * t * 0.5 * s, y, z + (i + 0.5) * 0.8 * s))
        seg = smooth(link(bpy.context.active_object))
        seg.name = f"Palm{idx}_trunk{i}"
        seg.rotation_euler = (0, -0.12, 0)
        seg.data.materials.append(M_WOOD)
    topx = x + 0.5 * s
    topz = z + 3.2 * s
    for i in range(6):
        ang = i / 6 * math.pi * 2
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.7 * s,
                                             location=(topx + math.cos(ang) * 0.8 * s,
                                                       y + math.sin(ang) * 0.8 * s,
                                                       topz - 0.15 * s))
        leaf = smooth(link(bpy.context.active_object))
        leaf.name = f"Palm{idx}_leaf{i}"
        leaf.scale = (1.0, 1.6, 0.28)
        leaf.rotation_euler = (0.35, 0, -ang)
        leaf.data.materials.append(M_LEAF if i % 2 == 0 else M_GRASS2)

def lighthouse(x, y, z):
    parts = [
        (1.5, 1.6, 1.2, M_WHITE, 0.6),
        (1.3, 1.5, 1.8, M_RED, 2.1),
        (1.1, 1.3, 1.8, M_WHITE, 3.9),
        (0.95, 1.1, 1.4, M_RED, 5.5),
    ]
    for r1, r2, h, m, lz in parts:
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=1, depth=1,
                                            location=(x, y, z + lz))
        o = smooth(link(bpy.context.active_object))
        for v in o.data.vertices:
            t = v.co.z + 0.5
            s = r1 * t + r2 * (1 - t)
            v.co.x *= s
            v.co.y *= s
        o.scale.z = h
        o.data.materials.append(m)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0,
                                         location=(x, y, z + 6.9))
    dome = smooth(link(bpy.context.active_object))
    dome.name = "LH_dome"
    dome.scale = (1.0, 1.0, 1.3)
    dome.data.materials.append(M_ROCK)

def hut(name, x, y, z, rgb=(0.85, 0.45, 0.22)):
    m = mat(f"M_{name}", rgb)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 0.75))
    base = flat(link(bpy.context.active_object))
    base.name = f"{name}_base"
    base.scale = (2.0, 1.6, 1.5)
    base.data.materials.append(m)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.7, depth=1.2,
                                    location=(x, y, z + 2.1))
    roof = flat(link(bpy.context.active_object))
    roof.name = f"{name}_roof"
    roof.rotation_euler = (0, 0, math.pi / 4)
    roof.data.materials.append(M_WOOD)

def bridge(name, ax, ay, az, bx, by, bz):
    import mathutils
    a = mathutils.Vector((ax, ay, az))
    b = mathutils.Vector((bx, by, bz))
    n = max(3, int((b - a).length / 0.45))
    for i in range(n):
        t = i / (n - 1)
        p = a.lerp(b, t)
        p.z += math.sin(t * math.pi) * 0.25
        bpy.ops.mesh.primitive_cube_add(size=1, location=(p.x, p.y, p.z))
        plank = flat(link(bpy.context.active_object))
        plank.name = f"{name}_plank{i}"
        plank.scale = (0.28, 1.3, 0.12)
        plank.rotation_euler = (0, 0, math.atan2(by - ay, bx - ax) + math.pi / 2)

def boat(name, x, y, rot=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=8, radius=1,
                                         location=(x, y, 0.5))
    hull = smooth(link(bpy.context.active_object))
    hull.name = f"{name}_hull"
    hull.scale = (1.0, 2.0, 0.55)
    for v in hull.data.vertices:
        if v.co.z < -0.2:
            v.co.z = -0.2  # ratakan dasar
    hull.rotation_euler = (0, 0, rot)
    hull.data.materials.append(M_WOOD)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.07, depth=3.4,
                                        location=(x, y, 2.2))
    mast = smooth(link(bpy.context.active_object))
    mast.name = f"{name}_mast"
    mast.data.materials.append(M_WOOD)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x + 0.9, y, 2.4))
    sail = flat(link(bpy.context.active_object))
    sail.name = f"{name}_sail"
    sail.scale = (1.6, 2.2, 1)
    sail.rotation_euler = (0, math.pi / 2 - 0.35, rot)
    sail.data.materials.append(M_WHITE)

# --- layout (Blender: x kanan, y depan) ---
yc = island("Center", 0, 0, 5.5, 6.0)
yr = island("Right", 7.5, 2.0, 4.5, 8.5)
yl = island("Left", -6.5, -1.0, 4.5, 5.0)
yf = island("Beach", -1.5, -6.5, 4.5, 2.0, sand=True)
ym = island("Mid", 4.5, -5.0, 3.5, 3.0, sand=True)
island("Back", -3.0, 5.0, 4.0, 6.5)
island("Far1", -16, 12, 2.2, 4.0)
island("Far2", 15, 14, 2.6, 5.0)

lighthouse(7.5, 1.0, yr - 0.7)
palm(0, -1.5, yc, 1.2, 1); palm(2.5, 1.5, yc, 0.9, 2)
palm(7.5, 0.0, yr, 1.1, 3); palm(9.5, 2.5, yr, 0.85, 4)
palm(-6, 0.0, yl, 1.0, 5); palm(-8, -2.0, yl, 0.85, 6)
palm(-2, -6.0, yf, 1.3, 7); palm(1, -8.0, yf, 1.0, 8); palm(4, -5.0, ym, 1.1, 9)
hut("HutLeft", -7.0, 2.5, yl)
bridge("BridgeR", 2.5, 1.0, yc, 5.0, 2.0, yr - 0.2)
bridge("BridgeL", -3.5, 0.0, yc - 0.2, -4.5, -0.5, yl)
bridge("BridgeF", -4.5, -3.5, yl - 0.5, -4.0, -4.5, yf + 0.4)
boat("Boat", -12, -10, rot=0.7)

# sun + kamera
bpy.ops.object.light_add(type="SUN", location=(25, -15, 35))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 2.0
bpy.ops.object.camera_add(location=(30, -34, 26))
cam = bpy.context.active_object
cam.name = "DioramaCam"
import mathutils
d = mathutils.Vector((0, 0, 2.5)) - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

bpy.ops.wm.save_as_mainfile(
    filepath=r"D:\ObsidianVault\The Abyssal Archive\sunlit-shores-clone\blender\sunlit_shores_v2.blend")

result = {"built": True, "objects": len(coll.objects)}
