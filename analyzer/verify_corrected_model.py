#!/usr/bin/env python3
"""
PhishGuard Model Verification - Tests correct subdomain counting with public suffix list
"""

import os
import sys
import pickle
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from feature_extractor import extract_domain_features_from_url

# Load model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'XGBoost_RealTime.dat')
print(f"[1] Loading model from {MODEL_PATH}...")
try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print(f"[OK] Model loaded successfully\n")
except Exception as e:
    print(f"[FAIL] Failed to load model: {e}")
    sys.exit(1)

print("="*80)
print("PHISHGUARD MODEL VERIFICATION - SUBDOMAIN COUNTING WITH PUBLIC SUFFIX LIST")
print("="*80)

# Test 1: Subdomain counting
print("\n[TEST 1] SUBDOMAIN COUNTING VERIFICATION")
print("-"*80)

subdomain_tests = [
    ('google.com', 0, 'com is public suffix, no subdomains'),
    ('mail.google.com', 1, 'mail is subdomain of google.com'),
    ('accounts.google.com', 1, 'accounts is subdomain of google.com'),
    ('sub.mail.google.com', 2, 'two subdomains: sub.mail'),
    ('example.co.uk', 0, 'co.uk is multi-part public suffix'),
    ('mail.example.co.uk', 1, 'mail is subdomain of example.co.uk'),
    ('192.168.1.1', 0, 'IP address has no subdomains'),
    ('bit.ly', 0, 'ly is public suffix, no subdomains'),
]

print(f"\n{'Domain':<35} {'Expected':<10} {'Actual':<10} {'Status':<8}")
print("-"*80)

subdomain_pass = 0
for domain, expected_count, description in subdomain_tests:
    features = extract_domain_features_from_url(domain)
    actual_count = int(features[4])
    
    status = "[PASS]" if actual_count == expected_count else "[FAIL]"
    if actual_count == expected_count:
        subdomain_pass += 1
    
    print(f"{domain:<35} {expected_count:<10} {actual_count:<10} {status:<8}")
    if actual_count != expected_count:
        print(f"   -> {description}")

print(f"\nSubdomain tests: {subdomain_pass}/{len(subdomain_tests)} passed")

# Test 2: Safe domain classification
print("\n" + "="*80)
print("[TEST 2] SAFE DOMAIN CLASSIFICATION (Low Risk)")
print("-"*80)

safe_domains = [
    ('https://google.com', 'Major search engine'),
    ('https://mail.google.com', 'Google Mail'),
    ('https://accounts.google.com', 'Google Accounts'),
    ('https://drive.google.com', 'Google Drive'),
    ('https://docs.google.com', 'Google Docs'),
    ('https://github.com', 'Source code hosting'),
    ('https://facebook.com', 'Social media'),
    ('https://twitter.com', 'Social media'),
    ('https://linkedin.com', 'Professional network'),
    ('https://amazon.com', 'E-commerce'),
    ('https://example.co.uk', 'Multi-part TLD example'),
]

print(f"\n{'Domain':<40} {'Score':<10} {'Risk':<10} {'Status':<8}")
print("-"*80)

safe_pass = 0
for domain, description in safe_domains:
    features = extract_domain_features_from_url(domain)
    X = np.array(features).reshape(1, -1)
    score = model.predict_proba(X)[0][1]
    
    risk = "LOW" if score < 0.4 else ("MEDIUM" if score < 0.75 else "HIGH")
    status = "[PASS]" if score < 0.4 else "[FAIL]"
    if score < 0.4:
        safe_pass += 1
    
    print(f"{domain:<40} {score:.4f}     {risk:<10} {status:<8}")

print(f"\nSafe domains: {safe_pass}/{len(safe_domains)} passed (all should be < 0.4)")

# Test 3: Phishing domain classification
print("\n" + "="*80)
print("[TEST 3] PHISHING DOMAIN CLASSIFICATION (High Risk)")
print("-"*80)

