"""Offline tests: workflow graphs are well-formed. LIVE=1 also checks node classes against a running ComfyUI.
    python3 tests/test_graphs.py        LIVE=1 python3 tests/test_graphs.py
"""
import json
import os
import subprocess
import sys
import unittest
import urllib.request

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LAB)
import pipeline as P  # noqa: E402


class Graphs(unittest.TestCase):
    def check(self, wf):
        for nid, n in wf.items():
            for k, v in n["inputs"].items():
                if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str):
                    self.assertIn(v[0], wf, f"{nid}.{k} points to missing node {v[0]}")

    def test_all_engines_and_modes(self):
        for eng in P.engines():
            for ref in (None, "ref.png"):
                wf = P.graph(eng, "a test", 1, ref_image=ref)
                self.check(wf)
                self.assertEqual(wf["12"]["class_type"], "SaveImage")
                self.assertEqual(("ReferenceLatent" in {n["class_type"] for n in wf.values()}), ref is not None)

    def test_engine_details(self):
        self.assertEqual(P.graph("klein9b", "x", 1)["8"]["inputs"]["steps"], 4)
        self.assertNotIn("FluxGuidance", {n["class_type"] for n in P.graph("klein9b", "x", 1).values()})
        dev = P.graph("dev", "x", 1)
        self.assertEqual(dev["14"]["inputs"]["guidance"], 4.0)
        turbo = P.graph("dev_turbo", "x", 1)
        self.assertEqual(turbo["8"]["inputs"]["steps"], 8)
        self.assertEqual(turbo["9"]["inputs"]["model"], ["13", 0])  # LoRA in the model path

    def test_styles_and_poses(self):
        st = P.styles()
        for need in ("hero", "character", "lowpoly", "prop"):
            self.assertIn(need, st)
        self.assertIn(P.CFG["DEFAULT_STYLE"], st)
        c = P.common()
        self.assertEqual(set(c["poses"]) - set(c["pose_hold"]), set())
        self.assertEqual(set(c["views"]), {"front", "left", "back", "right"})

    def test_name_rules(self):
        with self.assertRaises(SystemExit):
            P.slug("Bad Name")
        self.assertEqual(P.slug("jungle_cat"), "jungle_cat")

    def test_scripts_parse(self):
        for f in sorted(os.listdir(os.path.join(LAB, "scripts"))):
            r = subprocess.run(["bash", "-n", os.path.join(LAB, "scripts", f)], capture_output=True)
            self.assertEqual(r.returncode, 0, f)

    def test_live_nodes(self):
        if not os.environ.get("LIVE"):
            self.skipTest("set LIVE=1 with ComfyUI running")
        info = json.load(urllib.request.urlopen(P.COMFYUI_URL + "/object_info", timeout=20))
        need = {n["class_type"] for e in P.engines() for n in P.graph(e, "x", 1, ref_image="a.png").values()}
        self.assertEqual(sorted(need - set(info)), [])


if __name__ == "__main__":
    unittest.main()
