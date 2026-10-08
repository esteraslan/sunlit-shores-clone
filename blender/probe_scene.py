import bpy
result = {
    "version": ".".join(map(str, bpy.app.version)),
    "objects": len(bpy.data.objects),
    "names": [o.name for o in bpy.data.objects][:20],
    "scene": bpy.context.scene.name,
}
