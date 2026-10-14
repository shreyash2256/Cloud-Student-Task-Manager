@echo off
title Push Cloud-Student-Task-Manager to GitHub
color 0b

echo =====================================================================
echo    Pushing Cloud-Student-Task-Manager to GitHub
echo    Target: https://github.com/shreyash2256/Cloud-Student-Task-Manager
echo =====================================================================
echo.

git\cmd\git.exe push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =====================================================================
    echo   SUCCESS! Your project is live on GitHub at:
    echo   https://github.com/shreyash2256/Cloud-Student-Task-Manager
    echo =====================================================================
) else (
    echo.
    echo =====================================================================
    echo   Notice: If the repository does not exist on your account yet:
    echo   1. Click: https://github.com/new?name=Cloud-Student-Task-Manager
    echo   2. Click the green "Create repository" button.
    echo   3. Run this file again!
    echo =====================================================================
)

echo.
pause
