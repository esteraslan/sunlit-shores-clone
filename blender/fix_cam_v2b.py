"""Naikkan bidikan kamera agar puncak mercusuar masuk frame. Via bridge."""
import bpy
import mathutils

cam = bpy.data.objects.get("DioramaCam")
target = mathutils.Vector((0, 0, 3.5))
d = target - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
bpy.ops.wm.save_as_mainfile()
result = {"ok": True}
