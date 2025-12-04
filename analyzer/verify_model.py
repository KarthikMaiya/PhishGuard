#!/usr/bin/env python3
"""
PhishGuard Model Verification Script

Verifies that:
1. Feature extraction is correct (especially subdomain_count fix)
2. Model classifies safe domains as low-risk
3. Model classifies phishing domains as high-risk
4. All expected features are computed correctly
"""

import sys
import os
import pickle
import numpy as np
from urllib.parse import urlparse
from feature_extractor import extract_domain_features_from_url

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Load the model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "XGBoost_RealTime.dat")
print(f"{BLUE}[Analyzer]{RESET} Loading model from {MODEL_PATH}...")
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print(f"{GREEN}✓ Model loaded successfully{RESET}\n")
except Exception as e:
    print(f"{RED}✗ Failed to load model: {e}{RESET}")
    sys.exit(1)

# Feature names for readable output
FEATURE_NAMES = [
    "has_ip",
    "contains_hyphen",
    "contains_numbers",
    "is_long_domain",
    "subdomain_count",
    "tld_suspicious",
    "domain_entropy",
    "uses_shortener"
]

def print_test_result(url, features, score, risk, reasons, expected_category):
    """Print a test result in a formatted way."""
    print(f"{BOLD}URL:{RESET} {url}")
    
    # Print features with labels
    print(f"{BOLD}Features:{RESET}")
    for i, (name, value) in enumerate(zip(FEATURE_NAMES, features)):
        if i == 6:  # domain_entropy is float
            print(f"  {i+1}. {name:20} = {value:.3f}")
        else:
            print(f"  {i+1}. {name:20} = {int(value)}")
    
    # Print score and risk
    print(f"{BOLD}Model Output:{RESET}")
    print(f"  Score: {score:.4f}")
    print(f"  Risk:  {risk}")
    if reasons:
        print(f"  Reasons: {', '.join(reasons)}")
    else:
        print(f"  Reasons: (none)")
    
    # Expected vs actual
    print(f"{BOLD}Verification:{RESET}")
    print(f"  Expected category: {expected_category}")
    
    # Color-coded result
    if expected_category == "safe" and score < 0.4:
        print(f"  {GREEN}✓ PASS - Score correctly low{RESET}")
        result = True
    elif expected_category == "legitimate_subdomain" and score < 0.4:
        print(f"  {GREEN}✓ PASS - Subdomain classified as safe{RESET}")
        result = True
    elif expected_category == "phishing" and score > 0.7:
        print(f"  {GREEN}✓ PASS - Score correctly high{RESET}")
        result = True
    elif expected_category == "shortener" and score > 0.6:
        print(f"  {GREEN}✓ PASS - Shortener flagged as risky{RESET}")
        result = True
    elif expected_category == "ip_address" and features[0] == 1:
        print(f"  {GREEN}✓ PASS - IP address detected{RESET}")
        result = True
    else:
        print(f"  {RED}✗ FAIL - Score {score:.4f} outside expected range{RESET}")
        result = False
    
    print()
    return result

def verify_subdomain_logic():
    """Verify the corrected subdomain_count logic."""
    print(f"{BOLD}{BLUE}=== SUBDOMAIN COUNT VERIFICATION ==={RESET}\n")
    
    test_cases = [
        ("google.com", 0),
        ("mail.google.com", 1),
        ("accounts.google.com", 1),
        ("sub.mail.google.com", 2),
        ("192.168.1.1", 0),
        ("example.co.uk", 1),
    ]
    
    all_pass = True
    for domain, expected_count in test_cases:
        features = extract_domain_features_from_url(domain)
        actual_count = features[4]  # subdomain_count is 5th feature (index 4)
        
        if actual_count == expected_count:
            print(f"{GREEN}✓{RESET} {domain:25} → subdomain_count={int(actual_count)} (expected {expected_count})")
        else:
            print(f"{RED}✗{RESET} {domain:25} → subdomain_count={int(actual_count)} (expected {expected_count})")
            all_pass = False
    
    print()
    return all_pass

# Main test execution
print(f"{BOLD}{BLUE}=" * 60)
print("PhishGuard Model Verification")
print("=" * 60 + f"{RESET}\n")

# Step 1: Verify subdomain counting logic
subdomain_pass = verify_subdomain_logic()

# Step 2: Run comprehensive test cases
print(f"{BOLD}{BLUE}=== MODEL CLASSIFICATION TESTS ==={RESET}\n")

test_cases = [
    # Safe domains
    ("https://google.com", "safe"),
    ("https://github.com", "safe"),
    ("https://microsoft.com", "safe"),
    ("https://openai.com", "safe"),
    
    # Legitimate subdomains
    ("https://mail.google.com", "legitimate_subdomain"),
    ("https://accounts.google.com", "legitimate_subdomain"),
    
    # Phishing-like domains
    ("http://paypal-security-alert.com", "phishing"),
    ("http://login-verify-appleid.com", "phishing"),
    ("http://secure-checking-update.xyz", "phishing"),
    ("http://account-service-verification.ru", "phishing"),
    
    # Shortener domains
    ("http://bit.ly/test", "shortener"),
    ("http://tinyurl.com/hacked", "shortener"),
    
    # IP addresses
    ("http://192.168.0.1/login", "ip_address"),
    ("http://8.8.8.8", "ip_address"),
]

