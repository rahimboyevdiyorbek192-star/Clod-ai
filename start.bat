@echo off
chcp 65001 >nul
title Ustoz.ai Bot

:: .env tekshirish
if not exist .env (
    echo [XATO] .env fayl topilmadi!
    echo install.bat ni ishga tushuring.
    pause
    exit /b 1
)

:: BOT_TOKEN tekshirish
findstr /i "BOT_TOKEN=your_telegram" .env >nul 2>&1
if not errorlevel 1 (
    echo [XATO] BOT_TOKEN hali o'rnatilmagan!
    echo .env faylni oching va BOT_TOKEN ga bot tokeningizni kiriting.
    echo.
    notepad .env
    pause
    exit /b 1
)

echo ============================================
echo   Ustoz.ai Bot ishga tushmoqda...
echo   To'xtatish uchun: Ctrl+C
echo ============================================
echo.

:loop
python bot.py
if errorlevel 1 (
    echo.
    echo [!] Bot to'xtadi. 5 soniyadan keyin qayta ishga tushadi...
    timeout /t 5 /nobreak >nul
    goto loop
)
