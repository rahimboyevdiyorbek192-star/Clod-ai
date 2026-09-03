@echo off
chcp 65001 >nul
title Ustoz.ai Bot - O'rnatish

echo ============================================
echo   Ustoz.ai Bot - O'rnatish boshlandi
echo ============================================
echo.

:: Python borligini tekshirish
python --version >nul 2>&1
if errorlevel 1 (
    echo [XATO] Python topilmadi!
    echo.
    echo Python ni o'rnating: https://www.python.org/downloads/
    echo O'rnatishda "Add Python to PATH" katagiga belgi qo'ying!
    echo.
    pause
    exit /b 1
)

echo [OK] Python topildi
python --version
echo.

:: pip ni yangilash
echo [1/3] pip yangilanmoqda...
python -m pip install --upgrade pip --quiet
echo [OK] pip yangilandi
echo.

:: Kutubxonalar o'rnatish
echo [2/3] Kutubxonalar o'rnatilmoqda...
pip install -r requirements.txt
if errorlevel 1 (
    echo [XATO] Kutubxonalar o'rnatilmadi!
    pause
    exit /b 1
)
echo [OK] Kutubxonalar o'rnatildi
echo.

:: Playwright Chromium o'rnatish
echo [3/3] Chromium (brauzer) o'rnatilmoqda...
playwright install chromium
if errorlevel 1 (
    echo [XATO] Chromium o'rnatilmadi!
    pause
    exit /b 1
)
echo [OK] Chromium o'rnatildi
echo.

:: .env fayl tekshirish
if not exist .env (
    copy .env.example .env >nul
    echo [!] .env fayl yaratildi.
    echo     BOT_TOKEN ni kiriting - .env faylni Notepad da oching:
    echo.
    echo     Notepad .env
    echo.
    notepad .env
) else (
    echo [OK] .env fayl mavjud
)

echo.
echo ============================================
echo   O'rnatish muvaffaqiyatli yakunlandi!
echo   Botni ishga tushurish uchun: start.bat
echo ============================================
echo.
pause
