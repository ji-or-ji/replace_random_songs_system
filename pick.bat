@echo off
chcp 936 >nul
rem ClassIsland integration: silent pick, result to stdout
cd /d "%~dp0"
python run.py %*
