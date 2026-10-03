#!/usr/bin/env python3
"""Mac asset lab: text -> concept image -> views -> 3D model -> Blender. Stdlib only.

    ./pipeline.py styles
    ./pipeline.py concept <name> "<subject>" [--style character] [--pose tpose] [--engine klein9b] [--count 4]
    ./pipeline.py edit    <name> <image.png> "<instruction>" [--count 2]
    ./pipeline.py views   <name> <image.png> [--only front back]
    ./pipeline.py model3d <name> <image.png> [--pipeline-type 512|1024|1024_cascade] [--texture-size 1024]
    ./pipeline.py blender <name>              # GLB -> out/<name>/blender/<name>.blend
    ./pipeline.py build   <name> <image.png>  # views (optional) -> model3d -> blender in one go
    ./pipeline.py bench                       # same prompts on every engine, writes out/bench.md
    ./pipeline.py doctor                      # checks the install

Everything is written to out/<name>/ (concepts, views/, model/, blender/). The layout matches the game repo's
assets/concepts/<name>/, so scripts/export_to_game.sh can copy it over.
The style is chosen up front with --style (files in styles/*.json; add your own, the file name is the style name).
"""

import argparse
import glob
import json
import mimetypes
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

LAB = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(LAB, "out")
VENDOR = os.path.join(LAB, "vendor")


# ---------------------------------------------------------------- config

def load_env():
    cfg = {}
    with open(os.path.join(LAB, "config", "models.env")) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    cfg.update({k: v for k, v in os.environ.items() if k in cfg})
    return cfg


CFG = load_env()
COMFYUI_URL = CFG["COMFYUI_URL"]


def base(key):
    return os.path.basename(CFG[key])


# engine = which model stack renders the image. Filenames come from config/models.env.
def engines():
    return {
        "klein9b": dict(unet=base("KLEIN_UNET_FILE"), clip=base("KLEIN_CLIP_FILE"), steps=4, guidance=None, lora=None,
                        note="FLUX.2 klein 9B (distilled): 4 steps, best at editing, safe on the Mac"),
        "dev": dict(unet=base("DEV_UNET_FILE"), clip=base("DEV_CLIP_FILE"), steps=20, guidance=4.0, lora=None,
                    note="FLUX.2 dev 32B (GGUF): best quality, slow"),
        "dev_turbo": dict(unet=base("DEV_UNET_FILE"), clip=base("DEV_CLIP_FILE"), steps=8, guidance=4.0,
                          lora=base("TURBO_LORA_FILE"), note="FLUX.2 dev with the turbo LoRA: 8 steps"),
    }


def slug(name):
    if not re.fullmatch(r"[a-z0-9_]+", name):
        sys.exit(f"name must be lower_snake_case: {name!r}")
    return name


# ---------------------------------------------------------------- styles (chosen up front)

def common():
    with open(os.path.join(LAB, "styles", "_common.json")) as f:
        return json.load(f)


def styles():
    out = {}
    for p in sorted(glob.glob(os.path.join(LAB, "styles", "*.json"))):
        n = os.path.basename(p)[:-5]
        if n.startswith("_"):
            continue
        with open(p) as f:
            out[n] = json.load(f)
    return out


def cmd_styles(_a):
    for n, s in styles().items():
        mark = " (default)" if n == CFG["DEFAULT_STYLE"] else ""
        print(f"{n}{mark}: {s['description']}")
    print("poses:", ", ".join(common()["poses"]))


# ---------------------------------------------------------------- ComfyUI graph (API format)

