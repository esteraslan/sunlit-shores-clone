"""Polish v3: Standard transform, exposure, kamera lebar. Via bridge."""
import bpy
import mathutils

vs = bpy.context.scene.view_settings
try:
    vs.view_transform = "Standard"
except Exception:
    pass
vs.exposure = -0.2

sun = bpy.data.objects.get("Sun")
if sun:
    sun.data.energy = 1.8

cam = bpy.data.objects.get("DioramaCam")
cam.location = mathutils.Vector((37, -41, 30))
d = mathutils.Vector((0, 0, 3.0)) - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
bpy.ops.wm.save_as_mainfile()
result = {"polished": True, "vt": vs.view_transform}
