"""Import a generated GLB into a clean .blend for further work (retopo, rig, texture fixes).

    blender -b --factory-startup --python blender/import_glb.py -- <in.glb> <out.blend> --name <name>

What it does: imports the GLB, names the mesh object `<Name>` (CamelCase, like the game repo's masters), applies
transforms, puts the origin at the feet in the middle (Z = 0 is the floor), shades smooth, reports triangles,
bounding box and textures, and saves the blend with textures packed. It never decimates: the game LOD is made
later in the game repo (`model_pipeline.py lod`). Axes follow glTF import: the model faces -Y in Blender.
"""

import os
import sys

import bpy
from mathutils import Vector


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, dst = argv[0], argv[1]
    name = argv[argv.index("--name") + 1] if "--name" in argv else os.path.splitext(os.path.basename(src))[0]
    camel = "".join(w.capitalize() for w in name.split("_"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        sys.exit("no mesh in " + src)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name, ob.data.name = camel, camel
    ob.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for p in ob.data.polygons:
        p.use_smooth = True
    corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    bpy.context.scene.cursor.location = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    ob.location = (0, 0, 0)
    bpy.context.scene.cursor.location = (0, 0, 0)
    for img in bpy.data.images:
        if img.source == "FILE" and img.filepath:
            img.pack()
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    size = hi - lo
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=dst)
    print("import ok: %s, %d tris, %.2f x %.2f x %.2f m, textures %s -> %s" % (
        camel, tris, size.x, size.y, size.z, [i.name for i in bpy.data.images], dst))


main()