def graph(engine, prompt, seed, size=1024, ref_image=None, steps=None):
    """GGUF UNet + text encoder + Flux2 VAE. With ref_image the model runs in edit mode (ReferenceLatent).
    Same graph shape as the one proven on the Linux box (klein 4B); dev adds FluxGuidance and an optional LoRA."""
    e = engines()[engine]
    steps = steps or e["steps"]
    wf = {
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": e["unet"]}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": e["clip"], "type": "flux2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": base("VAE_FILE")}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
        "5": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": size, "height": size, "batch_size": 1}},
        "6": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "7": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "8": {"class_type": "Flux2Scheduler", "inputs": {"steps": steps, "width": size, "height": size}},
        "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["3", 0]}},
        "12": {"class_type": "SaveImage", "inputs": {"images": ["11", 0], "filename_prefix": "lab"}},
    }
    model, cond = ["1", 0], ["4", 0]
    if e["lora"]:
        wf["13"] = {"class_type": "LoraLoaderModelOnly",
                    "inputs": {"model": ["1", 0], "lora_name": e["lora"], "strength_model": 1.0}}
        model = ["13", 0]
    if ref_image:
        wf.update({
            "20": {"class_type": "LoadImage", "inputs": {"image": ref_image}},
            "21": {"class_type": "ImageScaleToTotalPixels", "inputs": {
                "image": ["20", 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 16}},
            "22": {"class_type": "VAEEncode", "inputs": {"pixels": ["21", 0], "vae": ["3", 0]}},
            "23": {"class_type": "ReferenceLatent", "inputs": {"conditioning": cond, "latent": ["22", 0]}},
        })
        cond = ["23", 0]
    if e["guidance"] is not None:
        wf["14"] = {"class_type": "FluxGuidance", "inputs": {"conditioning": cond, "guidance": e["guidance"]}}
        cond = ["14", 0]
    wf["9"] = {"class_type": "BasicGuider", "inputs": {"model": model, "conditioning": cond}}
    wf["10"] = {"class_type": "SamplerCustomAdvanced", "inputs": {
        "noise": ["6", 0], "guider": ["9", 0], "sampler": ["7", 0], "sigmas": ["8", 0], "latent_image": ["5", 0]}}
    return wf


def http_json(url, data=None, method=None, timeout=60):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method,
                                 headers={"Content-Type": "application/json"} if body else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} for {url.split('?')[0]}: {e.read().decode(errors='replace')[:600]}")


def require_comfy():
    try:
        http_json(f"{COMFYUI_URL}/system_stats", timeout=5)
    except (urllib.error.URLError, OSError):
        sys.exit(f"ComfyUI not reachable at {COMFYUI_URL}. Start it: scripts/comfy_up.sh")


def comfy_upload(path, upload_name):
    boundary = uuid.uuid4().hex
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        payload = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{upload_name}\"\r\n"
            f"Content-Type: {mime}\r\n\r\n").encode() + payload \
        + f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{COMFYUI_URL}/upload/image", data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["name"]


def render(engine, prompt, seed, out_path, ref_image=None, size=1024, steps=None):
    resp = http_json(f"{COMFYUI_URL}/prompt", {"prompt": graph(engine, prompt, seed, size, ref_image, steps),
                                               "client_id": uuid.uuid4().hex})
    pid, t0 = resp["prompt_id"], time.time()
    while True:
        hist = http_json(f"{COMFYUI_URL}/history/{pid}").get(pid)
        if hist and hist.get("status", {}).get("completed"):
            break
        if hist and hist.get("status", {}).get("status_str") == "error":
            sys.exit(f"ComfyUI error: {json.dumps(hist['status'].get('messages', []))[:1000]}")
        if time.time() - t0 > 3600:
            sys.exit("ComfyUI timeout (1 h)")
        time.sleep(1)
    img = hist["outputs"]["12"]["images"][0]
    q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img["subfolder"], "type": img["type"]})
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with urllib.request.urlopen(f"{COMFYUI_URL}/view?{q}", timeout=120) as r, open(out_path, "wb") as f:
        shutil.copyfileobj(r, f)
    return time.time() - t0


def rel(p):
    return os.path.relpath(p, LAB)


def meta_write(path, **kw):
    with open(path[:-4] + ".json", "w") as f:
        json.dump(kw, f, indent=2)


# ---------------------------------------------------------------- image steps

