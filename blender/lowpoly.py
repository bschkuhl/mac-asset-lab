"""Make a game-ready low-poly copy of an imported model and bake its colors onto it.

    blender -b <name>.blend --factory-startup --python blender/lowpoly.py -- <out.blend> <out.glb> --faces 1500
            [--size 2048]

Decimates a copy of the mesh to about --faces triangles, gives it fresh UVs and transfers the base color of the
detailed mesh onto it: every texel takes the color of the nearest point on the detailed surface. (Ray baking misses
or hits the wrong side once heavy decimation has moved the surface.) Makes the material matte (roughness 1,
metallic 0) and shades it flat. The detailed mesh is dropped from the result; the input .blend stays untouched.
Writes the low-poly .blend and a .glb for the game engine. Small details such as eyes survive because they live in
the texture.
"""

import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def base_color_image(ob):
    """(pixels as h x w x 4 float array, uv layer name) of the image feeding the Base Color of ob's material."""
    mat = ob.active_material
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if mat and mat.use_nodes else None
    links = bsdf.inputs["Base Color"].links if bsdf else []
    img = getattr(links[0].from_node, "image", None) if links else None
    if img is None:
        sys.exit(f"{ob.name}: no image texture on the Base Color of its material; nothing to transfer")
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(h, w, 4), ob.data.uv_layers.active.name


def triangles(me, uv_name):
    """Per triangle: vertex positions (n, 3, 3) and UVs (n, 3, 2)."""
    me.calc_loop_triangles()
    tris = me.loop_triangles
    loops = np.empty(len(tris) * 3, np.int32)
    tris.foreach_get("loops", loops)
    verts = np.empty(len(tris) * 3, np.int32)
    tris.foreach_get("vertices", verts)
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    uv = np.empty(len(me.loops) * 2, np.float32)
    me.uv_layers[uv_name].data.foreach_get("uv", uv)
    return co.reshape(-1, 3)[verts].reshape(-1, 3, 3), uv.reshape(-1, 2)[loops].reshape(-1, 3, 2)


def barycentric(p, a, b, c):
    """Barycentric weights of points p (n, d) in triangles (n, d) a, b, c."""
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    den[den == 0] = 1e-12
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return np.stack([1 - v - w, v, w], 1)


def bilinear(img, uv):
    """Sample img (h, w, 4) at uv (n, 2) in 0..1 with bilinear filtering."""
    h, w = img.shape[:2]
    x = (uv[:, 0] % 1) * w - 0.5
    y = (uv[:, 1] % 1) * h - 0.5
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    x0, x1 = x0.clip(0, w - 1), (x0 + 1).clip(0, w - 1)
    y0, y1 = y0.clip(0, h - 1), (y0 + 1).clip(0, h - 1)
    top = img[y0, x0] * (1 - fx) + img[y0, x1] * fx
    bottom = img[y1, x0] * (1 - fx) + img[y1, x1] * fx
    return top * (1 - fy) + bottom * fy


