@echo off
chcp 65001 > nul
title KiberStansiya - Bot ishlamoqda

echo.
echo ============================================
echo   KiberStansiya Bot - Ishga tushirilmoqda
echo ============================================
echo.

:: config.py tekshirish
if not exist "bot\config.py" (
    echo [XATO] bot\config.py topilmadi!
    echo INSTALL.bat ni avval ishga tushiring.
    pause
    exit /b 1
)

:: Kerakli kutubxonalar tekshirish
python -c "import telethon" > nul 2>&1
if %errorlevel% neq 0 (
    echo [XATO] Kerakli kutubxonalar o'rnatilmagan!
    echo INSTALL.bat ni ishga tushiring.
    pause
    exit /b 1
)

echo [OK] Barcha tekshiruvlar o'tdi.
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
