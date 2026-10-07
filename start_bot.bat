@echo off
title Link2Media Telegram Bot
cd /d "%~dp0"
echo ========================================================
echo   Starting Link2Media Telegram Bot (@OsncovertBot)
echo ========================================================
set PYTHONPATH=.
call .venv\Scripts\activate.bat
python -m link2media.main
pause
