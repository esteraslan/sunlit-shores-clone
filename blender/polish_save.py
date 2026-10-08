"""Polish: kamera mundur + sun lembut + simpan .blend. Via bridge."""
import bpy
import mathutils

sun = bpy.data.objects.get("Sun")
if sun:
    sun.data.energy = 2.0

cam = bpy.data.objects.get("DioramaCam")
target = mathutils.Vector((0, 0, 2.0))
cam.location = mathutils.Vector((27, -31, 22))
d = target - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

blend = r"D:\ObsidianVault\The Abyssal Archive\sunlit-shores-clone\blender\sunlit_shores.blend"
bpy.ops.wm.save_as_mainfile(filepath=blend)

result = {"saved": blend, "cam": [round(float(v), 2) for v in cam.location]}
