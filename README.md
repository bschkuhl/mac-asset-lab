# Mac Asset Lab

Lokale Pipeline für den Mac (Apple Silicon, M2 mit 64 GB): **Text → Konzeptbild → 4 Ansichten → 3D-Modell → Blender**.
Gedacht als Ergänzung zum Spiel-Repo *Monkey on an Island*, aber eigenständig. Alles läuft nativ, ohne Cloud-Kosten.

> **Warum kein Docker?** Docker auf dem Mac läuft in einer Linux-VM ohne Zugriff auf die GPU (Metal/MPS). ComfyUI
> und TRELLIS würden dort nur auf der CPU laufen, viele Male langsamer. Deshalb: pinned Setup-Skripte statt Container.
> Für einen Linux-Rechner mit NVIDIA-Karte kann später ein Dockerfile ergänzt werden.

## Auf dem Mac in 6 Schritten

```bash
git clone <dieses-repo> mac-asset-lab && cd mac-asset-lab
scripts/setup_mac.sh --trellis     # ComfyUI (gepinnt), GGUF-Node, Python-Env, TRELLIS.2-Mac-Port
hf auth login                      # einmalig; Lizenzen akzeptieren (siehe unten)
scripts/download_models.sh klein9b # ca. 27 GB; später: dev (ca. 60 GB)
scripts/comfy_up.sh                # ComfyUI im Hintergrund
./pipeline.py doctor               # prüft alles
./pipeline.py concept my_banana "a single ripe banana" --style prop --pose object --count 4
```

Lizenzen/Zugriff auf HuggingFace: Für TRELLIS: <https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m>
und <https://huggingface.co/briaai/RMBG-2.0> anfragen. FLUX.2 [dev]/klein 9B stehen unter der FLUX Non-Commercial
License (für private Zwecke in Ordnung; die erzeugten Bilder und Modelle dürfen genutzt werden).

## Der Ablauf (Details: `docs/PIPELINES.md`)

| Schritt | Befehl | Modell | Ergebnis |
|---|---|---|---|
| 0 Stil wählen | `./pipeline.py styles` | – | Liste der Stile |
| 1 Konzept | `./pipeline.py concept <name> "<subject>" --style character --pose tpose` | klein9b (oder dev) | `out/<name>/<name>_s<seed>.png` |
| 2 Korrektur | `./pipeline.py edit <name> <bild> "Remove the long tail."` | klein9b | `…_e<seed>.png` |
| 3 Ansichten | `./pipeline.py views <name> <bild>` | klein9b | `out/<name>/views/…` |
| 4 3D | `./pipeline.py model3d <name> <bild> --pipeline-type 1024` | TRELLIS.2 | `out/<name>/model/<name>_trellis.glb` |
| 5 Blender | `./pipeline.py blender <name>` | – | `out/<name>/blender/<name>.blend` |
| alles ab Bild | `./pipeline.py build <name> <bild> [--views]` | – | Schritte 3–5 |

## Stil vorher festlegen

Stile sind Dateien in `styles/*.json` (`name`, `description`, `prompt`). Der Dateiname ist der Stil-Name.
Gestartet wird mit dem **aktuellen Stil des Spiels**: `character` (Standard für neue Figuren), `hero`, `lowpoly`, `prop`
(Objekte ohne Gesicht). Einen neuen Stil anlegen = Datei kopieren, `prompt` ändern, dann `--style <neuer_name>`.
Posen, Rahmen-Text und Ansichten stehen in `styles/_common.json`. Standard-Stil ändern: `DEFAULT_STYLE` in
`config/models.env`.

## Ausgabe für Blender

`./pipeline.py blender <name>` importiert die GLB headless (`blender/import_glb.py`): Objekt `<CamelName>`, Transformationen
angewendet, Ursprung am Boden in der Mitte (Z = 0), glatte Schattierung, Texturen im .blend gepackt, Bericht mit
Dreiecken und Maßen. Es wird **nichts reduziert**; das Spiel-LOD (27 k / 5–10 k / 1–3 k Dreiecke, Textur 1024/512) macht
danach das Spiel-Repo. Blender wird gefunden über `BLENDER=…`, `PATH` oder `/Applications/Blender.app`.

## Zurück ins Spiel-Repo

```bash
scripts/export_to_game.sh <name> ~/Projekte/monkey-on-an-island
# danach, im Spiel-Repo (der Befehl wird ausgegeben):
python3 assets/scripts/model_pipeline.py import <name> assets/glb/<name>_trellis_download.glb --tag trellis
python3 assets/scripts/model_pipeline.py lod <name>
```

## Tests und Messung

- `python3 tests/test_graphs.py` (offline; mit `LIVE=1` und laufendem ComfyUI prüft es zusätzlich alle Node-Klassen).
- `./pipeline.py bench` erzeugt dieselben drei Motive (Banane, Goblin, Pferd) mit klein9b, dev und dev_turbo und schreibt
  die Zeiten nach `out/bench.md`. Danach entscheidest du, welche Engine Standard wird (`DEFAULT_ENGINE`).

## Status (ehrlich)

Auf dem Linux-Rechner getestet: Graph-Aufbau, alle ComfyUI-Nodes vorhanden, Konzept/Edit/Views gegen ein echtes ComfyUI
(mit klein 4B als Platzhalter), Blender-Import mit einem echten GLB. **Auf dem Mac nicht getestet:** Setup-Skripte,
Modell-Downloads, MPS-Lauf, FLUX.2 dev, TRELLIS.2. Bekannte Risiken: fp8-Gewichte laufen auf MPS eventuell nicht (deshalb
nutzt klein9b den bf16-Textencoder); dev braucht den 35-GB-Textencoder oder eine GGUF-Variante (siehe `docs/PIPELINES.md`).
