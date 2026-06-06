@echo off
chcp 65001 > nul
title Shaxsiy AI (Ollama) O'rnatish

echo.
echo ============================================
echo   Shaxsiy AI - O'rnatish (Ollama)
echo ============================================
echo.
echo Bu dastur Ollama va AI modelini yuklab o'rnatadi.
echo Internet aloqasi kerak (birinchi marta ~2-5 GB).
echo.

:: Ollama tekshirish
ollama --version > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama allaqachon o'rnatilgan.
    goto :model_install
)

echo [!] Ollama topilmadi. O'rnatilmoqda...
echo.
echo Ollama veb-sahifasi ochilmoqda...
start https://ollama.com/download

echo.
echo Ollama yuklab oling va o'rnating, keyin bu oynani yoping va qayta oching.
echo.
pause
exit /b 0

:model_install
echo.
echo Qaysi AI modelini o'rnatmoqchisiz?
echo.
echo   1) qwen2.5:3b   - Tez, 2 GB  (tavsiya - oddiy foydalanish)
echo   2) deepseek-r1:7b - Aqlli, 5 GB (tavsiya - murakkab vazifalar)
echo   3) qwen2.5:7b   - Yaxshi, 5 GB (ko'p til, shu jumladan O'zbek)
echo   4) phi3.5       - Tez, 2.5 GB (Microsoft modeli)
echo.
set /p choice="Tanlang (1-4): "

if "%choice%"=="1" set MODEL=qwen2.5:3b
if "%choice%"=="2" set MODEL=deepseek-r1:7b
if "%choice%"=="3" set MODEL=qwen2.5:7b
if "%choice%"=="4" set MODEL=phi3.5
if not defined MODEL set MODEL=qwen2.5:3b

echo.
echo [%MODEL%] yuklab olinmoqda...
echo Bu bir necha daqiqa yoki uzoqroq vaqt olishi mumkin.
echo.
ollama pull %MODEL%

if %errorlevel% neq 0 (
    echo.
    echo [XATO] Model yuklab olinmadi!
    echo Internet aloqasini tekshiring va qayta urinib ko'ring.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   AI modeli muvaffaqiyatli o'rnatildi!
echo ============================================
echo.
echo O'rnatilgan model: %MODEL%
echo.
echo Ishga tushirish uchun:
echo   ollama run %MODEL%
echo.
echo Endi START_BOT.bat ni ishga tushiring.
echo.
pause
