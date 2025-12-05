#!/usr/bin/env python
"""Test different Popen variants to find which one works"""
import subprocess
import sys
import time
import os

CONDA_PYTHON = r"C:\Users\Karthik Maiya\anaconda3\envs\phishguard_env\python.exe"
script_dir = r"C:\Users\Karthik Maiya\Desktop\PhishGuard_v2"

configs = [
    {"name": "with -u", "args": [CONDA_PYTHON, "-u", "analyzer/serve_ml.py"]},
    {"name": "without -u", "args": [CONDA_PYTHON, "analyzer/serve_ml.py"]},
    {"name": "full path with -u", "args": [CONDA_PYTHON, "-u", f"{script_dir}\\analyzer\\serve_ml.py"]},
]

for config in configs:
    print(f"\n[TEST] Config: {config['name']}")
    print(f"[TEST] Command: {config['args']}")
    
    try:
        proc = subprocess.Popen(
            config["args"],
            cwd=script_dir,
            env=os.environ.copy()
        )
        print(f"[TEST] PID: {proc.pid}")
        time.sleep(1)
        ret = proc.poll()
        print(f"[TEST] After 1s: proc.poll() = {ret}")
        if ret is None:
            proc.terminate()
            print(f"[TEST] Still running - terminating")
    except Exception as e:
        print(f"[TEST] Exception: {e}")
