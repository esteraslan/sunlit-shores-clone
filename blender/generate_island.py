"""
Sunlit Shores - procedural island generator for Blender 3.6+ / 4.x
Cara pakai:
  blender --background --python generate_island.py -- --out ./sunlit_shores.glb
  atau buka di Blender Text Editor > Run Script, lalu File > Export > glTF.

Ini meniru workflow di screenshot: semua environment dibuat di Blender,
lalu di-load di three.js. Versi three.js di /src/main.js memakai layout
yang SAMA (koordinat disamakan) agar 1:1.
"""
import bpy, math, sys, argparse

def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.materials):
        for x in list(coll):
            try: coll.remove(x)
            except: pass

def mat(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.9
    return m

M_GRASS = mat('Grass', (0.44, 0.79, 0.37))
M_ROCK = mat('Rock', (0.55, 0.56, 0.64))
M_SAND = mat('Sand', (0.95, 0.89, 0.70))
M_WOOD = mat('Wood', (0.61, 0.42, 0.24))
M_TRUNK = mat('Trunk', (0.48, 0.32, 0.19))
M_LEAF = mat('Leaf', (0.18, 0.62, 0.36))
M_WHITE = mat('White', (1, 1, 1))
M_RED = mat('Red', (0.88, 0.29, 0.29))

def cyl(name, r1, r2, h, loc, material, verts=7):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r1, depth=h, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale.z = 1
    # taper atas-bawah manual: scale vertex atas
    o.data.materials.append(material)
    # flat shading low-poly
    for p in o.data.polygons:
        p.use_smooth = False
    return o

def box(name, size, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o

def island(name, x, z, r=4, h=4, sand=False):
    grp = []
    grp.append(cyl(f'{name}_rock', r*0.92, r*0.7, h, (x, z, h/2), M_ROCK))
    grp.append(cyl(f'{name}_grass', r, r*0.92, 0.9, (x, z, h+0.35), M_GRASS))
    if sand:
        grp.append(cyl(f'{name}_sand', r*1.25, r*1.35, 0.5, (x, z, 0.25), M_SAND, verts=9))
    # tangga
    grp.append(box(f'{name}_stairs', (1.2, 1.6, h), (x+r*0.55, z, h/2), M_ROCK))
    return grp

def palm(x, y, z, s=1.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18*s, depth=2.2*s, location=(x, z, y+1.1*s))
    t = bpy.context.active_object; t.data.materials.append(M_TRUNK)
    for i in range(6):
        ang = i/6*math.pi*2
        lx = x + math.cos(ang)*0.7*s
        lz = z + math.sin(ang)*0.7*s
        bpy.ops.mesh.primitive_cone_add(radius1=0.32*s, depth=1.8*s, location=(lx, lz, y+2.3*s))
        leaf = bpy.context.active_object
        leaf.rotation_euler = (0, math.pi/2.4, ang)
        leaf.data.materials.append(M_LEAF)

def lighthouse(x, y, z):
    cyl('LH_base', 1.4, 1.4, 1.2, (x, z, y+0.6), M_ROCK, verts=8)
    cyl('LH_w1', 0.95, 0.95, 1.4, (x, z, y+1.9), M_WHITE, verts=8)
    cyl('LH_r', 0.8, 0.8, 1.2, (x, z, y+3.0), M_RED, verts=8)
    cyl('LH_w2', 0.65, 0.65, 1.0, (x, z, y+4.0), M_WHITE, verts=8)
    bpy.ops.mesh.primitive_cone_add(radius1=0.7, depth=0.7, location=(x, z, y+5.4))
    bpy.context.active_object.data.materials.append(M_RED)

def main():
    clear()
    # layout SAMA dengan src/main.js
    island('Center', 0, 0, 5.5, 5, False)
    island('Left', -6.5, -1, 3.6, 3.6, False)
    island('Right', 6.2, 0.5, 3.8, 4.2, False)
    island('Beach', 0.5, 7.5, 4.5, 1.6, True)
    island('Far1', -14, -10, 1.6, 2.5, False)
    island('Far2', 12, -9, 1.8, 3, False)
    lighthouse(0, 5.4, -1)
    palm(-1.5, 4.4, -0.5); palm(6.0, 5.0, 0); palm(-2, 2.4, 6.5); palm(2.2, 2.4, 8)
    # sun + camera ala diorama
    bpy.ops.object.light_add(type='SUN', location=(20, 10, 30))
    bpy.ops.object.camera_add(location=(18, -22, 16), rotation=(math.radians(60), 0, math.radians(180)))
    print('DONE: islands created. Export manual ke GLB atau via --out')

    argv = sys.argv
    out = None
    if '--' in argv:
        i = argv.index('--')
        if '--out' in argv[i:]:
            out = argv[argv.index('--out')+1]
    if out:
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False)
        print(f'Exported {out}')

if __name__ == '__main__':
    main()
