@echo off
cd "%~dp0\..\src"
chcp 65001 >NUL
uv run main.py %*
