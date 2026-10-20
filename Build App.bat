@echo off
title Tools Downloader
echo Cleaning previous builds...

set PYINSTALLER=py -m PyInstaller
if exist ".venv\Scripts\pyinstaller.exe" (
    set PYINSTALLER=.venv\Scripts\pyinstaller.exe
)

%PYINSTALLER% --noconsole --onefile --clean --noconfirm ^
--icon="assets\icon.ico" ^
--add-data "bin\ffmpeg.exe;bin" ^
--add-data "bin\ffprobe.exe;bin" ^
--add-data "bin\ffplay.exe;bin" ^
--add-data "bin\yt-dlp.exe;bin" ^
--add-data "assets\icon.png;assets" ^
--add-data "assets\icon.ico;assets" ^
--hidden-import "yt_dlp" ^
--collect-all "yt_dlp" ^
--name "Tools Downloader" ^
"main.py"

if errorlevel 1 (
    echo.
    echo Build failed.
    pause
    exit /b 1
)

if not exist "dist\bin" mkdir "dist\bin"

if exist "bin\yt-dlp.exe" (
    copy /Y "bin\yt-dlp.exe" "dist\yt-dlp.exe" >nul
    copy /Y "bin\yt-dlp.exe" "dist\bin\yt-dlp.exe" >nul
) else if exist "yt-dlp.exe" (
    copy /Y "yt-dlp.exe" "dist\yt-dlp.exe" >nul
)

echo.
echo ---------------------------------------------------
echo Build Complete! Check the 'dist' folder.
echo ---------------------------------------------------
pause
