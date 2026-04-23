@echo off
cd /d "%~dp0"

if not exist output mkdir output
if not exist assets\maps mkdir assets\maps
if not exist originals mkdir originals
if not exist overlay mkdir overlay
if not exist bot mkdir bot

echo Starting DBD clock map display bot...
echo.
python bot\map_ocr_to_obs.py

pause