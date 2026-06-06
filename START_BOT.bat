@echo off
chcp 65001 > nul
title KiberStansiya - Bot ishlamoqda

echo.
echo ============================================
echo   KiberStansiya Bot - Ishga tushirilmoqda
echo ============================================
echo.

:: config.py tekshirish (asosiy papkada)
if not exist "config.py" (
    echo [XATO] config.py topilmadi!
    echo config.py faylida API_ID, API_HASH, BOT_TOKEN bor ekanligini tekshiring.
    pause
    exit /b 1
)

:: main.py tekshirish
if not exist "main.py" (
    echo [XATO] main.py topilmadi!
    echo .bat fayl loyiha papkasida bo'lishi kerak.
    pause
    exit /b 1
)

echo [OK] Fayllar topildi.
echo.

:: Virtual muhit bo'lsa foydalanish, bo'lmasa oddiy Python
if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual muhit faollashtirilmoqda...
    call venv\Scripts\activate.bat
) else (
    echo [!] Virtual muhit topilmadi, tizim Python ishlatilmoqda.
)

echo.
echo Bot ishlamoqda... (to'xtatish uchun Ctrl+C bosing)
echo.
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [XATO] Bot to'xtadi! Xato kodi: %errorlevel%
    echo config.py dagi API_ID, API_HASH, BOT_TOKEN ni tekshiring.
)
echo.
pause
