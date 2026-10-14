@echo off
title Push Cloud-Student-Task-Manager to GitHub
color 0b

echo =====================================================================
echo    Pushing Cloud-Student-Task-Manager to GitHub
echo    Target: https://github.com/shreyashbhatt/Cloud-Student-Task-Manager
echo =====================================================================
echo.

git\cmd\git.exe push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =====================================================================
    echo   SUCCESS! Your project is live on GitHub at:
    echo   https://github.com/shreyashbhatt/Cloud-Student-Task-Manager
    echo =====================================================================
) else (
    echo.
    echo =====================================================================
    echo   If you saw an authentication or repository not found error:
    echo   1. Ensure you created the empty repo at:
    echo      https://github.com/new?name=Cloud-Student-Task-Manager
    echo   2. Sign in via your browser if prompted by Git Credential Manager.
    echo =====================================================================
)

echo.
pause
