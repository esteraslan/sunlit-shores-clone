"""Export koleksi SunlitV2 ke GLB. Via bridge."""
import bpy
import os

bpy.ops.object.select_all(action="DESELECT")
for o in bpy.data.collections.get("SunlitV2").objects:
    try:
        o.select_set(True)
    except Exception:
        pass

out = r"D:\ObsidianVault\The Abyssal Archive\sunlit-shores-clone\public\sunlit_shores_v2.glb"
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True,
                           export_materials="EXPORT")
result = {"exported": out, "bytes": os.path.getsize(out)}
