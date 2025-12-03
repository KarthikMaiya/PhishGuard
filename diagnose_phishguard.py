import subprocess
import socket
import sys
import os

def run(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True, timeout=10)
    except subprocess.CalledProcessError as e:
        out = f"ERROR (exit {e.returncode}):\n{e.output}"
    except Exception as e:
        out = f"EXCEPTION: {e}"
    return out

print("=== PhishGuard Diagnostic ===\n")

# 1) Check mitmdump / mitmproxy processes
print("1) mitmproxy / mitmdump processes:")
print(run('tasklist /FI "IMAGENAME eq mitmdump.exe" /FO LIST'))
print(run('tasklist /FI "IMAGENAME eq mitmproxy.exe" /FO LIST'))

# 2) Check listening ports for 8080 (IPv4)
print("\n2) netstat for port 8080 (listening entries):")
print(run('netstat -ano | findstr /R /C:":8080\\b"'))

# 3) Test TCP connect to 127.0.0.1:8080
print("\n3) TCP connect test to 127.0.0.1:8080:")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(3)
try:
    s.connect(("127.0.0.1", 8080))
    print("TCP connect to 127.0.0.1:8080: SUCCESS (socket opened)")
    try:
        s.shutdown(socket.SHUT_RDWR)
    except:
        pass
    s.close()
except Exception as e:
    print(f"TCP connect to 127.0.0.1:8080: FAILED ({e})")

# 4) Chrome processes and command lines (WMIC)
print("\n4) Chrome processes and command lines (WMIC):")
print(run('wmic process where "name=\'chrome.exe\'" get ProcessId,CommandLine /FORMAT:LIST'))

# 5) Verify Chrome shortcut launched with --proxy-server (search running command lines)
print("\n5) Searching for --proxy-server in running processes' command lines (simple search):")
wm = run('wmic process where "name=\'chrome.exe\'" get CommandLine /FORMAT:LIST')
if "--proxy-server" in wm:
    print("Found --proxy-server in a chrome.exe command line.")
else:
    print("No --proxy-server flag found in chrome.exe command lines (or output not available).")
print(wm)

# 6) Check Windows user proxy registry keys (HKCU Internet Settings)
print("\n6) Windows Internet Settings (HKCU) - ProxyEnable and ProxyServer:")
print(run('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable'))
print(run('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer'))

# 7) Check environment variables commonly used for proxies
print("\n7) Environment variables (HTTP_PROXY / HTTPS_PROXY / ALL_PROXY):")
for var in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"):
    print(f"{var} = {os.environ.get(var)!r}")

# 8) Show recent launcher.py and start_chrome_and_guard.bat (if present) - print top lines for quick review
print("\n8) Show first 200 lines of launcher.py (if present):")
try:
    with open("launcher.py", "r", encoding="utf-8") as f:
        print("----- launcher.py -----")
        for i, line in enumerate(f):
            if i>199:
                break
            print(line.rstrip())
except Exception as e:
    print(f"Could not open launcher.py: {e}")

print("\n9) Show first 200 lines of start_chrome_and_guard.bat (if present):")
try:
    with open("start_chrome_and_guard.bat", "r", encoding="utf-8") as f:
        print("----- start_chrome_and_guard.bat -----")
        for i, line in enumerate(f):
            if i>199:
                break
            print(line.rstrip())
except Exception as e:
    print(f"Could not open start_chrome_and_guard.bat: {e}")

print("\n=== End Diagnostic ===")
