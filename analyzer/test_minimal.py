#!/usr/bin/env python3
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(__file__))

print("Testing feature extraction...")
try:
    from feature_extractor import extract_domain_features_from_url
    print("[OK] feature_extractor imported")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Test feature extraction
try:
    features = extract_domain_features_from_url("https://google.com")
    print(f"[OK] Features extracted: {features}")
    print(f"     subdomain_count={int(features[4])}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test model loading
try:
    import pickle
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "XGBoost_RealTime.dat")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print("[OK] Model loaded")
except Exception as e:
    print(f"[ERROR] Loading model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test prediction
try:
    import numpy as np
    X = np.array(features).reshape(1, -1)
    score = model.predict_proba(X)[0][1]
    print(f"[OK] Prediction: score={score:.4f}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[SUCCESS] All basic tests passed!")