results = []
for url, category in test_cases:
    features = extract_domain_features_from_url(url)
    X = np.array(features).reshape(1, -1)
    
    # Get prediction
    try:
        score = float(model.predict_proba(X)[0][1])
    except Exception:
        pred = int(model.predict(X)[0])
        score = 0.99 if pred == 1 else 0.01
    
    # Determine risk level
    if score >= 0.75:
        risk = "high"
    elif score >= 0.4:
        risk = "medium"
    else:
        risk = "low"
    
    # Generate reasons (same logic as serve_ml.py)
    reasons = []
    for i, v in enumerate(features):
        if i == 6:  # domain_entropy
            if float(v) > 3.5:
                reasons.append(FEATURE_NAMES[i])
        else:
            if v and v != 0:
                reasons.append(FEATURE_NAMES[i])
    
    # Print result
    result = print_test_result(url, features, score, risk, reasons, category)
    results.append((url, category, result))

# Step 3: Final assertions
print(f"{BOLD}{BLUE}=== ASSERTIONS ==={RESET}\n")

assertions = []

# Assertion 1: google.com must not be high-risk
features = extract_domain_features_from_url("https://google.com")
X = np.array(features).reshape(1, -1)
score = float(model.predict_proba(X)[0][1])
try:
    assert score < 0.7, f"google.com score {score:.4f} >= 0.7 (HIGH RISK)"
    print(f"{GREEN}✓ PASS{RESET} google.com is not classified as high-risk (score={score:.4f})")
    assertions.append(True)
except AssertionError as e:
    print(f"{RED}✗ FAIL{RESET} {e}")
    assertions.append(False)

# Assertion 2: Suspicious domains must be high-risk
suspicious_urls = [
    "http://secure-checking-update.xyz",
    "http://account-service-verification.ru",
    "http://paypal-security-alert.com"
]
for url in suspicious_urls:
    features = extract_domain_features_from_url(url)
    X = np.array(features).reshape(1, -1)
    score = float(model.predict_proba(X)[0][1])
    try:
        assert score > 0.6, f"{url} score {score:.4f} <= 0.6 (NOT HIGH)"
        print(f"{GREEN}✓ PASS{RESET} {url} is high-risk (score={score:.4f})")
        assertions.append(True)
    except AssertionError as e:
        print(f"{RED}✗ FAIL{RESET} {e}")
        assertions.append(False)

# Assertion 3: Shortener domains must be flagged
shortener_urls = [
    "http://bit.ly/test",
    "http://tinyurl.com/hacked"
]
for url in shortener_urls:
    features = extract_domain_features_from_url(url)
    uses_shortener = features[7]  # 8th feature
    try:
        assert uses_shortener == 1, f"{url} uses_shortener={uses_shortener} (expected 1)"
        print(f"{GREEN}✓ PASS{RESET} {url} correctly flagged as shortener")
        assertions.append(True)
    except AssertionError as e:
        print(f"{RED}✗ FAIL{RESET} {e}")
        assertions.append(False)

# Assertion 4: Subdomain count formula
subdomain_tests = [
    ("google.com", 0),
    ("mail.google.com", 1),
    ("accounts.google.com", 1),
]
for url, expected in subdomain_tests:
    features = extract_domain_features_from_url(url)
    actual = features[4]
    try:
        assert actual == expected, f"{url} subdomain_count={actual} (expected {expected})"
        print(f"{GREEN}✓ PASS{RESET} {url} subdomain_count={int(actual)} (correct)")
        assertions.append(True)
    except AssertionError as e:
        print(f"{RED}✗ FAIL{RESET} {e}")
        assertions.append(False)

# Assertion 5: IP address detection
ip_tests = [
    ("http://192.168.0.1", 1),
    ("http://8.8.8.8", 1),
    ("http://google.com", 0),
]
for url, expected in ip_tests:
    features = extract_domain_features_from_url(url)
    actual = features[0]
    try:
        assert actual == expected, f"{url} has_ip={actual} (expected {expected})"
        print(f"{GREEN}✓ PASS{RESET} {url} has_ip={int(actual)} (correct)")
        assertions.append(True)
    except AssertionError as e:
        print(f"{RED}✗ FAIL{RESET} {e}")
        assertions.append(False)

# Final summary
print(f"\n{BOLD}{BLUE}=== FINAL SUMMARY ==={RESET}\n")
total_tests = len(results) + len(assertions)
passed_tests = sum(results for _, _, results in results) + sum(assertions)

print(f"Test Results: {passed_tests}/{total_tests} passed")
if passed_tests == total_tests:
    print(f"{GREEN}{BOLD}✓ ALL TESTS PASSED{RESET}")
    sys.exit(0)
else:
    print(f"{RED}{BOLD}✗ SOME TESTS FAILED{RESET}")
    sys.exit(1)
