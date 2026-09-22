@echo off
rem 离线安装依赖：从本目录 wheels/ 中安装，不访问外网
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  正在从本地 wheels 目录离线安装依赖...
echo ============================================
python -m pip install --no-index --find-links "%~dp0wheels" -r "%~dp0requirements.txt"
if errorlevel 1 (
  echo.
  echo [失败] 安装未完成。请确认：
  echo   1. 已安装 Python 3.8 及以上，且 python 命令可用；
  echo   2. wheels 目录内容完整。
) else (
  echo.
  echo [完成] 依赖安装成功。
)
pause
