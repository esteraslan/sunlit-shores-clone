"""Fix: tambah laut + arahkan kamera ke tengah. Via bridge."""
import bpy
import mathutils

# --- laut ---
sea_mat = bpy.data.materials.get("M_Sea")
if not sea_mat:
    sea_mat = bpy.data.materials.new("M_Sea")
    sea_mat.use_nodes = True
    bsdf = sea_mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.18, 0.62, 0.85, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.4

sea = bpy.data.objects.get("Sea")
if not sea:
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
    sea = bpy.context.active_object
    sea.name = "Sea"
    for c in list(sea.users_collection):
        c.objects.unlink(sea)
    bpy.context.scene.collection.children["SunlitShores"].objects.link(sea)
sea.data.materials.clear()
sea.data.materials.append(sea_mat)

# dangkal terang di tengah
sh = bpy.data.objects.get("Shallow")
if not sh:
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=26, depth=0.1, location=(0, 0, 0.05))
    sh = bpy.context.active_object
    sh.name = "Shallow"
    for c in list(sh.users_collection):
        c.objects.unlink(sh)
    bpy.context.scene.collection.children["SunlitShores"].objects.link(sh)
shm = bpy.data.materials.get("M_Shallow") or bpy.data.materials.new("M_Shallow")
shm.use_nodes = True
shm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.56, 0.91, 0.87, 1.0)
sh.data.materials.clear()
sh.data.materials.append(shm)

# --- kamera bidik tengah ---
cam = bpy.data.objects.get("DioramaCam")
target = mathutils.Vector((0, 0, 2.5))
cam.location = mathutils.Vector((20, -24, 18))
d = target - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

result = {"fixed": True, "cam_rot": [round(float(a), 3) for a in cam.rotation_euler]}
