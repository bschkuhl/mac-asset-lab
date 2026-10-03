# Pipelines im Detail

## Engines (Bildmodelle)

| Engine | Dateien (`config/models.env`) | Schritte | RAM (geladen, grob) | Zweck |
|---|---|---|---|---|
| `klein9b` | UNet GGUF Q8 (10 GB), Qwen3-8B bf16 (16 GB), VAE | 4, kein Guidance | ca. 27 GB | Standard auf dem Mac, bestes Bearbeiten mit Referenz |
| `dev` | UNet GGUF Q5_K_M (24 GB), Mistral-3-small Textencoder, VAE | 20, Guidance 4 | 24 GB + Encoder | beste Qualität, langsam |
| `dev_turbo` | wie dev + Turbo-LoRA (2,8 GB) | 8, Guidance 4 | wie dev | dev in etwa 2,5-mal weniger Schritten |

Die Graphen entsprechen den offiziellen ComfyUI-Vorlagen (Image Edit Flux.2 Dev / Klein 9B). Edit-Modus = das Referenzbild wird
VAE-kodiert und per `ReferenceLatent` an die Konditionierung gehängt.

### dev auf dem Mac (experimentell)
Der Mistral-Textencoder ist das Problem: `fp8` (18 GB) und `fp4_mixed` (12 GB) brauchen Float8, das MPS bei älteren
PyTorch-Versionen nicht kennt. Der `bf16`-Encoder (35,6 GB) plus UNet (24 GB) passt nur knapp in 64 GB; macOS gibt der GPU
standardmäßig etwa 75 %. Reihenfolge der Versuche:
1. `sudo sysctl iogpu.wired_limit_mb=57344`, dann `COMFY_ARGS="--lowvram" scripts/comfy_up.sh`, `--engine dev`.
2. Kleineres UNet (`DEV_UNET_FILE=flux2-dev-Q4_K_M.gguf`).
3. Textencoder als GGUF (ComfyUI-GGUF kann Mistral erkennen; passende Datei muss getestet werden; bisher nicht geprüft).
Läuft nichts davon, bleibt `klein9b` der Standard; der Qualitätsabstand (Arena-Elo etwa 1154 gegen 1120) ist moderat.

## Posen und Ansichten
`styles/_common.json`: `poses` (tpose, humanoid, quadruped, hexapod, wings, spread, flippers, object), `pose_hold` (Pose in
den Ansichten halten), `views` (front, left, back, right), `framing` (neutrales Licht, einfarbiger Hintergrund).
Anatomie-Regel des Spiel-Projekts: **Körperteile und Ansatzpunkte jedes Bildes zählen**, bevor es weiterverwendet wird.

## 3D mit TRELLIS.2 (Mac-Port)
`--pipeline-type 512` (schnell), `1024` (Standard), `1024_cascade` (am genauesten); `--texture-size 512|1024|2048`.
Der Port braucht ca. 18 GB Spitze, ca. 15 GB Gewichte (erster Lauf lädt sie), keine Lochfüllung (cumesh fehlt), Mesh wird
von ca. 800 k auf 200 k Flächen vereinfacht. Ausgabe: GLB mit Basecolor, Metallic, Roughness.

## Dateilayout
```
out/<name>/<name>_s<seed>.png (+ .json mit Prompt, Seed, Stil, Engine)
out/<name>/views/<name>_<view>_s<seed>.png
out/<name>/model/<name>_trellis.glb (+ .json)
out/<name>/blender/<name>.blend
```
Das ist dasselbe Layout wie `assets/concepts/<name>/` im Spiel-Repo (ohne `model/` und `blender/`, die nicht kopiert werden).

## Neues Modell oder Version eintragen
Nur `config/models.env` ändern (Repo, Datei, Commit). `scripts/download_models.sh` und `pipeline.py` lesen die Datei.
`./pipeline.py doctor` meldet fehlende Dateien.
