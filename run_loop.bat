@echo off
:: Auto-restart script for Dodge the Lasers
:: If the game crashes, it relaunches automatically after 3 seconds.
:: Press Ctrl+C in this terminal window to stop the restart loop.

echo ============================================
echo   DODGE THE LASERS - Auto-Restart Mode
echo   Press Ctrl+C to stop the restart loop
echo ============================================

:loop
echo.
echo [%date% %time%] Starting game...
python main.py
echo.
echo [%date% %time%] Game exited with code %errorlevel%.
echo Restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
