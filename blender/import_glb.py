"""Import a generated GLB into a clean .blend for further work (retopo, rig, texture fixes).

    blender -b --factory-startup --python blender/import_glb.py -- <in.glb> <out.blend> --name <name>
            [--rotate-z 180]

What it does: imports the GLB, names the mesh object `<Name>` (CamelCase, like the game repo's masters), applies
transforms, makes normals point outward, puts the origin at the feet in the middle (Z = 0 is the floor), shades
smooth (flat below 20 000 triangles, to keep low-poly facets), reports triangles, bounding box and textures, sets the
"Standard" view transform and saves the blend with textures packed. It never decimates: the game LOD is made later in
the game repo (`model_pipeline.py lod`). Axes follow glTF import: the model faces -Y in Blender.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

FLAT_BELOW = 20000  # triangles; below this the mesh is shaded flat (low-poly targets go up to 10 000)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, dst = argv[0], argv[1]
    name = argv[argv.index("--name") + 1] if "--name" in argv else os.path.splitext(os.path.basename(src))[0]
    camel = "".join(w.capitalize() for w in name.split("_"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0  # no .blend1 backups next to the results
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
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    if "--rotate-z" in argv:  # e.g. Pixal3D exports the model facing +Y
        angle = math.radians(float(argv[argv.index("--rotate-z") + 1]))
        ob.matrix_world = Matrix.Rotation(angle, 4, "Z") @ ob.matrix_world  # glTF objects use quaternion rotation
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # TRELLIS' simplified meshes are open and partly flipped; game engines cull back faces, so point normals outward
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    smooth = tris >= FLAT_BELOW  # low-poly models keep their facets
    for p in ob.data.polygons:
        p.use_smooth = smooth
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
    # AgX (the default) washes out the flat, saturated colors of the generated textures
    bpy.context.scene.view_settings.view_transform = "Standard"
    size = hi - lo
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=dst)
    print("import ok: %s, %d tris (%s), %.2f x %.2f x %.2f m, textures %s -> %s" % (
        camel, tris, "smooth" if smooth else "flat", size.x, size.y, size.z, [i.name for i in bpy.data.images], dst))


main()
