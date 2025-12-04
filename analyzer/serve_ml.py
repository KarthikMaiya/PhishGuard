# serve_ml.py
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import pickle
import numpy as np
from feature_extractor import extract_domain_features_from_url

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
    features = extract_domain_features_from_url(url)
    X = np.array(features).reshape(1, -1)

    # Use predict_proba if available
    try:
        score = float(model.predict_proba(X)[0][1])
    except Exception:
        # fallback to predict (0 or 1)
        pred = int(model.predict(X)[0])
        score = 0.99 if pred == 1 else 0.01

    # Risk levels (tunable)
    if score >= 0.75:
        risk = "high"
    elif score >= 0.4:
        risk = "medium"
    else:
        risk = "low"

    # Explainability: map features to names
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
    reasons = []
    for i, v in enumerate(features):
        # entropy is float; give reason if entropy > 3.5 (tunable)
        if i == 6:
            if float(v) > 3.5:
                reasons.append(names[i])
        else:
            if v and v != 0:
                reasons.append(names[i])

    return {
        "url": url,
        "score": round(score, 6),
        "risk": risk,
        "reasons": reasons
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
