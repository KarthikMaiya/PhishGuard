# serve_ml.py
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import pickle
import numpy as np
from feature_extractor import extract_domain_features_from_url
from urllib.parse import urlparse
from feature_extractor import brand_impersonation_score


app = FastAPI(title="PhishGuard ML Analyzer")

MODEL_PATH = "model/XGBoost_RealTime.dat"

print(f"[Analyzer] Loading model from {MODEL_PATH}...")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
print("[Analyzer] Model loaded successfully.")

class URLRequest(BaseModel):
    url: str

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score")
def score_url(data: URLRequest):
    url = data.url

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

    if similarity >= 0.75:
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
    uvicorn.run(app, host="127.0.0.1", port=8000)
