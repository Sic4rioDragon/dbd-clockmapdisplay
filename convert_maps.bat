@echo off
cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File "%~dp0convert_maps.ps1"

pause