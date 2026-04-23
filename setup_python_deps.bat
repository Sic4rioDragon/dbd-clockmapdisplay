@echo off
cd /d "%~dp0"

echo Installing required Python packages...
python -m pip install --upgrade pip
python -m pip install mss pillow pytesseract rapidfuzz

echo.
echo Done.
pause