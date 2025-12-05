#!/usr/bin/env python
"""Test importing analyzer via conda python with detailed error reporting"""
import subprocess
import os
import sys

CONDA_PYTHON = r"C:\Users\Karthik Maiya\anaconda3\envs\phishguard_env\python.exe"
script_dir = r"C:\Users\Karthik Maiya\Desktop\PhishGuard_v2"

test_code = """
import sys
import traceback
try:
    print('[Import] Step 1: Import FastAPI', flush=True)
    from fastapi import FastAPI
    print('[Import] Step 2: Import pickle', flush=True)
    import pickle
    print('[Import] Step 3: Import numpy', flush=True)
    import numpy as np
    print('[Import] Step 4: Import os/sys', flush=True)
    import os
    import sys
    print('[Import] Step 5: Import urlparse', flush=True)
    from urllib.parse import urlparse
    
    print('[Import] Step 6: Import feature_extractor', flush=True)
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from analyzer.feature_extractor import extract_domain_features_from_url, brand_impersonation_score
    
    print('[Import] Step 7: Create FastAPI app', flush=True)
    app = FastAPI(title="PhishGuard ML Analyzer")
    
    print('[Import] Step 8: Get model path', flush=True)
    MODEL_DIR = os.path.dirname(__file__)
    MODEL_PATH = os.path.join(MODEL_DIR, 'model', 'XGBoost_RealTime.dat')
    print(f'[Import] Loading {MODEL_PATH}', flush=True)
    
    print('[Import] Step 9: Load model', flush=True)
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print('[Import] SUCCESS!', flush=True)
    
except Exception as e:
    print(f'[Import] FAILED: {e}', flush=True)
    traceback.print_exc()
    sys.exit(1)
"""

print(f"[TEST] Running conda Python: {CONDA_PYTHON}")
proc = subprocess.Popen(
    [CONDA_PYTHON, "analyzer/serve_ml.py"],
    cwd=script_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=os.environ.copy()
)
print(f"[TEST] PID: {proc.pid}")

out, _ = proc.communicate(timeout=10)
print(f"[TEST] Return code: {proc.returncode}")
print("[TEST] Output:")
print(out)
