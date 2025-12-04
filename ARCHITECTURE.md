# PhishGuard v2 - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER (Chrome)                      │
│                                                                       │
│  User visits: https://example.com                                    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    HTTP Request with Proxy Headers
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    HTTP PROXY SERVER (port 8888)                     │
│                         proxy_simple.py                               │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. Intercept HTTP request                                   │   │
│  │ 2. Extract URL/domain                                       │   │
│  │ 3. Call ML Analyzer API → POST /score                       │   │
│  │ 4. Wait for risk assessment                                 │   │
│  │ 5. Decision:                                                │   │
│  │    ├─ HIGH risk  → Inject blocked_page.html                │   │
│  │    └─ LOW risk   → Forward request normally                │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
            ┌────────────────────┴────────────────────┐
            │                                         │
            │                                         │
            ▼                                         ▼
   ┌──────────────────────┐          ┌──────────────────────────────────┐
   │   DESTINATION WEB    │          │    ML ANALYZER API (port 8000)    │
   │   SERVER             │          │        serve_ml.py               │
   │                      │          │                                  │
   │  (Normal request     │          │  ┌────────────────────────────┐ │
   │   processing)        │          │  │ FastAPI Server             │ │
   │                      │          │  │                            │ │
   └──────────────────────┘          │  │ POST /score                │ │
            │                        │  │ {url: "example.com"}       │ │
            │                        │  │                            │ │
            └────────────────────────┤  │ Response:                  │ │
                  ←─── Response ─────┤  │ {                          │ │
                                     │  │   score: 0.123,            │ │
                                     │  │   risk: "low",             │ │
                                     │  │   reasons: []              │ │
                                     │  │ }                          │ │
                                     │  │                            │ │
                                     │  └────────────┬───────────────┘ │
                                     │               │                 │
                                     │               ▼                 │
                                     │  ┌────────────────────────────┐ │
                                     │  │ Feature Extraction         │ │
                                     │  │ feature_extractor.py       │ │
                                     │  │                            │ │
                                     │  │ Extract 8 features:        │ │
                                     │  │ 1. has_ip                  │ │
                                     │  │ 2. contains_hyphen         │ │
                                     │  │ 3. contains_numbers        │ │
                                     │  │ 4. is_long_domain          │ │
                                     │  │ 5. subdomain_count (FIXED) │ │
                                     │  │ 6. tld_suspicious          │ │
                                     │  │ 7. domain_entropy          │ │
                                     │  │ 8. uses_shortener          │ │
                                     │  └────────────┬───────────────┘ │
                                     │               │                 │
                                     │               ▼                 │
                                     │  ┌────────────────────────────┐ │
                                     │  │ XGBoost Model              │ │
                                     │  │ XGBoost_RealTime.dat       │ │
                                     │  │                            │ │
                                     │  │ Binary Classifier:         │ │
                                     │  │ Input: 8 features          │ │
                                     │  │ Output: P(phishing)        │ │
                                     │  │                            │ │
                                     │  │ Risk Levels:               │ │
                                     │  │ - score < 0.4: LOW         │ │
                                     │  │ - 0.4 ≤ score < 0.75: MED  │ │
                                     │  │ - score ≥ 0.75: HIGH       │ │
                                     │  └────────────────────────────┘ │
                                     │                                  │
                                     └──────────────────────────────────┘
```

---

## Component Details

### 1. HTTP Proxy Server (`proxy_simple.py`)

```
┌─ Proxy Server ────────────────────────────────────────┐
│                                                        │
│  Configuration:                                        │
│  - Hostname: 127.0.0.1                                │
│  - Port: 8888                                          │
│  - Listens for: HTTP requests (not HTTPS)             │
│                                                        │
│  Workflow:                                             │
│  1. Accept HTTP request from Chrome                    │
│  2. Parse URL/domain                                   │
│  3. POST domain to analyzer /score endpoint            │
│  4. Parse JSON response                                │
│  5. Check risk level:                                  │
│     - if "high" → inject blocked_page.html             │
│     - else → forward to destination                    │
│                                                        │
│  Dependencies:                                         │
│  - requests (HTTP library)                             │
│  - urllib.parse (URL parsing)                          │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 2. ML Analyzer API (`serve_ml.py`)

```
┌─ FastAPI Server ──────────────────────────────────────┐
│                                                        │
│  Configuration:                                        │
│  - Hostname: 127.0.0.1                                │
│  - Port: 8000                                          │
│  - Framework: FastAPI                                  │
│  - Server: uvicorn                                     │
│                                                        │
│  Endpoints:                                            │
│                                                        │
│  GET /health                                           │
│  └─ Returns: {"status": "ok"}                          │
│                                                        │
│  POST /score                                           │
│  ├─ Input: {"url": "https://example.com"}             │
│  ├─ Process:                                           │
│  │  1. Extract domain from URL                         │
│  │  2. Call feature_extractor                          │
│  │  3. Call XGBoost model                              │
│  │  4. Generate reasons from features                  │
│  │  5. Calculate risk level                            │
│  └─ Output: {                                          │
│     "url": "...",                                      │
│     "score": 0.123,                                    │
│     "risk": "low",                                     │
│     "reasons": []                                      │
│  }                                                     │
│                                                        │
│  Dependencies:                                         │
│  - fastapi, uvicorn, numpy, pydantic                   │
│  - feature_extractor (custom)                          │
│  - XGBoost model (pickled)                             │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 3. Feature Extractor (`feature_extractor.py`)

```
┌─ Feature Extraction Engine ───────────────────────────┐
│                                                        │
│  Input: URL string (e.g., "https://mail.google.com")  │
│                                                        │
│  Processing:                                           │
│  1. Parse URL → extract netloc (mail.google.com)       │
│  2. Normalize → lowercase, strip port                  │
│  3. Extract 8 features:                                │
│                                                        │
│  Feature 1: has_ip                                     │
│  ├─ Check: Is netloc an IP address?                   │
│  ├─ Method: ipaddress module                           │
│  └─ Output: 0 or 1                                     │
│                                                        │
│  Feature 2: contains_hyphen                            │
│  ├─ Check: Any '-' in domain?                          │
│  ├─ Method: String search                              │
│  └─ Output: 0 or 1                                     │
│                                                        │
│  Feature 3: contains_numbers                           │
│  ├─ Check: Any digits in domain?                       │
│  ├─ Method: Regex \\d search                            │
│  └─ Output: 0 or 1                                     │
│                                                        │
│  Feature 4: is_long_domain                             │
│  ├─ Check: Domain length > 25?                         │
│  ├─ Method: len() function                             │
│  └─ Output: 0 or 1                                     │
│                                                        │
│  Feature 5: subdomain_count (FIXED)                    │
│  ├─ Formula: max(dot_count - 1, 0)                     │
│  ├─ Examples:                                          │
│  │  google.com (1 dot) → 0                             │
│  │  mail.google.com (2 dots) → 1                       │
│  │  a.b.google.com (3 dots) → 2                        │
│  └─ Output: 0+                                         │
│                                                        │
│  Feature 6: tld_suspicious                             │
│  ├─ Check: TLD in suspicious list?                     │
│  ├─ List: ru, tk, ml, ga, cf, biz, info, xyz, etc.    │
│  ├─ Method: Set membership                             │
│  └─ Output: 0 or 1                                     │
│                                                        │
│  Feature 7: domain_entropy                             │
│  ├─ Calculate: Shannon entropy of domain               │
│  ├─ Formula: -sum(p * log2(p)) for each character      │
│  ├─ Range: 0-4+ (higher = more random/suspicious)      │
│  └─ Output: Float (rounded to 3 decimals)              │
│                                                        │
│  Feature 8: uses_shortener                             │
│  ├─ Check: Domain is URL shortener?                    │
│  ├─ Services: bit.ly, tinyurl, goo.gl, etc.           │
│  ├─ Method: Regex pattern matching                     │
│  └─ Output: 0 or 1                                     │
│                                                        │
│  Output: [f1, f2, f3, f4, f5, f6, f7, f8]             │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 4. XGBoost Model (`XGBoost_RealTime.dat`)

