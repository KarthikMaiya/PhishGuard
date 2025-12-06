@echo off
cd /d "C:\Users\Karthik Maiya\Desktop\PhishGuard_v2"

call C:\Users\Karthik Maiya\anaconda3\Scripts\activate.bat phishguard_env

start "" /B python launcher.py

exit
