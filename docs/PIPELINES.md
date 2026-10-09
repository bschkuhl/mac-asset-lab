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

## 3D mit Pixal3D (Standard) und Low-Poly
Pixal3D (SIGGRAPH 2026, Mac-Port `vendor/pixal3d-mac`, `scripts/setup_pixal3d.sh`) richtet Form und Textur pixelgenau am
Eingabebild aus. Im Vergleich mit TRELLIS am Papagei: Augen mit schwarzer Pupille, weißem Ring und Glanzpunkt wie im
Konzept (TRELLIS: braun), sauberer Schnabel, Gelb bleibt gelb. Ca. 8 min pro Modell; die Modelle schauen nach +Y und
werden beim Import gedreht. Pixal3Ds eigene Reduktion zerlegt dünne Teile bei wenigen Dreiecken (Test 1 500: nur ein
Flügelstück übrig), deshalb erzeugt es `PIXAL3D_FACES` (100 000) und `lowpoly` reduziert danach:

`blender/lowpoly.py` reduziert eine Kopie auf `--faces` (sonst `faces` des Stils), legt neue UVs an und überträgt die
Farbe: jedes Texel bekommt die Farbe des nächstgelegenen Punkts auf dem detaillierten Netz. (Blenders Strahl-Bake
verfehlt nach starker Reduktion die Oberfläche (schwarze Löcher) oder trifft die falsche Seite (Farben verschmiert).)
Material matt (Roughness 1), flach schattiert, GLB für Godot. Details wie Augen bleiben, weil sie in der Textur sitzen;
bei 1 500 Dreiecken verschmilzt der Schnabel noch mit dem Kopf, 3 000 ist sauber.

## 3D mit TRELLIS.2 (Mac-Port, `--engine3d trellis`)
`--pipeline-type 512` (schnell), `1024` (Standard), `1024_cascade` (am genauesten); `--texture-size 512|1024|2048`.
Der Port braucht ca. 18 GB Spitze, ca. 15 GB Gewichte (erster Lauf lädt sie). Ausgabe: GLB mit Basecolor, Metallic, Roughness.

**Dreiecke:** TRELLIS erzeugt intern ein dichtes Netz (Papagei: 3,2 Mio. Dreiecke) und vereinfacht es vor dem Texturbacken.
Das Ziel kommt aus `--faces`, sonst aus `faces` im Stil des Bildes (`lowpoly`: 3000), sonst 200 000 wie im Original.
`setup_trellis.sh` patcht dafür `generate.py` (Umgebungsvariable `TRELLIS_FACES`). Weil die Textur erst auf dem fertigen
Netz gebacken wird, braucht es danach keine eigene Reduktion. Test Papagei: 2 891 statt 190 k Dreiecke, GLB 1,5 statt 10 MB,
optisch fast gleich; nur dünne Teile (Schwanz von der Seite) werden noch flacher.

## Dateilayout
```
out/<name>/<name>_s<seed>.png (+ .json mit Prompt, Seed, Stil, Engine)
out/<name>/views/<name>_<view>_s<seed>.png
out/<name>/model/<name>_<pixal3d|trellis>.glb (+ .json), <name>_lowpoly.glb
out/<name>/blender/<name>.blend, <name>_lowpoly.blend
out/<name>/preview/preview_<front|front34|left|back|right>.png
```
Das ist dasselbe Layout wie `assets/concepts/<name>/` im Spiel-Repo (ohne `model/` und `blender/`, die nicht kopiert werden).

## Neues Modell oder Version eintragen
Nur `config/models.env` ändern (Repo, Datei, Commit). `scripts/download_models.sh` und `pipeline.py` lesen die Datei.
`./pipeline.py doctor` meldet fehlende Dateien.
