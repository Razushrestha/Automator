@echo off
echo Building Bulk Sender .exe...
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --windowed --name "Sendorar" --icon=auto.ico app.py
echo.
echo ✅ BUILD COMPLETE!
echo 📁 Find Sendora.exe in 'dist' folder
pause