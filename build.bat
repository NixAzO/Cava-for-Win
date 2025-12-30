@echo off
echo Building AudioVisualizer...
pip install pyinstaller
pyinstaller --clean visualizer.spec
echo.
echo Done! Check dist\AudioVisualizer.exe
pause
