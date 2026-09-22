@echo off
rem Launch RandomSongs GUI, sharing the repo-level main_data
chcp 936 >nul
cd /d "%~dp0"
set "RANDOM_SONGS_DATA=%~dp0..\main_data"
set "EXE=%~dp0src\RandomSongs.App\bin\x64\Debug\net8.0-windows10.0.19041.0\win-x64\RandomSongs.App.exe"
if exist "%EXE%" (
  start "" "%EXE%"
) else (
  echo Building and running via dotnet run ...
  dotnet run --project "%~dp0src\RandomSongs.App\RandomSongs.App.csproj"
)
