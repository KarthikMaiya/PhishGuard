@echo off
cd /d "%~dp0"

echo Starting PhishGuard...
echo Using Python:
where python
echo.

python launcher.py

echo.
echo ================================
echo PROGRAM EXITED - SHOWING ERROR
echo ================================
pause
