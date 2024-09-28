@echo off
echo Installing dependencies...
echo.
pip install yt-dlp

timeout /t 2 /nobreak > nul
cls
cd /d "%~dp0src"
python __main__.py
pause