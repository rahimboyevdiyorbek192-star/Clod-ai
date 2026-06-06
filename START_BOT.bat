@echo off
chcp 65001 > nul
title KiberStansiya - Bot ishlamoqda

echo.
echo ============================================
echo   KiberStansiya Bot - Ishga tushirilmoqda
echo ============================================
echo.

:: Virtual muhit tekshirish
if not exist "venv\Scripts\activate.bat" (
    echo [XATO] Virtual muhit topilmadi!
    echo Avval INSTALL.bat ni ishga tushiring.
    pause
    exit /b 1
)

:: config.py tekshirish
if not exist "bot\config.py" (
    echo [XATO] bot\config.py topilmadi!
    echo API_ID, API_HASH va BOT_TOKEN ni kiriting.
    pause
    exit /b 1
)

:: Virtual muhitni faollashtirish
call venv\Scripts\activate.bat

echo [OK] Virtual muhit faollashtirildi.
echo.
echo Bot ishlamoqda... (to'xtatish uchun Ctrl+C bosing)
echo.
cd bot
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [XATO] Bot to'xtadi! Xato kodi: %errorlevel%
    echo bot\config.py dagi API_ID, API_HASH, BOT_TOKEN ni tekshiring.
)
echo.
pause
