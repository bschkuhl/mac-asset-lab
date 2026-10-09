"""Offline tests for the preview step, build chaining, pinned TRELLIS ref and export exclusions.
    python3 tests/test_preview.py      BLENDER_TEST=1 python3 tests/test_preview.py   (adds a real Blender render)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LAB)
import pipeline as P  # noqa: E402

VIEWS = ("front", "front34", "left", "back", "right")


def read(*parts):
    with open(os.path.join(LAB, *parts)) as f:
        return f.read()


class Preview(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.object(P, "OUT", self.tmp.name)
        p.start()
        self.addCleanup(p.stop)

    def test_missing_blend_exits(self):
        with mock.patch.object(P.subprocess, "run") as run:
            with self.assertRaises(SystemExit) as cm:
                P.cmd_preview(argparse.Namespace(name="nothing_here"))
        self.assertIn("missing", str(cm.exception.code))
        run.assert_not_called()

    def test_invalid_name_exits(self):
        with self.assertRaises(SystemExit):
            P.cmd_preview(argparse.Namespace(name="Bad Name"))

    def test_blender_command(self):
        d = os.path.join(self.tmp.name, "crate", "blender")
        os.makedirs(d)
        blend = os.path.join(d, "crate.blend")
        open(blend, "w").close()
        with mock.patch.object(P, "blender_exe", return_value="/fake/Blender"), \
                mock.patch.object(P.subprocess, "run") as run:
            P.cmd_preview(argparse.Namespace(name="crate"))
        cmd = run.call_args[0][0]
        self.assertEqual(cmd[0], "/fake/Blender")
        self.assertIn("-b", cmd)
        self.assertEqual(cmd[cmd.index("-b") + 1], blend)
        self.assertIn("--factory-startup", cmd)
        self.assertEqual(cmd[cmd.index("--python") + 1], os.path.join(LAB, "blender", "render_preview.py"))
        self.assertEqual(cmd[cmd.index("--") + 1], os.path.join(self.tmp.name, "crate", "preview"))
        self.assertTrue(run.call_args[1].get("check"))

    def test_subcommand_dispatch(self):
        with mock.patch.object(P, "cmd_preview") as cp, mock.patch.object(sys, "argv", ["pipeline.py", "preview", "crate"]):
            P.main()
        cp.assert_called_once()
        self.assertEqual(cp.call_args[0][0].name, "crate")

    def test_build_runs_blender_then_preview(self):
        calls = []
        with mock.patch.object(P, "cmd_model3d", side_effect=lambda a: calls.append("model3d")), \
                mock.patch.object(P, "cmd_blender", side_effect=lambda a: calls.append("blender")), \
                mock.patch.object(P, "cmd_preview", side_effect=lambda a: calls.append("preview")):
            P.cmd_build(argparse.Namespace(name="crate", image="x.png", views=False, seed=None, engine="klein9b",
                                           pipeline_type="1024", texture_size=1024, faces=None, engine3d="trellis"))
        self.assertEqual(calls, ["model3d", "blender", "preview"])


class Faces(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.img = os.path.join(self.tmp.name, "a.png")
        open(self.img, "w").close()

    def meta(self, style):
        with open(os.path.join(self.tmp.name, "a.json"), "w") as f:
            json.dump({"style": style}, f)

    def ns(self, faces=None):
        return argparse.Namespace(image=self.img, faces=faces)

    def test_explicit_wins(self):
        self.meta("lowpoly")
        self.assertEqual(P.mesh_faces(self.ns(1234)), (1234, "--faces"))

    def test_style_default(self):
        self.meta("lowpoly")
        self.assertEqual(P.mesh_faces(self.ns()), (10000, "style lowpoly"))

    def test_style_without_faces(self):
        self.meta("nofaces")
        with mock.patch.object(P, "styles", return_value={"nofaces": {"prompt": "x"}}):
            self.assertEqual(P.mesh_faces(self.ns()), (200000, "default"))

    def test_missing_json(self):
        self.assertEqual(P.mesh_faces(self.ns()), (200000, "default"))

    def test_unknown_style(self):
        self.meta("does_not_exist")
        self.assertEqual(P.mesh_faces(self.ns()), (200000, "default"))

    def test_model3d_env_and_json(self):
        self.meta("lowpoly")
        vendor = os.path.join(self.tmp.name, "vendor")
        py = os.path.join(vendor, "trellis-mac", ".venv", "bin", "python")
        os.makedirs(os.path.dirname(py))
        open(py, "w").close()
        out = os.path.join(self.tmp.name, "out")
        glb = os.path.join(vendor, "trellis-mac", "crate_trellis.glb")
        with open(glb, "w") as f:
            f.write("glb")
        a = argparse.Namespace(name="crate", image=self.img, seed=1, pipeline_type="1024", texture_size=1024, faces=None,
                               engine3d="trellis")
        with mock.patch.object(P, "VENDOR", vendor), mock.patch.object(P, "OUT", out), \
                mock.patch.object(P.subprocess, "run") as run:
            P.cmd_model3d(a)
        self.assertEqual(run.call_args[1]["env"]["TRELLIS_FACES"], "10000")
        self.assertTrue(run.call_args[1]["env"]["PATH"])  # parent env preserved
        with open(os.path.join(out, "crate", "model", "crate_trellis.json")) as f:
            meta = json.load(f)
        self.assertEqual(meta["faces"], 10000)
        self.assertEqual(meta["engine3d"], "trellis")

    def test_cli_faces_parsed_as_int(self):
        for cmd, fn in (("model3d", "cmd_model3d"), ("build", "cmd_build")):
            with mock.patch.object(P, fn) as m, \
                    mock.patch.object(sys, "argv", ["pipeline.py", cmd, "crate", "x.png", "--faces", "5000"]):
                P.main()
            self.assertEqual(m.call_args[0][0].faces, 5000, cmd)
            with mock.patch.object(P, fn) as m, mock.patch.object(sys, "argv", ["pipeline.py", cmd, "crate", "x.png"]):
                P.main()
            self.assertIsNone(m.call_args[0][0].faces)
            with mock.patch.object(sys, "argv", ["pipeline.py", cmd, "crate", "x.png", "--faces", "abc"]), \
                    mock.patch("sys.stderr"), self.assertRaises(SystemExit):
                P.main()

    def test_build_forwards_faces(self):
        with mock.patch.object(P, "cmd_model3d") as m3, mock.patch.object(P, "cmd_blender"), mock.patch.object(P, "cmd_preview"):
            P.cmd_build(argparse.Namespace(name="crate", image="x.png", views=False, seed=None, engine="klein9b",
                                           pipeline_type="1024", texture_size=1024, faces=777, engine3d="trellis"))
        self.assertEqual(m3.call_args[0][0].faces, 777)

    def test_setup_trellis_patches_faces(self):
        self.assertIn("TRELLIS_FACES", read("scripts", "setup_trellis.sh"))


class Engines3D(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = os.path.join(self.tmp.name, "out")
        self.vendor = os.path.join(self.tmp.name, "vendor")
        for p in (mock.patch.object(P, "OUT", self.out), mock.patch.object(P, "VENDOR", self.vendor)):
            p.start()
            self.addCleanup(p.stop)

    def model_dir(self, name="crate"):
        d = os.path.join(self.out, name, "model")
        os.makedirs(d, exist_ok=True)
        return d

    def touch(self, path, mtime=None, text=""):
        with open(path, "w") as f:
            f.write(text)
        if mtime:
            os.utime(path, (mtime, mtime))

    def ns(self, **kw):
        d = dict(name="crate", image=os.path.join(self.tmp.name, "a.png"), seed=7, pipeline_type="1024",
                 texture_size=2048, faces=None, engine3d="pixal3d")
        d.update(kw)
        return argparse.Namespace(**d)

    def fake_vendor(self, sub):
        py = os.path.join(self.vendor, sub, ".venv", "bin", "python")
        os.makedirs(os.path.dirname(py))
        self.touch(py)
        return py

    def test_pixal3d_command_env_and_json(self):
        py = self.fake_vendor("pixal3d-mac")
        with mock.patch.object(P.subprocess, "run") as run:
            P.cmd_model3d(self.ns(faces=4000))
        cmd, kw = run.call_args[0][0], run.call_args[1]
        dest = os.path.join(self.out, "crate", "model", "crate_pixal3d.glb")
        self.assertEqual(cmd[:2], [py, "generate_mps.py"])
        self.assertEqual(cmd[2], os.path.abspath(self.ns().image))
        self.assertEqual(cmd[cmd.index("--output") + 1], dest)
        self.assertEqual(cmd[cmd.index("--seed") + 1], "7")
        self.assertEqual(cmd[cmd.index("--native-decimation-target") + 1], P.CFG["PIXAL3D_FACES"])
        self.assertEqual(cmd[cmd.index("--texture-size") + 1], "2048")
        self.assertEqual(kw["cwd"], os.path.join(self.vendor, "pixal3d-mac"))
        self.assertEqual(kw["env"]["O_VOXEL_PYTHON"], py)
        self.assertTrue(kw["check"])
        with open(dest[:-4] + ".json") as f:
            meta = json.load(f)
        self.assertEqual((meta["engine3d"], meta["faces"], meta["seed"]), ("pixal3d", 4000, 7))

    def test_pixal3d_not_installed_exits(self):
        with mock.patch.object(P.subprocess, "run") as run, self.assertRaises(SystemExit):
            P.cmd_model3d(self.ns())
        run.assert_not_called()

    def test_trellis_not_installed_exits(self):
        with mock.patch.object(P.subprocess, "run") as run, self.assertRaises(SystemExit):
            P.cmd_model3d(self.ns(engine3d="trellis"))
        run.assert_not_called()

    def test_latest_model_ignores_lowpoly_and_picks_newest(self):
        d = self.model_dir()
        self.touch(os.path.join(d, "crate_trellis.glb"), 1000)
        self.touch(os.path.join(d, "crate_pixal3d.glb"), 2000)
        self.touch(os.path.join(d, "crate_pixal3d.json"), text='{"engine3d": "pixal3d", "faces": 5}')
        self.touch(os.path.join(d, "crate_lowpoly.glb"), 3000)
        glb, meta = P.latest_model("crate")
        self.assertEqual(os.path.basename(glb), "crate_pixal3d.glb")
        self.assertEqual(meta["faces"], 5)
        os.utime(os.path.join(d, "crate_trellis.glb"), (4000, 4000))
        self.assertEqual(os.path.basename(P.latest_model("crate")[0]), "crate_trellis.glb")

    def test_latest_model_missing_json_or_none(self):
        d = self.model_dir()
        with self.assertRaises(SystemExit):
            P.latest_model("crate")
        self.touch(os.path.join(d, "crate_lowpoly.glb"))
        with self.assertRaises(SystemExit):
            P.latest_model("crate")  # only the low-poly export does not count
        self.touch(os.path.join(d, "crate_trellis.glb"))
        self.assertEqual(P.latest_model("crate")[1], {})
        self.touch(os.path.join(d, "crate_trellis.json"), text="not json")
        self.assertEqual(P.latest_model("crate")[1], {})

    def run_blender_step(self, meta):
        d = self.model_dir()
        self.touch(os.path.join(d, "crate_x.glb"))
        self.touch(os.path.join(d, "crate_x.json"), text=json.dumps(meta))
        with mock.patch.object(P, "blender_exe", return_value="/fake/B"), mock.patch.object(P.subprocess, "run") as run:
            P.cmd_blender(argparse.Namespace(name="crate"))
        return run.call_args[0][0], d

    def test_blender_rotates_only_pixal3d(self):
        cmd, d = self.run_blender_step({"engine3d": "pixal3d"})
        self.assertEqual(cmd[cmd.index("--rotate-z") + 1], "180")
        self.assertEqual(cmd[cmd.index("--") + 1], os.path.join(d, "crate_x.glb"))
        self.assertEqual(cmd[cmd.index("--name") + 1], "crate")

    def test_blender_no_rotation_for_trellis_or_unknown(self):
        for meta in ({"engine3d": "trellis"}, {}):
            cmd, _ = self.run_blender_step(meta)
            self.assertNotIn("--rotate-z", cmd)

    def blend_dir(self):
        d = os.path.join(self.out, "crate", "blender")
        os.makedirs(d, exist_ok=True)
        return d

    def lowpoly(self, **kw):
        with mock.patch.object(P, "blender_exe", return_value="/fake/B"), mock.patch.object(P.subprocess, "run") as run:
            P.cmd_lowpoly(argparse.Namespace(name="crate", **{"faces": None, "size": 2048, **kw}))
        return run.call_args[0][0]

    def test_lowpoly_missing_blend_exits(self):
        with mock.patch.object(P.subprocess, "run") as run, self.assertRaises(SystemExit):
            P.cmd_lowpoly(argparse.Namespace(name="crate", faces=None, size=2048))
        run.assert_not_called()

    def test_lowpoly_command_and_faces_default(self):
        bd = self.blend_dir()
        blend = os.path.join(bd, "crate.blend")
        self.touch(blend)
        md = self.model_dir()
        self.touch(os.path.join(md, "crate_pixal3d.glb"))
        self.touch(os.path.join(md, "crate_pixal3d.json"), text='{"faces": 4321}')
        cmd = self.lowpoly()
        self.assertEqual(cmd[cmd.index("-b") + 1], blend)
        self.assertIn("--factory-startup", cmd)
        self.assertEqual(cmd[cmd.index("--python") + 1], os.path.join(LAB, "blender", "lowpoly.py"))
        i = cmd.index("--")
        self.assertEqual(cmd[i + 1], os.path.join(bd, "crate_lowpoly.blend"))
        self.assertEqual(cmd[i + 2], os.path.join(md, "crate_lowpoly.glb"))
        self.assertEqual(cmd[cmd.index("--faces") + 1], "4321")
        self.assertEqual(cmd[cmd.index("--size") + 1], "2048")
        cmd = self.lowpoly(faces=99, size=512)
        self.assertEqual(cmd[cmd.index("--faces") + 1], "99")
        self.assertEqual(cmd[cmd.index("--size") + 1], "512")

    def test_lowpoly_faces_fallback_3000(self):
        self.touch(os.path.join(self.blend_dir(), "crate.blend"))
        self.touch(os.path.join(self.model_dir(), "crate_trellis.glb"))
        cmd = self.lowpoly()
        self.assertEqual(cmd[cmd.index("--faces") + 1], "3000")

    def preview_blend(self, **kw):
        with mock.patch.object(P, "blender_exe", return_value="/fake/B"), mock.patch.object(P.subprocess, "run") as run:
            P.cmd_preview(argparse.Namespace(name="crate", **kw))
        cmd = run.call_args[0][0]
        return os.path.basename(cmd[cmd.index("-b") + 1])

    def test_preview_lowpoly_vs_high(self):
        bd = self.blend_dir()
        self.touch(os.path.join(bd, "crate.blend"))
        self.assertEqual(self.preview_blend(high=False), "crate.blend")
        self.touch(os.path.join(bd, "crate_lowpoly.blend"))
        self.assertEqual(self.preview_blend(high=False), "crate_lowpoly.blend")
        self.assertEqual(self.preview_blend(high=True), "crate.blend")
        self.assertEqual(self.preview_blend(), "crate_lowpoly.blend")  # no flag at all

    def test_build_lowpoly_only_for_pixal3d(self):
        for eng, expect in (("pixal3d", ["model3d", "blender", "lowpoly", "preview"]),
                            ("trellis", ["model3d", "blender", "preview"])):
            calls = []
            with mock.patch.object(P, "cmd_model3d", side_effect=lambda a: calls.append("model3d")), \
                    mock.patch.object(P, "cmd_blender", side_effect=lambda a: calls.append("blender")), \
                    mock.patch.object(P, "cmd_lowpoly", side_effect=lambda a: calls.append(("lowpoly", a.size))), \
                    mock.patch.object(P, "cmd_preview", side_effect=lambda a: calls.append(("preview", a.high))):
                P.cmd_build(argparse.Namespace(name="crate", image="x.png", views=False, seed=None, engine="klein9b",
                                               pipeline_type="1024", texture_size=2048, faces=None, engine3d=eng))
            names = [c if isinstance(c, str) else c[0] for c in calls]
            self.assertEqual(names, expect, eng)
            self.assertIn(("preview", False), calls)
            if eng == "pixal3d":
                self.assertIn(("lowpoly", 2048), calls)

    def parse(self, *argv):
        seen = {}
        names = {c: f"cmd_{c}" for c in ("model3d", "build", "lowpoly", "preview")}
        with mock.patch.object(P, names[argv[0]], side_effect=lambda a: seen.update(vars(a))), \
                mock.patch.object(sys, "argv", ["pipeline.py", *argv]):
            P.main()
        return seen

    def test_cli_engine3d(self):
        self.assertEqual(P.ENGINES3D, ("pixal3d", "trellis"))
        self.assertEqual(P.CFG["DEFAULT_ENGINE3D"], "pixal3d")
        for cmd in ("model3d", "build"):
            self.assertEqual(self.parse(cmd, "c", "x.png")["engine3d"], "pixal3d")
            self.assertEqual(self.parse(cmd, "c", "x.png")["texture_size"], 2048)
            self.assertEqual(self.parse(cmd, "c", "x.png", "--engine3d", "trellis")["engine3d"], "trellis")
            with mock.patch.object(sys, "argv", ["pipeline.py", cmd, "c", "x.png", "--engine3d", "bogus"]), \
                    mock.patch("sys.stderr"), self.assertRaises(SystemExit):
                P.main()

    def test_cli_lowpoly_and_preview(self):
        a = self.parse("lowpoly", "c")
        self.assertEqual((a["faces"], a["size"]), (None, 2048))
        a = self.parse("lowpoly", "c", "--faces", "1500", "--size", "512")
        self.assertEqual((a["faces"], a["size"]), (1500, 512))
        for bad in (["--size", "300"], ["--faces", "0"], ["--faces", "-5"]):
            with mock.patch.object(sys, "argv", ["pipeline.py", "lowpoly", "c", *bad]), \
                    mock.patch("sys.stderr"), self.assertRaises(SystemExit):
                P.main()
        self.assertFalse(self.parse("preview", "c")["high"])
        self.assertTrue(self.parse("preview", "c", "--high")["high"])

    def test_style_faces(self):
        st = P.styles()
        self.assertEqual(st["psx"]["faces"], 5000)
        self.assertEqual(st["lowpoly"]["faces"], 10000)

    def test_setup_pixal3d_script(self):
        path = os.path.join(LAB, "scripts", "setup_pixal3d.sh")
        self.assertEqual(subprocess.run(["bash", "-n", path]).returncode, 0)
        self.assertIn("PIXAL3D_REF", read("scripts", "setup_pixal3d.sh"))
        self.assertRegex(P.CFG["PIXAL3D_REF"], r"^[0-9a-f]{40}$")

    def test_export_prefers_lowpoly(self):
        src = read("scripts", "export_to_game.sh")
        self.assertIn("_lowpoly.glb", src)
        self.assertIn("ls -t", src)


class Config(unittest.TestCase):
    def test_trellis_ref_is_commit_hash(self):
        self.assertRegex(P.CFG["TRELLIS_MAC_REF"], r"^[0-9a-f]{40}$")

    def test_export_excludes_preview(self):
        src = read("scripts", "export_to_game.sh")
        for d in ("model/", "blender/", "preview/"):
            self.assertIn(f"--exclude '{d}'", src)

    def test_setup_mac_hint(self):
        self.assertIn("./pipeline.py doctor", read("scripts", "setup_mac.sh"))

    def test_blender_scripts_use_standard_transform(self):
        for f in ("import_glb.py", "render_preview.py"):
            src = read("blender", f)
            self.assertRegex(src, r'view_transform\s*=\s*"Standard"', f)


class BlenderIntegration(unittest.TestCase):
    def test_render_previews(self):
        if not os.environ.get("BLENDER_TEST"):
            self.skipTest("set BLENDER_TEST=1")
        try:
            blender = P.blender_exe()
        except SystemExit:
            self.skipTest("Blender not found")
        with tempfile.TemporaryDirectory() as t:
            blend, out = os.path.join(t, "cube.blend"), os.path.join(t, "preview")
            make = ("import bpy;bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.mesh.primitive_cube_add();"
                    f"bpy.ops.wm.save_as_mainfile(filepath={blend!r})")
            subprocess.run([blender, "-b", "--factory-startup", "--python-expr", make], check=True, capture_output=True)
            subprocess.run([blender, "-b", blend, "--factory-startup", "--python",
                            os.path.join(LAB, "blender", "render_preview.py"), "--", out], check=True, capture_output=True)
            for v in VIEWS:
                f = os.path.join(out, f"preview_{v}.png")
                self.assertTrue(os.path.getsize(f) > 0, f)
                with open(f, "rb") as fh:
                    self.assertEqual(fh.read(8), b"\x89PNG\r\n\x1a\n")

    def test_lowpoly_bake(self):
        if not os.environ.get("BLENDER_TEST"):
            self.skipTest("set BLENDER_TEST=1")
        try:
            blender = P.blender_exe()
        except SystemExit:
            self.skipTest("Blender not found")
        with tempfile.TemporaryDirectory() as t:
            blend = os.path.join(t, "sphere.blend")
            dst_blend, dst_glb = os.path.join(t, "low.blend"), os.path.join(t, "low.glb")
            make = (
                "import bpy\n"
                "bpy.ops.wm.read_factory_settings(use_empty=True)\n"
                "bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32)\n"
                "o=bpy.context.object\n"
                "img=bpy.data.images.new('t',64,64)\n"
                "img.pixels=[0.9,0.2,0.1,1.0]*(64*64)\n"
                "m=bpy.data.materials.new('m'); m.use_nodes=True\n"
                "tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=img\n"
                "m.node_tree.links.new(tex.outputs['Color'], m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])\n"
                "o.data.materials.append(m)\n"
                "img.pack()\n"
                f"bpy.ops.wm.save_as_mainfile(filepath={blend!r})\n")
            subprocess.run([blender, "-b", "--factory-startup", "--python-expr", make], check=True, capture_output=True)
            r = subprocess.run([blender, "-b", blend, "--factory-startup", "--python",
                                os.path.join(LAB, "blender", "lowpoly.py"), "--", dst_blend, dst_glb,
                                "--faces", "200", "--size", "256"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-1500:])
            self.assertGreater(os.path.getsize(dst_blend), 0)
            self.assertGreater(os.path.getsize(dst_glb), 0)
            check = (
                "import bpy,sys\n"
                f"bpy.ops.wm.open_mainfile(filepath={dst_blend!r})\n"
                "tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.data.objects if o.type=='MESH')\n"
                "mx=max((max(i.pixels[:]) for i in bpy.data.images if i.size[0]>0 and i.name!='Render Result'), default=0)\n"
                "print('RESULT',tris,mx)\n")
            r = subprocess.run([blender, "-b", "--factory-startup", "--python-expr", check], capture_output=True, text=True)
            line = [ln for ln in r.stdout.splitlines() if ln.startswith("RESULT")][0].split()
            tris, mx = int(line[1]), float(line[2])
            self.assertTrue(100 <= tris <= 400, tris)
            self.assertGreater(mx, 0.05, "baked texture is all black")


if __name__ == "__main__":
    unittest.main()
