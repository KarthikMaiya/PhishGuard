# PhishGuard ML Analyzer - Quick Start Guide

## What Was Fixed

The critical bug was in `analyzer/feature_extractor.py`:

**The Bug:** `subdomain_count()` was returning raw dot count instead of actual subdomain count
- `google.com` (1 dot) → was returning 1, now returns 0 ✓
- `mail.google.com` (2 dots) → was returning 2, now returns 1 ✓

**The Fix:** Changed formula from `netloc.count('.')` to `max(dot_count - 1, 0)`

This caused `google.com` to be incorrectly classified as high-risk phishing.

---

## Current System State

All files have been created and verified:

### Core Files
- ✓ `analyzer/feature_extractor.py` - FIXED subdomain_count() function
- ✓ `analyzer/serve_ml.py` - API server (verified correct)
- ✓ `analyzer/model/XGBoost_RealTime.dat` - Trained model file exists

### Integration Files
- ✓ `proxy_simple.py` - Calls analyzer API
- ✓ `popup_simple.py` - Shows blocked page UI
- ✓ `launcher.py` - Starts analyzer + proxy

### Verification Files
- ✓ `analyzer/verify_model_simple.py` - Comprehensive test script
- ✓ `analyzer/train_quick.py` - Quick model training
- ✓ `analyzer/test_minimal.py` - Basic diagnostic

### Documentation
- ✓ `VERIFICATION_REPORT.md` - Detailed technical report
- ✓ `VERIFICATION_CHECKLIST.md` - Quick checklist

---

## Testing Instructions

### Test 1: Quick Diagnostic (2 seconds)
```bash
cd analyzer
python test_minimal.py
```
Expected output: `[SUCCESS] All basic tests passed!`

### Test 2: Full Verification (10 seconds)
```bash
cd analyzer
python verify_model_simple.py
```
Expected output: `[✓] ALL TESTS PASSED` with results for:
- 14 URL classifications
- 5 assertion groups

### Test 3: Regenerate Model (optional)
```bash
cd analyzer
python train_quick.py
```
This regenerates the XGBoost model if needed.

---

## Feature Extraction Details

The corrected feature extraction produces 8 features in this exact order:

| Index | Feature | Type | Purpose |
|-------|---------|------|---------|
| 0 | `has_ip` | 0 or 1 | Detects IP addresses in domain |
| 1 | `contains_hyphen` | 0 or 1 | Hyphens often appear in phishing domains |
| 2 | `contains_numbers` | 0 or 1 | Numbers can indicate phishing attempts |
| 3 | `is_long_domain` | 0 or 1 | Long domains (>25 chars) are suspicious |
| 4 | `subdomain_count` | 0+ | **FIXED**: Actual subdomain count |
| 5 | `tld_suspicious` | 0 or 1 | Checks against 13 suspicious TLDs |
| 6 | `domain_entropy` | float | Domain complexity (0-4+) |
| 7 | `uses_shortener` | 0 or 1 | Matches known URL shorteners |

### Subdomain Count Formula (FIXED)
```python
dot_count = domain.count('.')
subdomain_count = max(dot_count - 1, 0)

Examples:
- google.com (1 dot) → 0 subdomains ✓
- mail.google.com (2 dots) → 1 subdomain ✓
- accounts.google.com (2 dots) → 1 subdomain ✓
- a.b.google.com (3 dots) → 2 subdomains ✓
```

---

## Test Coverage

The verification script tests:

### Safe Domains (Expected: low risk)
- google.com
- github.com
- microsoft.com
- openai.com

### Legitimate Subdomains (Expected: low risk)
- mail.google.com
- accounts.google.com

### Phishing Domains (Expected: high risk)
- paypal-security-alert.com
- login-verify-appleid.com
- secure-checking-update.xyz
- account-service-verification.ru

### URL Shorteners (Expected: high risk)
- bit.ly/test
- tinyurl.com/hacked

### IP Addresses (Expected: high risk)
- 192.168.0.1
- 8.8.8.8

---

## Running PhishGuard

Once verified, run:
```bash
python launcher.py
```

This will:
1. Start the ML analyzer on port 8000
2. Start the proxy server on port 8888
3. Launch Chrome with proxy configured
4. PhishGuard will block high-risk domains automatically

---

## How It Works

```
User visits URL
    ↓
Proxy intercepts request
    ↓
Calls analyzer API: POST /score?url=...
    ↓
Feature Extractor extracts 8 features
    ↓
XGBoost model predicts risk score (0-1)
    ↓
If score >= 0.75: BLOCK with blocked_page.html
If score < 0.75: ALLOW request
```

---

## Key Improvements

1. **Fixed Critical Bug** - Subdomain counting now correct
2. **Added Verification** - Automated tests ensure correctness
3. **Clear Documentation** - All features documented and tested
4. **Production Ready** - Model trained with corrected logic

---

## Files Summary

```
analyzer/
  ├── feature_extractor.py ........... FIXED: subdomain_count() formula
  ├── serve_ml.py ................... API server (verified)
  ├── model/
  │   └── XGBoost_RealTime.dat ....... Trained model
  ├── requirements.txt ............... Dependencies
  ├── verify_model_simple.py ......... Verification script (NEW)
  ├── train_quick.py ................ Quick training (NEW)
  └── test_minimal.py ............... Diagnostic script (NEW)

proxy_simple.py ..................... Proxy with ML integration
popup_simple.py ..................... Blocked page popup
launcher.py ......................... Orchestration script

VERIFICATION_REPORT.md .............. Detailed technical report (NEW)
VERIFICATION_CHECKLIST.md ........... Quick checklist
```

---

## Success Criteria

✓ google.com classified as low-risk (score < 0.4)
✓ Phishing domains classified as high-risk (score > 0.7)
✓ Subdomain formula: max(dot_count - 1, 0)
✓ Shortener domains detected and flagged
✓ IP addresses detected correctly
✓ All features in correct order (8 total)
✓ Model predicts with correct probability scores

---

## Support

All changes are backward compatible with existing code. The fix only corrects the subdomain counting logic, which was the root cause of google.com misclassification.
