@echo off
cd /d "%~dp0"

REM ---- HARD RESET ----
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM mitmdump.exe >nul 2>&1

echo Starting PhishGuard... > phishguard_startup.log

REM ---- ACTIVATE CONDA ----
call "C:\Users\Karthik Maiya\anaconda3\Scripts\activate.bat" phishguard_env >> phishguard_startup.log 2>&1

REM ---- START ANALYZER ----
start "" /b cmd /c "python analyzer\serve_ml.py >> analyzer_bg.log 2>&1"

timeout /t 8 >nul

REM ---- START MITMPROXY (FIXED QUOTING) ----
start "" /b cmd /c ^
""C:\Users\Karthik Maiya\anaconda3\envs\phishguard_env\Scripts\mitmdump.exe" ^
-s proxy_simple.py --listen-port 8080 >> mitmproxy_bg.log 2>&1"

timeout /t 6 >nul

REM ---- START CHROME THROUGH PROXY ----
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
--proxy-server="http=127.0.0.1:8080;https=127.0.0.1:8080" ^
--ignore-certificate-errors ^
--user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data"

exit
