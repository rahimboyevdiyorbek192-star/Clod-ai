@echo off
chcp 65001 > nul
title KiberStansiya - O'rnatish

echo.
echo ============================================
echo   KiberStansiya Bot - O'rnatish
echo ============================================
echo.

:: Python tekshirish
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [XATO] Python topilmadi!
    echo Iltimos, https://python.org dan Python 3.10+ yuklab o'rnating.
    echo O'rnatishda "Add Python to PATH" ni belgilang.
    pause
    exit /b 1
)
echo [OK] Python topildi.
echo.

:: Virtual muhit yaratish (boshqa loyihalar bilan ziddiyatni oldini oladi)
if exist "venv\" (
    echo [OK] Virtual muhit allaqachon mavjud.
) else (
    echo Virtual muhit yaratilmoqda...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [XATO] Virtual muhit yaratib bo'lmadi!
        pause
        exit /b 1
    )
    echo [OK] Virtual muhit yaratildi.
)
echo.

:: Virtual muhitni faollashtirish
call venv\Scripts\activate.bat

:: pip yangilash
echo pip yangilanmoqda...
python -m pip install --upgrade pip --quiet

:: Kerakli kutubxonalarni o'rnatish
echo Kerakli kutubxonalar o'rnatilmoqda...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [XATO] Kutubxonalar o'rnatishda muammo yuz berdi!
    echo Internet aloqasini tekshiring va qayta urinib ko'ring.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   O'rnatish muvaffaqiyatli yakunlandi!
echo ============================================
echo.
echo Keyingi qadam:
echo   1. bot\config.py faylini oching
echo   2. API_ID, API_HASH, BOT_TOKEN ni kiriting
echo   3. START_BOT.bat ni ishga tushiring
echo.
pause
