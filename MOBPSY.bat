@echo off
setlocal EnableExtensions
title MobPsy - Panel de control
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0_mobpsy\MOBPSY.ps1"
exit /b %ERRORLEVEL%
