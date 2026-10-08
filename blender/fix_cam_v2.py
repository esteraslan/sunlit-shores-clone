"""Lebarkan framing kamera v2. Via bridge."""
import bpy
import mathutils

cam = bpy.data.objects.get("DioramaCam")
target = mathutils.Vector((0, 0, 2.0))
cam.location = mathutils.Vector((34, -38, 28))
d = target - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
bpy.ops.wm.save_as_mainfile()

result = {"cam": [round(float(v), 1) for v in cam.location]}
