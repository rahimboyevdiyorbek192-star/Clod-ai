@echo off
chcp 65001 > nul
title KiberStansiya - Web Platforma

echo.
echo ============================================
echo   KiberStansiya - Web Platforma
echo ============================================
echo.

:: Virtual muhit tekshirish
if not exist "venv\Scripts\activate.bat" (
    echo [XATO] Virtual muhit topilmadi!
    echo Avval INSTALL.bat ni ishga tushiring.
    pause
    exit /b 1
)

:: Virtual muhitni faollashtirish
call venv\Scripts\activate.bat
echo [OK] Virtual muhit faollashtirildi.
echo.

:: ANTHROPIC_API_KEY tekshirish
if "%ANTHROPIC_API_KEY%"=="" (
    echo [!] ANTHROPIC_API_KEY topilmadi.
    set /p ANTHROPIC_API_KEY="Anthropic API kalitini kiriting: "
    if "%ANTHROPIC_API_KEY%"=="" (
        echo [XATO] API kalit kiritilmadi!
        pause
        exit /b 1
    )
)

echo [OK] ANTHROPIC_API_KEY topildi.
echo.
echo Web server ishlamoqda...
echo Brauzerda oching: http://localhost:8000
echo.
echo To'xtatish uchun: Ctrl+C
echo.
python main.py

echo.
pause
