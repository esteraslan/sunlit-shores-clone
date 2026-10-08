import bpy
import math
import random

# Bersihkan scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Setup Koleksi
coll = bpy.data.collections.get("TinyTrails")
if not coll:
    coll = bpy.data.collections.new("TinyTrails")
    bpy.context.scene.collection.children.link(coll)

# Fungsi Material untuk Low-Poly (Solid, Flat)
def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))

def make_mat(name, hex_color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    rgb = hex_to_rgb(hex_color)
    # Konversi sRGB ke Linear untuk viewport/render Blender
    linear = [pow(c, 2.2) for c in rgb] + [1.0]
    bsdf.inputs["Base Color"].default_value = linear
    bsdf.inputs["Roughness"].default_value = 0.95
    return m

M_GRASS = make_mat("M_Grass", "#8cd639")
M_ROCK = make_mat("M_Rock", "#858e96")
M_SAND = make_mat("M_Sand", "#ebdca5")
M_WOOD = make_mat("M_Wood", "#9c6535")
M_LEAF = make_mat("M_Leaf", "#5dbf34")
M_RED = make_mat("M_Red", "#d94343")
M_WHITE = make_mat("M_White", "#f5f5f5")

def link(obj):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    # Pastikan Flat Shading
    for p in obj.data.polygons:
        p.use_smooth = False
    return obj

# 1. GENERATOR PULAU (Tapered)
def add_island(x, y, z, r, h, is_sand=False):
    # Base Batu (Lebar di bawah, sempit di atas)
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=1, depth=1, location=(x, y, z + h/2))
    rock = link(bpy.context.active_object)
    rock.name = "Rock"
    for v in rock.data.vertices:
        if v.co.z > 0:
            v.co.x *= r * 0.9
            v.co.y *= r * 0.9
        else:
            v.co.x *= r * 1.2 # Taper bawah
            v.co.y *= r * 1.2
    rock.scale.z = h
    rock.data.materials.append(M_ROCK)

    # Topi Rumput / Pasir (Tebal, sedikit melebar)
    cap_h = 0.6
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=1, depth=1, location=(x, y, z + h + cap_h/2))
    cap = link(bpy.context.active_object)
    cap.name = "GrassCap" if not is_sand else "SandCap"
    for v in cap.data.vertices:
        if v.co.z > 0:
            v.co.x *= r * 1.0
            v.co.y *= r * 1.0
        else:
            v.co.x *= r * 0.95
            v.co.y *= r * 0.95
    cap.scale.z = cap_h
    cap.data.materials.append(M_SAND if is_sand else M_GRASS)
    return z + h + cap_h

# Layout Utama (Lebih padat, menumpuk organik)
hC = add_island(0, 0, -3, 5, 5)            # Center
hR = add_island(6.5, 2.5, -3, 4, 7.5)      # Kanan (Lighthouse)
hL = add_island(-5.5, 1, -3, 4, 4)         # Kiri (Rumah)
hF = add_island(-1, -5.5, -3, 4.5, 2.5, True) # Depan (Pasir)
hFR = add_island(4.5, -4, -3, 3, 3.5, True)   # Depan Kanan (Pasir)
# Filler penghubung (agar tidak terputus)
add_island(3.5, 1, -3, 3.5, 5.5)
add_island(-3, -3, -3, 3.5, 3.5)

# 2. DETAIL: MERCUSUAR
def add_lh(x, y, z):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=1.2, depth=0.8, location=(x, y, z+0.4))
    base = link(bpy.context.active_object); base.data.materials.append(M_WHITE)
    def ring(r1, r2, dz, lz, mat):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=1, depth=dz, location=(x, y, z+lz))
        r = link(bpy.context.active_object)
        for v in r.data.vertices:
            v.co.x *= r1 if v.co.z > 0 else r2
            v.co.y *= r1 if v.co.z > 0 else r2
        r.data.materials.append(mat)
    ring(1.0, 1.15, 1.5, 1.55, M_RED)
    ring(0.85, 1.0, 1.5, 3.05, M_WHITE)
    ring(0.7, 0.85, 1.5, 4.55, M_RED)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.8, depth=1.2, location=(x, y, z+5.9))
    roof = link(bpy.context.active_object); roof.data.materials.append(M_ROCK)
add_lh(6.5, 2.5, hR)

