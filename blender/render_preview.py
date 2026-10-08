"""Render preview EEVEE dari DioramaCam. Dijalankan via bridge (deferred)."""
import bpy
import os
import time

out = r"D:\ObsidianVault\The Abyssal Archive\sunlit-shores-clone\blender\preview.png"

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = out
# cepat untuk preview
if hasattr(scene.eevee, "taa_render_samples"):
    scene.eevee.taa_render_samples = 16

# world: langit biru agar mirip laut game
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.45, 0.75, 0.95, 1.0)
    bg.inputs["Strength"].default_value = 1.0
scene.world = world

cam = bpy.data.objects.get("DioramaCam")
if cam:
    scene.camera = cam

if os.path.exists(out):
    os.remove(out)

bpy.ops.render.render("INVOKE_DEFAULT", animation=False, write_still=True)

_state = {"size": -1, "stable": 0}

def check_is_finished():
    if not os.path.exists(out):
        return None
    sz = os.path.getsize(out)
    if sz == _state["size"] and sz > 0:
        _state["stable"] += 1
    else:
        _state["size"] = sz
        _state["stable"] = 0
    if _state["stable"] >= 8:
        return {"render": out, "bytes": sz}
    return None
