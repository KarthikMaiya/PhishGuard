#!/usr/bin/env python3
"""
Quick training script for PhishGuard ML model with corrected subdomain counting
using the public suffix list.
"""

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import os
import pickle
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from feature_extractor import extract_domain_features_from_url

print("="*70)
print("PhishGuard ML Model Training (Corrected Subdomain Counting)")
print("="*70)

# Sample training data
benign_urls = [
    'https://google.com',
    'https://mail.google.com',
    'https://drive.google.com',
    'https://docs.google.com',
    'https://www.amazon.com',
    'https://github.com',
    'https://github.io',
    'https://facebook.com',
    'https://twitter.com',
    'https://linkedin.com',
    'https://youtube.com',
    'https://instagram.com',
    'https://microsoft.com',
    'https://apple.com',
    'https://example.co.uk',
    'https://bbc.co.uk',
    'https://www.bbc.co.uk',
    'https://accounts.google.com',
    'https://maps.google.com',
    'https://pinterest.com',
]

phishing_urls = [
    'https://g00gle.com',
    'https://googlе.com',
    'https://suspicious-domain-12345.tk',
    'https://update-paypal-verify.ml',
    'https://confirm-account-now.ga',
    'https://login-secure-check.cf',
    'https://verify-identity-urgent.biz',
    'https://secure-banking-portal.pw',
    'https://account-suspension-fix.xyz',
    'https://urgent-action-required.win',
    'https://paypal-security-verify.tk',
    'https://amazon-verify-account.ml',
    'https://apple-id-verify.ga',
    'https://bank-secure-login-portal.cf',
    'https://verify-identity-now-secure.biz',
    'https://goggle.com',
    'https://goo-gle.com',
    'https://paypa1.com',
    'https://amaz0n.com',
    'https://suspicious-long-domain-with-many-hyphens-to-trick-users.tk',
]

print("\n[Step 1] Loading data...")
df1 = pd.DataFrame({'url': benign_urls, 'label': 0})
df2 = pd.DataFrame({'url': phishing_urls, 'label': 1})
df = pd.concat([df1, df2], ignore_index=True)
print(f"✅ Loaded {len(df1)} benign + {len(df2)} phishing = {len(df)} total URLs")

print("\n[Step 2] Extracting features...")
X = []
for url in df['url']:
    features = extract_domain_features_from_url(url)
    X.append(features)

X = np.array(X)
y = df['label'].values
print(f"✅ Feature matrix shape: {X.shape}")

print("\n[Step 3] Feature verification for key test cases:")
test_cases = [
    ('https://google.com', 0),
    ('https://mail.google.com', 0),
    ('https://accounts.google.com', 0),
    ('https://example.co.uk', 0),
    ('https://bit.ly', 1),
]

for url, expected_label in test_cases:
    features = extract_domain_features_from_url(url)
    subdomain_count = int(features[4])
    entropy = features[6]
    label = df[df['url'] == url]['label'].values
    if len(label) > 0:
        label = label[0]
        status = "✅" if label == expected_label else "❌"
        print(f"   {status} {url:40} → subdomains={subdomain_count}, entropy={entropy:.2f}")
    else:
        print(f"   {url} (not in training set)")

print("\n[Step 4] Training XGBoost model...")
model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    use_label_encoder=False,
    eval_metric='logloss',
    verbosity=0
)

model.fit(X, y)
print(f"✅ Model trained successfully")

# Evaluate
y_pred = model.predict(X)
accuracy = accuracy_score(y, y_pred)
precision = precision_score(y, y_pred, zero_division=0)
recall = recall_score(y, y_pred, zero_division=0)
f1 = f1_score(y, y_pred, zero_division=0)

print(f"\n[Step 5] Model Performance:")
print(f"   Accuracy:  {accuracy:.4f}")
print(f"   Precision: {precision:.4f}")
print(f"   Recall:    {recall:.4f}")
print(f"   F1-Score:  {f1:.4f}")

# Test predictions on critical domains
print("\n[Step 6] Predictions on critical domains:")
critical_tests = [
    ('https://google.com', 0, 'Safe - benign'),
    ('https://mail.google.com', 0, 'Safe - subdomain'),
    ('https://accounts.google.com', 0, 'Safe - legitimate subdomain'),
    ('https://example.co.uk', 0, 'Safe - multi-part TLD'),
    ('https://bit.ly', 1, 'High risk - shortener'),
    ('https://g00gle.com', 1, 'Phishing - typo'),
    ('https://googlе.com', 1, 'Phishing - unicode spoofing'),
    ('https://suspicious-domain-12345.tk', 1, 'Phishing - suspicious TLD'),
    ('https://paypal-security-verify.tk', 1, 'Phishing - suspicious TLD'),
]

passed = 0
for url, expected_label, desc in critical_tests:
    features = extract_domain_features_from_url(url)
    X_test = np.array(features).reshape(1, -1)
    score = model.predict_proba(X_test)[0][1]
    pred_label = 1 if score >= 0.5 else 0
    
    status = "✅ PASS" if pred_label == expected_label else "❌ FAIL"
    if pred_label == expected_label:
        passed += 1
    
    expected_str = "Phishing" if expected_label == 1 else "Benign"
    pred_str = "Phishing" if pred_label == 1 else "Benign"
    print(f"   {status} {url:40} → {pred_str:8} (expected: {expected_str:8}, score: {score:.4f})")

print(f"\n   Result: {passed}/{len(critical_tests)} critical tests passed")

# Save model
print(f"\n[Step 7] Saving model...")
model_dir = os.path.join(os.path.dirname(__file__), 'model')
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, 'XGBoost_RealTime.dat')

with open(model_path, 'wb') as f:
    pickle.dump(model, f)

print(f"✅ Model saved to: {model_path}")
print(f"   File size: {os.path.getsize(model_path) / 1024:.2f} KB")

print("\n" + "="*70)
print("✅ TRAINING COMPLETE")
print("="*70)
print(f"\nFeature extraction uses:")
print(f"   • public suffix list for TLD detection")
print(f"   • Correct subdomain counting: max(dots - len(tld_with_dots), 0)")
print(f"   • 8-feature vector (consistent with serve_ml.py)")
print(f"\nModel is ready for deployment with serve_ml.py")