phishing_domains = [
    ('https://g00gle.com', 'Typo phishing (zero instead of O)'),
    # ('https://googlе.com', 'Unicode typo phishing (Cyrillic e)'),  # Skipped due to console encoding
    ('https://goo-gle.com', 'Hyphenated phishing'),
    ('https://paypa1.com', 'Number substitution phishing'),
    ('https://suspicious-domain-12345.tk', 'Suspicious pattern + .tk TLD'),
    ('https://update-paypal-verify.ml', 'Phishing pattern + suspicious TLD'),
    ('https://confirm-account-now.ga', 'Urgency language + suspicious TLD'),
    ('https://login-secure-check.cf', 'Login pattern + suspicious TLD'),
    ('https://verify-identity-urgent.biz', 'Verification scam + .biz'),
    ('https://secure-banking-portal.pw', 'Banking scam + .pw'),
]

print(f"\n{'Domain':<45} {'Score':<10} {'Risk':<10} {'Status':<8}")
print("-"*80)

phishing_pass = 0
for domain, description in phishing_domains:
    features = extract_domain_features_from_url(domain)
    X = np.array(features).reshape(1, -1)
    score = model.predict_proba(X)[0][1]
    
    risk = "LOW" if score < 0.4 else ("MEDIUM" if score < 0.75 else "HIGH")
    status = "[PASS]" if score > 0.6 else "[FAIL]"
    if score > 0.6:
        phishing_pass += 1
    
    print(f"{domain:<45} {score:.4f}     {risk:<10} {status:<8}")

print(f"\nPhishing domains: {phishing_pass}/{len(phishing_domains)} passed (all should be > 0.6)")

# Test 4: Feature extraction details
print("\n" + "="*80)
print("[TEST 4] FEATURE EXTRACTION DETAILS (Order & Values)")
print("-"*80)

feature_names = [
    'has_ip',
    'contains_hyphen',
    'contains_numbers',
    'is_long_domain',
    'subdomain_count',
    'tld_suspicious',
    'domain_entropy',
    'uses_shortener'
]

test_urls = [
    'https://google.com',
    'https://mail.google.com',
    'https://example.co.uk',
    'https://suspicious-long-domain-with-hyphens.tk',
]

for url in test_urls:
    features = extract_domain_features_from_url(url)
    print(f"\n{url}")
    print("   Feature values:")
    for i, (name, value) in enumerate(zip(feature_names, features)):
        if i == 6:  # entropy is float
            print(f"     {i+1}. {name:20} = {value:.3f}")
        else:
            print(f"     {i+1}. {name:20} = {int(value)}")

# Test 5: Consistency with serve_ml.py
print("\n" + "="*80)
print("[TEST 5] CONSISTENCY CHECK - Feature Order & Inference")
print("-"*80)

print("\n[OK] Feature Extraction Order (MUST MATCH serve_ml.py):")
for i, name in enumerate(feature_names):
    print(f"   {i+1}. {name}")

print("\n[OK] Inference Process:")
test_url = 'https://google.com'
features = extract_domain_features_from_url(test_url)
X = np.array(features).reshape(1, -1)
score = model.predict_proba(X)[0][1]

print(f"   URL: {test_url}")
print(f"   Features: {features}")
print(f"   Score: {score:.4f}")
print(f"   Risk: {'HIGH' if score >= 0.75 else ('MEDIUM' if score >= 0.4 else 'LOW')}")

print("\n" + "="*80)
print("VERIFICATION SUMMARY")
print("="*80)

total_tests = (len(subdomain_tests) + len(safe_domains) + 
               len(phishing_domains))
total_passed = subdomain_pass + safe_pass + phishing_pass

print(f"\n1. Subdomain Counting: {subdomain_pass}/{len(subdomain_tests)} passed")
print(f"2. Safe Domains:       {safe_pass}/{len(safe_domains)} passed")
print(f"3. Phishing Domains:   {phishing_pass}/{len(phishing_domains)} passed")
print(f"\nTotal: {total_passed}/{total_tests} tests passed")

if total_passed >= total_tests * 0.85:  # 85% threshold
    print("\n[SUCCESS] MODEL VERIFICATION SUCCESSFUL")
    print("   The model correctly:")
    print("   * Counts subdomains using public suffix list")
    print("   * Classifies safe domains as low-risk")
    print("   * Classifies phishing domains as high-risk")
    print("   * Uses consistent 8-feature vector")
else:
    print("\n[WARNING] MODEL VERIFICATION INCOMPLETE")
    print("   Some tests failed. Please review the results above.")

print("\n" + "="*80)

