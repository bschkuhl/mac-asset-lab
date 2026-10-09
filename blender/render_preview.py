"""Render review images of a .blend: front, front34, left, back, right (orthographic, neutral grey, two suns).

    blender -b <file.blend> --factory-startup --python blender/render_preview.py -- <out_dir>

Writes <out_dir>/preview_<view>.png (768 px). Uses the "Standard" view transform: Blender's default AgX desaturates
the bright, flat colors of the generated textures. Axes follow glTF import: the model faces -Y in Blender.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

# camera angle around Z; "left" = the model's left side toward the camera (styles/_common.json convention)
VIEWS = (("front", -90), ("front34", -45), ("left", 0), ("back", 90), ("right", 180))


def main():
    out_dir = sys.argv[sys.argv.index("--") + 1]
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    meshes = [o for o in scene.objects if o.type == "MESH"]
    if not meshes:
        sys.exit("no mesh in " + bpy.data.filepath)
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center, size = (lo + hi) / 2, max(hi - lo)

    for o in [o for o in scene.objects if o.type in ("CAMERA", "LIGHT")]:
        bpy.data.objects.remove(o)
    cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = size * 1.25
    cam.data.clip_start, cam.data.clip_end = size * 0.01, size * 10
    scene.collection.objects.link(cam)
    scene.camera = cam
    target = bpy.data.objects.new("PreviewTarget", None)
    target.location = center
    scene.collection.objects.link(target)
    cam.constraints.new("TRACK_TO").target = target
    for name, rot, energy in (("Key", (50, 0, 30), 4.0), ("Fill", (60, 0, 210), 1.5)):
        sun = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        sun.data.energy = energy
        sun.rotation_euler = [math.radians(a) for a in rot]
        scene.collection.objects.link(sun)

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.85, 0.85, 0.85, 1)
    bg.inputs[1].default_value = 0.6

    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.image_settings.file_format = "PNG"

    dist = size * 3
    for view, angle in VIEWS:
        a = math.radians(angle)
        cam.location = center + Vector((math.cos(a) * dist, math.sin(a) * dist, size * 0.15))
        scene.render.filepath = os.path.join(out_dir, f"preview_{view}.png")
        bpy.ops.render.render(write_still=True)
    print("preview ok: %d views -> %s" % (len(VIEWS), out_dir))


main()
