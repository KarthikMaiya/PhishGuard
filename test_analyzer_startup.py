#!/usr/bin/env python
"""Quick test: start analyzer and check if port 8000 is listening"""
import subprocess
import sys
import time
import urllib.request
import urllib.error
import os

CONDA_PYTHON = r"C:\Users\Karthik Maiya\anaconda3\envs\phishguard_env\python.exe"
script_dir = r"C:\Users\Karthik Maiya\Desktop\PhishGuard_v2"

print(f"[TEST] Starting analyzer via {CONDA_PYTHON}")
proc = subprocess.Popen(
    [CONDA_PYTHON, "-u", "analyzer/serve_ml.py"],
    cwd=script_dir,
    env=os.environ.copy()
)
print(f"[TEST] Process PID: {proc.pid}")

# Give it 5 seconds to start
for i in range(10):
    time.sleep(0.5)
    ret = proc.poll()
    print(f"[TEST] Checking after {(i+1)*0.5:.1f}s - proc.poll() = {ret}")
    
    if ret is not None:
        print(f"[TEST] ERROR: Process exited with code {ret}")
        break
    
    # Try to contact port 8000
    try:
        req = urllib.request.Request('http://127.0.0.1:8000/health')
        r = urllib.request.urlopen(req, timeout=1)
        print(f"[TEST] SUCCESS! Got HTTP {r.status}")
        break
    except urllib.error.URLError as e:
        print(f"[TEST] Not ready yet: {e.reason}")
    except Exception as e:
        print(f"[TEST] Error: {e}")

if proc.poll() is None:
    print(f"[TEST] Process still running, terminating")
    proc.terminate()
