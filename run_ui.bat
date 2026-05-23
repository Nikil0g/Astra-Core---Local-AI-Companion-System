@echo off
chcp 65001 >nul
title Astra Control Panel

echo ========================================
echo   Запуск Astra v0.2
echo ========================================
echo.

:: Переход в папку скрипта
cd /d %~dp0

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден. Установите Python 3.10+
    pause
    exit /b 1
)

:: Запуск UI
echo Запуск графического интерфейса...
python ui_main.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Не удалось запустить UI.
    echo Проверьте установку зависимостей (install_deps.bat)
    pause
)