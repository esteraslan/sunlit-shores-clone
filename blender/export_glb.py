"""Export koleksi SunlitShores ke GLB untuk Three.js. Via bridge."""
import bpy

# hanya export koleksi SunlitShores: hide yang lain dari export via select
bpy.ops.object.select_all(action="DESELECT")
coll = bpy.data.collections.get("SunlitShores")
for o in coll.objects:
    try:
        o.select_set(True)
    except Exception:
        pass

out = r"D:\ObsidianVault\The Abyssal Archive\sunlit-shores-clone\public\sunlit_shores.glb"
bpy.ops.export_scene.gltf(
    filepath=out,
    export_format="GLB",
    use_selection=True,
    export_materials="EXPORT",
)

import os
result = {"exported": out, "bytes": os.path.getsize(out)}
