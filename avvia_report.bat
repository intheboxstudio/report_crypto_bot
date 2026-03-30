@echo off
echo === Avvio Report Crypto Bot ===
echo.

set PYTHONIOENCODING=utf-8
set CHROME_LOG_FILE=nul
python report_crypto.py 2>nul

exit