# 3. POHON PALEM (Low-Poly Elegan)
def add_palm(x, y, z, scale=1.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.15*scale, depth=2.5*scale, location=(x, y, z+1.25*scale))
    trunk = link(bpy.context.active_object)
    trunk.rotation_euler[0] = random.uniform(-0.15, 0.15)
    trunk.rotation_euler[1] = random.uniform(-0.15, 0.15)
    trunk.data.materials.append(M_WOOD)
    for i in range(5):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z + 2.5*scale))
        leaf = link(bpy.context.active_object)
        leaf.scale = (0.4*scale, 1.6*scale, 1)
        # Bikin mirip berlian (diamond shape)
        for v in leaf.data.vertices:
            if v.co.y > 0: v.co.x *= 0.1; v.co.y *= 1.2
            if v.co.y < 0: v.co.x *= 0.2; v.co.y *= 0.1
        ang = (i/5) * math.pi * 2
        leaf.rotation_euler = (math.pi/3, 0, ang)
        leaf.location.x += math.sin(ang)*0.4*scale
        leaf.location.y -= math.cos(ang)*0.4*scale # Blender orientasi Y depan
        leaf.data.materials.append(M_LEAF)
        
add_palm(0, 0, hC, 1.2); add_palm(2, -1, hC, 0.8); add_palm(-1, 2, hC, 1.0)
add_palm(6.5, 0, hR, 1.1)
add_palm(-5.5, 0, hL, 0.9); add_palm(-4.5, 2.5, hL, 1.0)
add_palm(0, -6, hF, 1.3); add_palm(-2.5, -4.5, hF, 1.0)

# 4. JEMBATAN KAYU (Berpapan)
def add_bridge(x1, y1, z1, x2, y2, z2):
    dx = x2 - x1; dy = y2 - y1; dist = math.sqrt(dx**2 + dy**2)
    ang = math.atan2(dy, dx)
    count = int(dist / 0.5)
    for i in range(count):
        t = i / (count - 1) if count > 1 else 0.5
        px = x1 + dx * t; py = y1 + dy * t; pz = z1 + (z2 - z1) * t + math.sin(t * math.pi)*0.3
        bpy.ops.mesh.primitive_cube_add(size=1, location=(px, py, pz))
        plank = link(bpy.context.active_object)
        plank.scale = (0.3, 1.2, 0.1)
        plank.rotation_euler[2] = ang
        plank.data.materials.append(M_WOOD)

add_bridge(2, 1, hC, 4.5, 2, hR-0.2)
add_bridge(-2.5, 0.5, hC, -4, 1, hL-0.2)
add_bridge(-2.5, -3.5, hF, -4, -1, hL-0.5)

# 5. PERAHU (Stylized Boat)
def add_boat(x, y, z, ang):
    # Lambung Perahu
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z+0.3))
    hull = link(bpy.context.active_object)
    hull.scale = (1.8, 0.8, 0.5)
    for v in hull.data.vertices:
        if v.co.z < 0: v.co.x *= 0.6; v.co.y *= 0.6
        if abs(v.co.x) > 0: v.co.y *= 0.5 if v.co.x > 0 else 0.8
    hull.rotation_euler[2] = ang
    hull.data.materials.append(M_WOOD)
    # Tiang
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.06, depth=2, location=(x, y, z+1.5))
    mast = link(bpy.context.active_object); mast.data.materials.append(M_WOOD)
    # Layar
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y-0.2, z+1.5))
    sail = link(bpy.context.active_object)
    sail.scale = (1.2, 1.6, 1); sail.rotation_euler = (math.pi/2, 0, ang + math.pi/6)
    sail.data.materials.append(M_WHITE)
add_boat(-6, -6, 0.1, math.pi/4)

# 6. BATU LONCATAN (Stepping stones)
for _ in range(8):
    x = random.uniform(-1, 3); y = random.uniform(-1, 3)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.2, depth=0.1, location=(x, y, hC))
    s = link(bpy.context.active_object); s.data.materials.append(M_WHITE)

# 7. EXPORT GLB
out = r"D:\ObsidianVault\The Abyssal Archive\sunlit-shores-clone\public\sunlit_shores_pro.glb"
bpy.ops.object.select_all(action='DESELECT')
for o in coll.objects: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_materials="EXPORT")

result = {"status": "ok", "exported": out}
