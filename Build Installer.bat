@echo off
title Tools Downloader - Build Installer
echo ========================================================
echo        Building Tools Downloader Setup Installer
echo ========================================================
echo.

if not exist "dist\Tools Downloader.exe" (
    echo [ERROR] 'dist\Tools Downloader.exe' not found!
    echo Please run 'Build App.bat' first to build the main executable.
    echo.
    pause
    exit /b 1
)

set ISCC=""
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else (
    where iscc >nul 2>&1
    if not errorlevel 1 (
        set ISCC=iscc
    )
)

if %ISCC%=="" (
    echo [ERROR] Inno Setup compiler (ISCC.exe) not found!
    echo Please install Inno Setup 6 from: https://jrsoftware.org/isdl.php
    echo or run: winget install JRSoftware.InnoSetup
    echo.
    pause
    exit /b 1
)

echo Compiling setup package using Inno Setup...
%ISCC% "installer.iss"

if errorlevel 1 (
    echo.
    echo [ERROR] Installer build failed!
    pause
    exit /b 1
)

echo.
echo ========================================================
echo [SUCCESS] Installer created successfully!
echo Output file: dist\Tools_Downloader_Setup_v1.0.exe
echo ========================================================
echo.
pause

