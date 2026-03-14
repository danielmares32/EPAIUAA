@echo off
REM Build EPA Dashboard .exe for Windows

echo ========================================
echo   EPA Dashboard - EXE Builder
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [2/4] Cleaning old build folders...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo [3/4] Building executable...
pyinstaller --name EPA_Dashboard ^
    --windowed ^
    --onefile ^
    --clean ^
    --add-data "assets;assets" ^
    --add-data "config;config" ^
    --add-data "qt_views;qt_views" ^
    --add-data "services;services" ^
    --add-data "app;app" ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    --hidden-import rake_nltk ^
    --hidden-import keybert ^
    --hidden-import yake ^
    --hidden-import spacy ^
    --hidden-import requests ^
    main.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [4/4] Creating portable package...
if not exist "dist\EPA_Dashboard_Portable" mkdir "dist\EPA_Dashboard_Portable"
copy "dist\EPA_Dashboard.exe" "dist\EPA_Dashboard_Portable\" >nul
if exist "config" xcopy "config" "dist\EPA_Dashboard_Portable\config\" /E /I /Y >nul

echo.
echo ========================================
echo   Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\EPA_Dashboard.exe
echo Portable package: dist\EPA_Dashboard_Portable\
echo.
echo You can now distribute the .exe file!
echo.
pause