def cmd_concept(a):
    name, c, st = slug(a.name), common(), styles()
    if a.style not in st:
        sys.exit(f"unknown style {a.style!r}; see ./pipeline.py styles")
    if a.pose not in c["poses"]:
        sys.exit(f"unknown pose {a.pose!r}")
    require_comfy()
    prompt = f"{a.subject.strip()} {c['poses'][a.pose]} {st[a.style]['prompt']} {c['framing']}"
    base_seed = a.seed if a.seed is not None else random.randrange(1 << 31)
    for i in range(a.count):
        seed = base_seed + i
        path = os.path.join(OUT, name, f"{name}_s{seed}.png")
        dt = render(a.engine, prompt, seed, path, size=a.size)
        meta_write(path, subject=a.subject, pose=a.pose, style=a.style, engine=a.engine, prompt=prompt, seed=seed)
        print(f"{rel(path)}  ({dt:.0f} s)")


def cmd_edit(a):
    name, c = slug(a.name), common()
    require_comfy()
    meta = {}
    mp = os.path.splitext(a.image)[0] + ".json"
    if os.path.exists(mp):
        with open(mp) as f:
            meta = json.load(f)
    ref = comfy_upload(a.image, f"{name}_edit_ref{os.path.splitext(a.image)[1]}")
    ins = a.instruction.strip()
    ins += "" if ins[-1] in ".!?" else "."
    prompt = (f"Edit the reference image: {ins} Keep everything else exactly the same: the same character, design, "
              f"colors, markings, pose, camera angle and framing. {c['framing']}")
    base_seed = a.seed if a.seed is not None else random.randrange(1 << 31)
    for i in range(a.count):
        seed = base_seed + i
        path = f"{os.path.splitext(a.image)[0]}_e{seed}.png"
        dt = render(a.engine, prompt, seed, path, ref_image=ref, size=a.size)
        meta_write(path, **{**meta, "edited_from": os.path.basename(a.image), "instruction": a.instruction,
                            "prompt": prompt, "seed": seed, "engine": a.engine})
        print(f"{rel(path)}  ({dt:.0f} s)")


def cmd_views(a):
    name, c = slug(a.name), common()
    require_comfy()
    pose = a.pose
    mp = os.path.splitext(a.image)[0] + ".json"
    if pose is None and os.path.exists(mp):
        with open(mp) as f:
            pose = json.load(f).get("pose")
    pose = pose if pose in c["pose_hold"] else "tpose"
    ref = comfy_upload(a.image, f"{name}_ref{os.path.splitext(a.image)[1]}")
    seed = a.seed if a.seed is not None else random.randrange(1 << 31)
    for view in a.only or c["views"]:
        limbs = "All limbs fully visible" if pose == "humanoid" else "All limbs and the tail fully visible"
        prompt = " ".join(filter(None, [
            "The exact same character as in the reference image: identical design, proportions, colors, markings "
            f"and fur pattern. {c['views'][view]}.", c["pose_hold"][pose],
            f"{limbs} and not overlapping the body, orthographic camera at mid-body height.", a.note, c["framing"]]))
        path = os.path.join(OUT, name, "views", f"{name}_{view}_s{seed}.png")
        dt = render(a.engine, prompt, seed, path, ref_image=ref, size=a.size)
        meta_write(path, reference=os.path.basename(a.image), view=view, pose=pose, prompt=prompt, seed=seed,
                   engine=a.engine)
        print(f"{rel(path)}  ({dt:.0f} s)")


# ---------------------------------------------------------------- 3D (TRELLIS.2 for Apple Silicon) and Blender

def cmd_model3d(a):
    name = slug(a.name)
    t = os.path.join(VENDOR, "trellis-mac")
    py = os.path.join(t, ".venv", "bin", "python")
    if not os.path.exists(py):
        sys.exit("TRELLIS not installed: scripts/setup_trellis.sh")
    out_dir = os.path.join(OUT, name, "model")
    os.makedirs(out_dir, exist_ok=True)
    stem = f"{name}_trellis"
    cmd = [py, os.path.join(t, "generate.py"), os.path.abspath(a.image), "--seed", str(a.seed),
           "--output", stem, "--pipeline-type", a.pipeline_type, "--texture-size", str(a.texture_size)]
    print(" ".join(cmd))
    t0 = time.time()
    subprocess.run(cmd, cwd=t, check=True)
    found = [p for p in (os.path.join(t, stem + ".glb"), os.path.join(t, stem, stem + ".glb"),
                         *glob.glob(os.path.join(t, "**", stem + ".glb"), recursive=True)) if os.path.exists(p)]
    if not found:
        sys.exit(f"TRELLIS finished but {stem}.glb was not found under {t}; check its output folder")
    dest = os.path.join(out_dir, stem + ".glb")
    shutil.copy(found[0], dest)
    with open(dest[:-4] + ".json", "w") as f:
        json.dump(dict(image=os.path.basename(a.image), seed=a.seed, pipeline_type=a.pipeline_type,
                       texture_size=a.texture_size, seconds=round(time.time() - t0)), f, indent=2)
    print(f"{rel(dest)}  ({time.time() - t0:.0f} s)")


