@echo off
title Push Tools Downloader to GitHub
echo ========================================================
echo        Pushing Tools Downloader to GitHub
echo ========================================================
echo.

set GIT_EXE="%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
if not exist %GIT_EXE% (
    set GIT_EXE=git
)

%GIT_EXE% push -u origin main

if errorlevel 1 (
    echo.
    echo --------------------------------------------------------
    echo If GitHub rejected because a README exists on remote,
    echo you can force push to overwrite:
    echo --------------------------------------------------------
    set /p FORCE="Do you want to force push? (Y/N): "
    if /i "%FORCE%"=="Y" (
        %GIT_EXE% push -u origin main --force
    )
)

echo.
echo ========================================================
echo Process Finished.
echo ========================================================
pause

