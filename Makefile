.PHONY: setup models-klein models-dev trellis up down doctor test bench
setup:        ; scripts/setup_mac.sh
trellis:      ; scripts/setup_trellis.sh
models-klein: ; scripts/download_models.sh klein9b
models-dev:   ; scripts/download_models.sh dev
up:           ; scripts/comfy_up.sh
down:         ; scripts/comfy_down.sh
doctor:       ; ./pipeline.py doctor
test:         ; python3 tests/test_graphs.py
bench:        ; ./pipeline.py bench
