"""Perbaiki look: warna saturasi ala game + exposure benar. Via bridge."""
import bpy

PAL = {
    "M_Grass": (0.30, 0.72, 0.28),
    "M_Rock": (0.52, 0.55, 0.65),
    "M_RockDark": (0.36, 0.38, 0.50),
    "M_Sand": (0.96, 0.87, 0.62),
    "M_Leaf": (0.10, 0.55, 0.25),
    "M_Leaf2": (0.22, 0.72, 0.33),
    "M_Sea": (0.04, 0.55, 0.78),
    "M_Shallow": (0.35, 0.85, 0.78),
    "M_Red": (0.85, 0.22, 0.25),
    "M_White": (0.96, 0.95, 0.92),
    "M_HutBeach": (0.88, 0.45, 0.22),
    "M_HutRight": (0.60, 0.35, 0.88),
}
for name, rgb in PAL.items():
    m = bpy.data.materials.get(name)
    if not m:
        continue
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)

sea = bpy.data.materials.get("M_Sea")
if sea:
    bsdf = sea.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Metallic"].default_value = 0.1

# exposure: Standard (bukan AgX) agar warna game punchy
vs = bpy.context.scene.view_settings
try:
    vs.view_transform = "Standard"
except Exception:
    pass
vs.exposure = -0.3

sun = bpy.data.objects.get("Sun")
if sun:
    sun.data.energy = 1.6

# world: biru langit sedikit lebih dalam, strength turun
world = bpy.context.scene.world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.35, 0.68, 0.94, 1.0)
bg.inputs["Strength"].default_value = 0.7

# ambient occlusion untuk kedalaman
try:
    bpy.context.scene.eevee.use_gtao = True
except Exception:
    pass

bpy.ops.wm.save_as_mainfile()

result = {"look": "fixed", "view_transform": vs.view_transform}
