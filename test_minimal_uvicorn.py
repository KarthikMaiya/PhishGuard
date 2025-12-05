#!/usr/bin/env python
"""Minimal test: create FastAPI app and start uvicorn"""
import sys
sys.path.insert(0, '.')

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test")

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print("[uvicorn] Starting...")
    sys.stdout.flush()
    sys.stderr.flush()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )
