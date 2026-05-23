@echo off
chcp 65001 >nul
title Установка зависимостей Astra

echo ========================================
echo   Установка зависимостей Astra v0.2
echo ========================================
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден.
    echo Установите Python 3.10 или новее с python.org
    echo Обязательно поставьте галочку "Add Python to PATH"
    pause
    exit /b 1
)

echo Используется: python
python --version
echo.

:: Обновление pip
echo Обновление pip...
python -m pip install --upgrade pip
echo.

:: Установка зависимостей
echo Установка пакетов...
python -m pip install requests tzdata pyside6 sounddevice scipy faster-whisper keyboard pygame win10toast numpy

if errorlevel 1 (
    echo.
    echo [ПРЕДУПРЕЖДЕНИЕ] Некоторые пакеты не установились.
    echo Вы всё равно можете использовать текстовый чат и UI.
) else (
    echo.
    echo Установка завершена успешно!
)

echo.
echo Для запуска интерфейса выполните run_ui.bat
pause