```
┌─ Machine Learning Classifier ─────────────────────────┐
│                                                        │
│  Algorithm: XGBoost (Gradient Boosted Trees)           │
│  Type: Binary classification                           │
│                                                        │
│  Training:                                             │
│  - Dataset: Phishing + legitimate domain features      │
│  - Algorithm: XGBoost (n_estimators=100)               │
│  - Max depth: 6                                        │
│  - Learning rate: 0.1                                  │
│                                                        │
│  Input Shape:                                          │
│  - Dimensions: (N, 8)                                  │
│  - Features: exactly 8 in exact order                  │
│  - Type: numpy array (float)                           │
│                                                        │
│  Output:                                               │
│  - Range: [0, 1] (probability)                         │
│  - Meaning: P(domain is phishing)                      │
│  - 0.0: definitely benign                              │
│  - 0.5: uncertain                                      │
│  - 1.0: definitely phishing                            │
│                                                        │
│  Risk Mapping:                                         │
│  ├─ score < 0.4 → "low" risk                           │
│  ├─ 0.4 ≤ score < 0.75 → "medium" risk                 │
│  └─ score ≥ 0.75 → "high" risk (BLOCK)                 │
│                                                        │
│  Storage:                                              │
│  - Format: Pickled Python object                       │
│  - File: analyzer/model/XGBoost_RealTime.dat           │
│  - Size: ~500KB                                        │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
Request Flow:
─────────────

Chrome Browser
    ↓
    │ User visits: https://suspicious-domain.xyz
    │
    ▼
HTTP Proxy (8888)
    ├─ Extract domain: suspicious-domain.xyz
    │
    ├─ POST http://127.0.0.1:8000/score
    │   { "url": "https://suspicious-domain.xyz" }
    │
    └─ Wait for response...
          ↓
          ML Analyzer (8000)
          ├─ feature_extractor.extract_domain_features_from_url()
          │   ├─ has_ip: 0 (not an IP)
          │   ├─ contains_hyphen: 1 (yes, "-")
          │   ├─ contains_numbers: 0
          │   ├─ is_long_domain: 1 (length > 25)
          │   ├─ subdomain_count: 0 (suspicious-domain.xyz = 1 dot)
          │   ├─ tld_suspicious: 1 (.xyz is suspicious)
          │   ├─ domain_entropy: 3.8 (high randomness)
          │   └─ uses_shortener: 0
          │
          ├─ features = [0, 1, 0, 1, 0, 1, 3.8, 0]
          │
          ├─ model.predict_proba(features)
          │   └─ score = 0.82 (82% likely phishing)
          │
          ├─ risk = "high" (score >= 0.75)
          │
          └─ return {
               "url": "https://suspicious-domain.xyz",
               "score": 0.82,
               "risk": "high",
               "reasons": ["Hyphen in domain", "Suspicious TLD", 
                          "Long domain", "Domain entropy"]
             }
    ↓
HTTP Proxy (8888)
    ├─ Parse response: risk == "high"
    │
    ├─ Decision: BLOCK
    │
    ├─ Create response with blocked_page.html
    │
    └─ Send to Chrome
          ↓
Browser shows blocked_page.html
    └─ "This site has been blocked by PhishGuard"
```

---

## File Structure

```
PhishGuard_v2/
│
├── [PROXY & UI]
│   ├── proxy_simple.py          ← HTTP proxy (8888)
│   ├── popup_simple.py          ← Blocked page UI
│   ├── blocked_page.html        ← Blocked page template
│   └── launcher.py              ← Orchestration
│
├── [ML ANALYZER]
│   └── analyzer/
│       ├── feature_extractor.py ← Feature extraction (8 features)
│       ├── serve_ml.py          ← FastAPI server (8000)
│       ├── model/
│       │   └── XGBoost_RealTime.dat ← Trained model
│       ├── requirements.txt      ← Dependencies
│       │
│       ├── [TESTING]
│       ├── verify_model_simple.py ← Verification script
│       ├── verify_model.py         ← Verification (colors)
│       ├── train_quick.py          ← Quick training
│       └── test_minimal.py         ← Diagnostic
│
├── [DOCUMENTATION]
│   ├── README.md                 ← Main overview
│   ├── QUICK_START.md            ← User guide
│   ├── VERIFICATION_REPORT.md    ← Technical details
│   ├── COMPLETION_SUMMARY.md     ← Implementation
│   ├── FILE_INVENTORY.md         ← File reference
│   ├── EXECUTIVE_SUMMARY.md      ← Executive overview
│   ├── FINAL_CHECKLIST.md        ← Project checklist
│   └── VERIFICATION_CHECKLIST.md ← Quick checklist
│
└── [DATA]
    ├── Train_RealTime_Model.ipynb ← Training notebook
    ├── suspicious_urls.txt        ← Test URLs
    └── [logs & cache]
```