def blender_exe():
    for c in (os.environ.get("BLENDER"), shutil.which("blender"), "/Applications/Blender.app/Contents/MacOS/Blender"):
        if c and os.path.exists(c):
            return c
    sys.exit("Blender not found. Install it or set BLENDER=/path/to/Blender")


def cmd_blender(a):
    name = slug(a.name)
    glb = os.path.join(OUT, name, "model", f"{name}_trellis.glb")
    if not os.path.exists(glb):
        sys.exit(f"missing {rel(glb)}; run model3d first")
    dest = os.path.join(OUT, name, "blender", f"{name}.blend")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    subprocess.run([blender_exe(), "-b", "--factory-startup", "--python", os.path.join(LAB, "blender", "import_glb.py"),
                    "--", glb, dest, "--name", name], check=True)
    print(rel(dest))


def cmd_build(a):
    name = slug(a.name)
    if a.views:
        cmd_views(argparse.Namespace(name=name, image=a.image, seed=a.seed, only=None, pose=None, note=None,
                                     engine=a.engine, size=1024))
    cmd_model3d(argparse.Namespace(name=name, image=a.image, seed=a.seed or 42, pipeline_type=a.pipeline_type,
                                   texture_size=a.texture_size))
    cmd_blender(argparse.Namespace(name=name))


# ---------------------------------------------------------------- bench and doctor

BENCH = [("banana", "a single ripe banana", "object", "prop"),
         ("goblin", "a scruffy green goblin villager in a ragged vest", "humanoid", "character"),
         ("horse", "a sturdy brown knight's horse with a short braided mane", "quadruped", "character")]


def cmd_bench(a):
    require_comfy()
    rows = ["| engine | prompt | seconds | file |", "|---|---|---|---|"]
    for eng in a.engines:
        for name, subject, pose, style in BENCH:
            args = argparse.Namespace(name="bench_" + name, subject=subject, pose=pose, style=style, engine=eng,
                                      count=1, seed=1234, size=1024)
            t0 = time.time()
            cmd_concept(args)
            rows.append(f"| {eng} | {name} | {time.time() - t0:.0f} | out/bench_{name}/bench_{name}_s1234.png |")
            os.replace(os.path.join(OUT, "bench_" + name, f"bench_{name}_s1234.png"),
                       os.path.join(OUT, "bench_" + name, f"bench_{name}_{eng}.png"))
    with open(os.path.join(OUT, "bench.md"), "w") as f:
        f.write("\n".join(rows) + "\n")
    print("\n".join(rows))


