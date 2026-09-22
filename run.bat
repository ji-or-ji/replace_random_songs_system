@echo off
rem 启动随机点歌系统（双击即可运行）
cd /d "%~dp0"
python run.py
if errorlevel 1 pause