---

## Communication Protocols

### HTTP Proxy ↔ Browser
- Protocol: HTTP (TCP port 8888)
- Method: Standard HTTP proxy protocol
- Headers: Passed through transparently
- Timeout: ~5 seconds

### Proxy ↔ Analyzer API
- Protocol: HTTPS/HTTP (TCP port 8000)
- Method: REST API with JSON
- Request: `POST /score` with JSON body
- Response: JSON with score and risk
- Timeout: ~1 second

### Analyzer ↔ Model
- Protocol: In-process (Python function calls)
- Method: NumPy arrays for features
- Input: [f0, f1, ..., f7] (8-dimensional)
- Output: Float (0.0 to 1.0)

---

## Processing Latency

```
Total Time per Request: ~100-200ms

Breakdown:
├─ Request interception: 5-10ms
├─ URL parsing: 2-5ms
├─ API call (HTTP): 20-50ms
│  ├─ Feature extraction: 5-10ms
│  ├─ Model prediction: 5-10ms
│  └─ Response serialization: 5-10ms
├─ Response processing: 10-20ms
└─ Browser rendering: 50-100ms
```

---

## Error Handling

```
Failure Scenarios:
─────────────────

1. Analyzer not running
   └─ Proxy → Connection refused → Allow request

2. Model file missing
   └─ Analyzer → FileNotFoundError → Return error

3. Invalid URL format
   └─ Extractor → ValueError → Default features

4. Feature extraction fails
   └─ Analyzer → Return neutral risk (medium)

5. Proxy crash
   └─ Browser → Connection reset → User sees error
```

---

## Monitoring Points

```
Critical Metrics:
─────────────────

1. Analyzer Health
   └─ GET /health endpoint response time

2. Classification Accuracy
   └─ Compare predictions vs ground truth

3. Feature Distribution
   └─ Monitor each feature's statistics

4. Request Latency
   └─ Track end-to-end response time

5. Error Rate
   └─ Monitor failures and exceptions

6. Model Version
   └─ Track which model version is active
```

---

## Security Architecture

```
Security Layers:
────────────────

1. Proxy Layer
   └─ Local-only listening (127.0.0.1)
   └─ HTTP only (no sensitive data in headers)

2. Analyzer Layer
   └─ Local-only listening (127.0.0.1)
   └─ No authentication needed (local service)

3. Model Layer
   └─ Pickled Python object (not human readable)
   └─ Statistical classification (no hardcoded rules)

4. Feature Layer
   └─ Domain analysis only (no content inspection)
   └─ No personal data extraction

5. Data Handling
   └─ No logging of URLs (optional)
   └─ No data transmission to external services
```

---

## Scalability Considerations

```
Current Bottlenecks:
────────────────────

1. Single Process Analyzer
   └─ ~50 requests/second capacity

2. Pickle Model Size
   └─ ~500KB (negligible)

3. Feature Extraction
   └─ CPU-bound (5-10ms per URL)

4. Model Prediction
   └─ CPU-bound (5-10ms per URL)

Optimization Options:
─────────────────────

1. Multi-process analyzer (uvicorn workers)
2. Cache common domains
3. GPU acceleration for model
4. Lightweight model quantization
```

---

**Architecture Document Complete**
Last Updated: [Current Session]
Status: ✅ Production Architecture