def transfer_colors(high, low, size):
    """Texture (size x size x 4) for low's UVs: each texel gets the color of the nearest point on high."""
    src, src_uv_name = base_color_image(high)
    sh, sw = src.shape[:2]
    h_pos, h_uv = triangles(high.data, src_uv_name)
    bvh = BVHTree.FromPolygons(h_pos.reshape(-1, 3).tolist(), np.arange(len(h_pos) * 3).reshape(-1, 3).tolist())
    l_pos, l_uv = triangles(low.data, low.data.uv_layers.active.name)

    # texel centers covered by each low triangle -> 3D points on the low surface
    pts, idx = [], []
    for t in range(len(l_uv)):
        uv = l_uv[t] * size
        x0, y0 = np.floor(uv.min(0)).astype(int).clip(0, size - 1)
        x1, y1 = np.ceil(uv.max(0)).astype(int).clip(0, size - 1)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        p = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        bc = barycentric(p, *(np.repeat(uv[k][None], len(p), 0) for k in range(3)))
        inside = (bc >= -0.02).all(1)
        if inside.any():
            pts.append(bc[inside] @ l_pos[t])
            idx.append(ys.ravel()[inside] * size + xs.ravel()[inside])
    pts, idx = np.concatenate(pts), np.concatenate(idx)

    # nearest point on the detailed surface -> its UV -> its color
    hit_pos, hit_tri = np.empty((len(pts), 3), np.float32), np.empty(len(pts), np.int64)
    for i, p in enumerate(pts):
        loc, _n, tri, _d = bvh.find_nearest(Vector(p))
        hit_pos[i], hit_tri[i] = loc, tri
    a, b, c = (h_pos[hit_tri, k] for k in range(3))
    bc = barycentric(hit_pos, a, b, c).clip(0, 1)
    bc /= bc.sum(1, keepdims=True)
    bc = bc * 0.8 + 0.2 / 3  # pull toward the triangle's middle: never sample the black gutter between UV islands
    uv = (bc[:, :, None] * h_uv[hit_tri]).sum(1)

    out = np.zeros((size * size, 4), np.float32)
    out[idx] = bilinear(src, uv)
    out[idx, 3] = 1
    out = out.reshape(size, size, 4)
    for _ in range(8):  # grow islands into the gutter so texture filtering never pulls in black
        empty = out[..., 3] == 0
        if not empty.any():
            break
        grown = out.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            shifted = np.roll(out, (dy, dx), (0, 1))
            take = empty & (shifted[..., 3] > 0) & (grown[..., 3] == 0)
            grown[take] = shifted[take]
        out = grown
    out[..., 3] = 1
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    dst_blend, dst_glb = argv[0], argv[1]
    faces = int(argv[argv.index("--faces") + 1])
    size = int(argv[argv.index("--size") + 1]) if "--size" in argv else 2048
    bpy.context.preferences.filepaths.save_version = 0  # no .blend1 backups next to the results
    scene = bpy.context.scene
    high = next(o for o in scene.objects if o.type == "MESH")
    name = high.name
    high.name = name + "_high"
    tris = sum(len(p.vertices) - 2 for p in high.data.polygons)

    low = high.copy()
    low.data = high.data.copy()
    low.name = low.data.name = name
    scene.collection.objects.link(low)
    for o in scene.objects:
        o.select_set(o == low)
    bpy.context.view_layer.objects.active = low
    if tris > faces:
        dec = low.modifiers.new("Decimate", "DECIMATE")
        dec.ratio = faces / tris
        dec.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dec.name)
    bm = bmesh.new()
    bm.from_mesh(low.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(low.data)
    bm.free()
    for p in low.data.polygons:
        p.use_smooth = False

    while low.data.uv_layers:
        low.data.uv_layers.remove(low.data.uv_layers[0])
    low.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
    bpy.ops.object.mode_set(mode="OBJECT")

    img = bpy.data.images.new(name + "_basecolor", size, size)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nodes.active = tex
    low.data.materials.clear()
    low.data.materials.append(mat)

    pixels = transfer_colors(high, low, size)
    img.pixels.foreach_set(pixels.ravel())
    img.pack()

    bpy.data.objects.remove(high)
    scene.view_settings.view_transform = "Standard"
    low_tris = sum(len(p.vertices) - 2 for p in low.data.polygons)
    os.makedirs(os.path.dirname(os.path.abspath(dst_blend)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(dst_glb)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=dst_blend)
    for o in scene.objects:
        o.select_set(o == low)
    bpy.ops.export_scene.gltf(filepath=dst_glb, export_format="GLB", use_selection=True)
    print("lowpoly ok: %s, %d -> %d tris, texture %d px -> %s, %s" % (
        name, tris, low_tris, size, dst_blend, dst_glb))


main()
