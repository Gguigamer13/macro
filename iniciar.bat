@echo off
title Auto Clicker
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -m autoclicker
) else (
    python -m autoclicker
)

if errorlevel 1 (
    echo.
    echo Nao foi possivel abrir o Auto Clicker.
    echo Instale o Python 3.10 ou mais novo em https://www.python.org/downloads/windows/
    echo e marque a opcao "Add Python to PATH".
    echo.
    pause
)