def cmd_doctor(_a):
    ok = True

    def check(label, good, hint=""):
        nonlocal ok
        print(("ok    " if good else "FAIL  ") + label + ("" if good else f"   -> {hint}"))
        ok = ok and good

    check("Apple Silicon macOS (arm64)", sys.platform == "darwin" and os.uname().machine == "arm64",
          "expected on the Mac; on Linux only the tests run")
    comfy = os.path.join(VENDOR, "ComfyUI")
    check("ComfyUI installed", os.path.exists(os.path.join(comfy, "main.py")), "scripts/setup_mac.sh")
    for eng, e in engines().items():
        for kind, sub in (("unet", "diffusion_models"), ("clip", "text_encoders")):
            p = os.path.join(comfy, "models", sub, e[kind])
            check(f"[{eng}] {sub}/{e[kind]}", os.path.exists(p), f"scripts/download_models.sh {eng.split('_')[0]}")
        if e["lora"]:
            check(f"[{eng}] loras/{e['lora']}", os.path.exists(os.path.join(comfy, "models", "loras", e["lora"])),
                  "scripts/download_models.sh dev")
    check("vae/" + base("VAE_FILE"), os.path.exists(os.path.join(comfy, "models", "vae", base("VAE_FILE"))),
          "scripts/download_models.sh klein9b")
    try:
        info = http_json(f"{COMFYUI_URL}/object_info", timeout=10)
        need = {n["class_type"] for n in graph("dev_turbo", "x", 1, ref_image="x.png").values()}
        missing = sorted(need - set(info))
        check("ComfyUI running with all nodes", not missing, f"missing nodes: {missing}")
    except (urllib.error.URLError, OSError):
        check("ComfyUI running", False, "scripts/comfy_up.sh")
    check("TRELLIS.2 installed", os.path.exists(os.path.join(VENDOR, "trellis-mac", ".venv", "bin", "python")),
          "scripts/setup_trellis.sh (optional)")
    try:
        blender_exe()
        check("Blender found", True)
    except SystemExit:
        check("Blender found", False, "install Blender or set BLENDER=...")
    sys.exit(0 if ok else 1)


# ---------------------------------------------------------------- cli

def main():
    ds, de = CFG["DEFAULT_STYLE"], CFG["DEFAULT_ENGINE"]
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("styles")
    c = sub.add_parser("concept")
    c.add_argument("name")
    c.add_argument("subject")
    c.add_argument("--style", default=ds)
    c.add_argument("--pose", default="tpose")
    c.add_argument("--engine", default=de, choices=engines())
    c.add_argument("--count", type=int, default=4)
    c.add_argument("--seed", type=int)
    c.add_argument("--size", type=int, default=1024)
    e = sub.add_parser("edit")
    e.add_argument("name")
    e.add_argument("image")
    e.add_argument("instruction")
    e.add_argument("--engine", default="klein9b", choices=engines())
    e.add_argument("--count", type=int, default=2)
    e.add_argument("--seed", type=int)
    e.add_argument("--size", type=int, default=1024)
    v = sub.add_parser("views")
    v.add_argument("name")
    v.add_argument("image")
    v.add_argument("--engine", default="klein9b", choices=engines())
    v.add_argument("--only", nargs="+", choices=list(common()["views"]))
    v.add_argument("--pose")
    v.add_argument("--note")
    v.add_argument("--seed", type=int)
    v.add_argument("--size", type=int, default=1024)
    m = sub.add_parser("model3d")
    m.add_argument("name")
    m.add_argument("image")
    m.add_argument("--pipeline-type", default="1024", choices=["512", "1024", "1024_cascade"])
    m.add_argument("--texture-size", type=int, default=1024, choices=[512, 1024, 2048])
    m.add_argument("--seed", type=int, default=42)
    b = sub.add_parser("blender")
    b.add_argument("name")
    bu = sub.add_parser("build")
    bu.add_argument("name")
    bu.add_argument("image")
    bu.add_argument("--views", action="store_true", help="also render the 4 views first (for review)")
    bu.add_argument("--engine", default="klein9b", choices=engines())
    bu.add_argument("--pipeline-type", default="1024", choices=["512", "1024", "1024_cascade"])
    bu.add_argument("--texture-size", type=int, default=1024, choices=[512, 1024, 2048])
    bu.add_argument("--seed", type=int)
    be = sub.add_parser("bench")
    be.add_argument("--engines", nargs="+", default=["klein9b", "dev", "dev_turbo"], choices=engines())
    sub.add_parser("doctor")
    a = p.parse_args()
    {"styles": cmd_styles, "concept": cmd_concept, "edit": cmd_edit, "views": cmd_views, "model3d": cmd_model3d,
     "blender": cmd_blender, "build": cmd_build, "bench": cmd_bench, "doctor": cmd_doctor}[a.cmd](a)


if __name__ == "__main__":
    main()
