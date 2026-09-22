@echo off
chcp 936 >nul
rem Offline install: install deps from local wheels/ without network
cd /d "%~dp0"
echo ============================================
echo  正在从本地 wheels 目录离线安装依赖...
echo ============================================
python -m pip install --no-index --find-links "%~dp0wheels" -r "%~dp0requirements.txt"
if errorlevel 1 (
  echo.
  echo [FAILED] Install not completed. Check python and the wheels folder.
) else (
  echo.
  echo [DONE] Dependencies installed.
)
pause
