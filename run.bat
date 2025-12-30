@echo off
title Audio Visualizer

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found!
    echo Download Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit
)

echo Installing dependencies...
pip install numpy PyQt5 sounddevice -q

echo Starting...
pythonw visualizer.py
