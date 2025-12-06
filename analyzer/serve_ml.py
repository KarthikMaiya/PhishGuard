# serve_ml.py
import sys
import os

# Handle imports for both subprocess and direct execution
try:
    from .feature_extractor import extract_domain_features_from_url, brand_impersonation_score
except ImportError:
    # When run directly as a script, use absolute imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from analyzer.feature_extractor import extract_domain_features_from_url, brand_impersonation_score

print(f"[Analyzer] Starting imports...", flush=True)
sys.stdout.flush()

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import pickle
import numpy as np
from urllib.parse import urlparse

print(f"[Analyzer] FastAPI, uvicorn, pickle imported successfully", flush=True)
sys.stdout.flush()


app = FastAPI(title="PhishGuard ML Analyzer")

# Use absolute path for model to work from any working directory
MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, "model", "XGBoost_RealTime.dat")

print(f"[Analyzer] Model directory: {MODEL_DIR}", flush=True)
print(f"[Analyzer] Model path: {MODEL_PATH}", flush=True)
print(f"[Analyzer] Model file exists: {os.path.exists(MODEL_PATH)}", flush=True)

# Load model - critical for functionality
model = None
try:
    print(f"[Analyzer] Loading model from {MODEL_PATH}...", flush=True)
    sys.stdout.flush()
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print(f"[Analyzer] Model loaded successfully.", flush=True)
    sys.stdout.flush()
except FileNotFoundError as e:
    print(f"[Analyzer] CRITICAL: Model file not found: {MODEL_PATH}", flush=True)
    print(f"[Analyzer] Error: {e}", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    # Continue - will handle in /score endpoint
except Exception as e:
    print(f"[Analyzer] CRITICAL: Could not load model: {type(e).__name__}: {e}", flush=True)
    import traceback
    print(f"[Analyzer] Traceback: {traceback.format_exc()}", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    # Continue - will handle in /score endpoint

class URLRequest(BaseModel):
    url: str

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score")
def score_url(data: URLRequest):
    url = data.url
    
    # CRITICAL: Check if model loaded successfully
    if model is None:
        print(f"[Analyzer] WARNING: Model not loaded, returning safe default (low risk) for {url}", flush=True)
        sys.stdout.flush()
        return {
            "url": url,
            "score": 0.0,
            "risk": "low",
            "reasons": ["analyzer_model_unavailable"]
        }

    # 1. Extract ML features (8 features only)
    features = extract_domain_features_from_url(url)
    X = np.array(features).reshape(1, -1)
    reasons = []

    # 2. ML prediction
    try:
        score = float(model.predict_proba(X)[0][1])
    except Exception:
        pred = int(model.predict(X)[0])
        score = 0.99 if pred == 1 else 0.01

    # 3. Base ML risk
    if score >= 0.75:
        risk = "high"
    elif score >= 0.4:
        risk = "medium"
    else:
        risk = "low"

    # 4. Explainability from ML features
    names = [
        "IP in domain",
        "Hyphen in domain",
        "Numbers in domain",
        "Long domain",
        "Multiple subdomains",
        "Suspicious TLD",
        "Domain entropy",
        "Known shortener domain"
    ]

    for i, v in enumerate(features):
        if i == 6:  # entropy
            if float(v) > 3.5:
                reasons.append(names[i])
        else:
            if v and v != 0:
                reasons.append(names[i])

    # 5. BRAND IMPERSONATION OVERRIDE (FINAL AUTHORITY)
    parsed = urlparse(url)
    domain = parsed.netloc.lower().split(":")[0]

    similarity, brand = brand_impersonation_score(domain)

    OFFICIAL_BRANDS = {
        "google": ["google.com"],
        "microsoft": ["microsoft.com"],
        "paypal": ["paypal.com"],
        "apple": ["apple.com"],
        "amazon": ["amazon.com"],
        "facebook":["facebook.com"]
    }

    legit_domains = OFFICIAL_BRANDS.get(brand, [])

    is_legit = domain in legit_domains or any(domain.endswith("." + d) for d in legit_domains)

    if similarity >= 0.75 and not is_legit:
        score = max(score, 0.95)
        risk = "high"

        tag = f"brand_impersonation:{brand}"
        if tag not in reasons:
            reasons.append(tag)


    # 6. Final response
    return {
        "url": url,
        "score": round(score, 6),
        "risk": risk,
        "reasons": reasons
    }


if __name__ == "__main__":
    import sys
    print(f"[Analyzer] Python executable: {sys.executable}", flush=True)
    print(f"[Analyzer] Current working directory: {os.getcwd()}", flush=True)
    print(f"[Analyzer] Starting uvicorn on 127.0.0.1:8000...", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True
    )


