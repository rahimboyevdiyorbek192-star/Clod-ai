@echo off
chcp 65001 > nul
title KiberStansiya - Web Platforma

echo.
echo ============================================
echo   KiberStansiya - Web Platforma
echo ============================================
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

:: Uvicorn tekshirish
python -c "import uvicorn" > nul 2>&1
if %errorlevel% neq 0 (
    echo [XATO] Kerakli kutubxonalar o'rnatilmagan!
    echo INSTALL.bat ni ishga tushiring.
    pause
    exit /b 1
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
