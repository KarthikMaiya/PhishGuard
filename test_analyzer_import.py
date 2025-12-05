#!/usr/bin/env python
"""Test if analyzer can even be imported"""
import subprocess
import os

CONDA_PYTHON = r"C:\Users\Karthik Maiya\anaconda3\envs\phishguard_env\python.exe"
script_dir = r"C:\Users\Karthik Maiya\Desktop\PhishGuard_v2"

# Test 1: Just import the module
print("[TEST] Test 1: Import analyzer.serve_ml")
proc = subprocess.Popen(
    [CONDA_PYTHON, "-c", "from analyzer.serve_ml import app; print('OK')"],
    cwd=script_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
out, err = proc.communicate()
print(f"  Return code: {proc.returncode}")
print(f"  stdout: {out}")
print(f"  stderr: {err}")

# Test 2: Run the script's main block
print("\n[TEST] Test 2: Run __name__=='__main__' logic")
proc = subprocess.Popen(
    [CONDA_PYTHON, "-c", "if __name__=='__main__': print('Script would run here')"],
    cwd=script_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
out, err = proc.communicate()
print(f"  Return code: {proc.returncode}")
print(f"  stdout: {out}")
print(f"  stderr: {err}")

# Test 3: Check if uvicorn can be imported
print("\n[TEST] Test 3: Import uvicorn")
proc = subprocess.Popen(
    [CONDA_PYTHON, "-c", "import uvicorn; print(uvicorn.__version__)"],
    cwd=script_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
out, err = proc.communicate()
print(f"  Return code: {proc.returncode}")
print(f"  stdout: {out}")
print(f"  stderr: {err}")
