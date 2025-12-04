#!/usr/bin/env python3
"""
Quick training script to generate XGBoost_RealTime.dat for testing
"""

import os
import pickle
import numpy as np
import xgboost as xgb
from feature_extractor import extract_domain_features_from_url

# Sample datasets
benign_urls = [
    'https://google.com',
    'https://github.com',
    'https://microsoft.com',
    'https://amazon.com',
    'https://facebook.com',
    'https://twitter.com',
    'https://linkedin.com',
    'https://youtube.com',
    'https://openai.com',
    'https://mail.google.com',
]

phishing_urls = [
    'http://paypal-security-alert.com',
    'http://login-verify-appleid.com',
    'http://secure-checking-update.xyz',
    'http://account-service-verification.ru',
    'http://g00gle.com',
    'http://amaz0n-verify.com',
    'http://microsof-security.ga',
    'http://facebok-confirm.tk',
    'http://bit.ly/malicious',
    'http://tinyurl.com/phishing',
]

# Extract features
print("[Training] Extracting features from benign domains...")
X_benign = [extract_domain_features_from_url(url) for url in benign_urls]
y_benign = [0] * len(benign_urls)

print(f"[Training] Extracted {len(X_benign)} benign samples")

print("[Training] Extracting features from phishing domains...")
X_phishing = [extract_domain_features_from_url(url) for url in phishing_urls]
y_phishing = [1] * len(phishing_urls)

print(f"[Training] Extracted {len(X_phishing)} phishing samples")

# Combine
X = np.array(X_benign + X_phishing)
y = np.array(y_benign + y_phishing)

print(f"[Training] Total samples: {len(X)}")
print(f"[Training] Feature matrix shape: {X.shape}")

# Train
print("[Training] Training XGBoost model...")
model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    use_label_encoder=False,
    eval_metric='logloss',
    verbosity=0
)
model.fit(X, y)

print("[Training] Model training complete")

# Test on sample
features = extract_domain_features_from_url('https://google.com')
X_test = np.array(features).reshape(1, -1)
score = model.predict_proba(X_test)[0][1]
print(f"[Training] Test: google.com score = {score:.4f} (expected < 0.4)")

# Save
model_dir = os.path.join(os.path.dirname(__file__), "model")
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, "XGBoost_RealTime.dat")

with open(model_path, 'wb') as f:
    pickle.dump(model, f)

print(f"[Training] Model saved to {model_path}")
print(f"[Training] Done!")
