@echo off
python "%~dp0windows_optimizer.pyw"
if errorlevel 1 (
    echo.
    echo The app could not run. Read the error above.
    pause
)
