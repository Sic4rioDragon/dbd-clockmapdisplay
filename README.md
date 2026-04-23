# dbd-clockmapdisplay

Small Windows-based Dead by Daylight map OCR overlay for OBS.

This setup watches the in-game map name text, tries to detect the current map with Tesseract OCR, and serves a local overlay that OBS can show as a Browser Source.

## current goal

This version is meant to work cleanly on Windows with a simple local setup.

It does **not** use the original Scala/Cygwin/Pango setup that parts of this project were inspired by.

## folder layout

```text
dbd-clockmapdisplay/
│
├─ README.md
├─ run_bot.bat
├─ setup_python_deps.bat
├─ convert_maps.bat
├─ convert_maps.ps1
│
├─ bot/
│  ├─ map_ocr_to_obs.py
│  └─ settings.json
│
├─ overlay/
│  └─ overlay.html
│
├─ assets/
│  └─ maps/
│
├─ originals/
│
└─ output/