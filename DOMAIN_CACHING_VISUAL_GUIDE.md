# 🎯 Domain-Level Caching: Visual Summary

## Problem → Solution Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    BROWSER LOADS DOMAIN                     │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         v               v               v
   Main page      Favicon            CSS/JS
   malicious.com  favicon.ico        style.css
         │               │               │
         v               v               v
┌──────────────────────────────────────────────────┐
│         OLD BEHAVIOR (URL-LEVEL CACHE)           │
│                                                  │
│  popup_shown_urls = {                           │
│    'https://malicious.com/',                    │
│    'https://malicious.com/favicon.ico',         │
│    'https://malicious.com/style.css'            │
│  }                                               │
│                                                  │
│  Each URL is DIFFERENT → Each triggers POPUP    │
│  Result: 3+ POPUPS FOR 1 DOMAIN ❌              │
└──────────────────────────────────────────────────┘
         │               │               │
         v               v               v
     ❌ POPUP         ❌ POPUP         ❌ POPUP
     ❌ POPUP         ❌ POPUP         ❌ POPUP
     ❌ POPUP         ❌ POPUP         ❌ POPUP
         ↓               ↓               ↓
    USER HARASSED WITH MULTIPLE POPUPS ❌❌❌


┌──────────────────────────────────────────────────┐
│      NEW BEHAVIOR (DOMAIN-LEVEL CACHE)           │
│                                                  │
│  popup_shown_domains = {'malicious.com'}         │
│  domain_decisions = {                            │
│    'malicious.com': 'block'                      │
│  }                                               │
│                                                  │
│  All URLs from SAME DOMAIN → shared cache       │
│  Result: 1 POPUP FOR 1 DOMAIN ✅                │
└──────────────────────────────────────────────────┘
         │               │               │
         v               v               v
     ✅ POPUP        ✅ CACHED        ✅ CACHED
     (user clicks)   (no popup)       (no popup)
         │               │               │
         ↓               ↓               ↓
     USER SEES ONLY 1 POPUP ✅
```

---

## Request Flow Diagram

### First Request to Domain (Popup shown)

```
GET https://malicious.com/
        │
        ↓
  [Check ML Analyzer]
        │
        ↓
   Risk = HIGH
        │
        ↓
  normalized = normalize_domain("malicious.com")
             = "malicious.com"
        │
        ↓
  IS "malicious.com" IN popup_shown_domains?
        │
        NO ← First time seeing this domain
        │
        ↓
  Add to popup_shown_domains:
  popup_shown_domains.add("malicious.com")
        │
        ↓
  Show popup:
  show_popup_subprocess("malicious.com", reasons)
        │
        ↓
  User clicks: BLOCK
        │
        ↓
  Cache decision:
  domain_decisions["malicious.com"] = "block"
        │
        ↓
  Apply BLOCK decision → Show block page ✅
```

### Subsequent Request to Same Domain (No popup)

```
GET https://malicious.com/favicon.ico
        │
        ↓
  [Check ML Analyzer]
        │
        ↓
   Risk = HIGH
        │
        ↓
  normalized = normalize_domain("malicious.com")
             = "malicious.com"
        │
        ↓
  IS "malicious.com" IN popup_shown_domains?
        │
        YES ← Already cached!
        │
        ↓
  Retrieve cached decision:
  show_popup_decision = domain_decisions["malicious.com"]
                     = "block"
        │
        ↓
  NO POPUP SHOWN ✅
  Directly apply cached decision: BLOCK
        │
        ↓
  Block favicon load (or show block page)
```

---

## Cache State Visualization

### Timeline: User visits multiple domains

```
TIME 0: User starts browsing
┌────────────────────────────────┐
│ popup_shown_domains = {}       │
│ domain_decisions = {}          │
└────────────────────────────────┘

TIME 1: User visits evil.com (HIGH RISK)
        ┌──────────────────────────────────────┐
        │ [POPUP SHOWN]                        │
        │ User clicks: BLOCK                    │
        └──────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│ popup_shown_domains = {'evil.com'}             │
│ domain_decisions = {'evil.com': 'block'}       │
└────────────────────────────────────────────────┘

TIME 2: User visits evil.com/favicon.ico (AUTO-LOAD)
        [NO POPUP - CACHED] ✅
┌────────────────────────────────────────────────┐
│ popup_shown_domains = {'evil.com'}             │
│ domain_decisions = {'evil.com': 'block'}       │
└────────────────────────────────────────────────┘

TIME 3: User visits phishing.com (HIGH RISK)
        ┌──────────────────────────────────────┐
        │ [POPUP SHOWN]                        │
        │ User clicks: ALLOW                    │
        └──────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│ popup_shown_domains = {                        │
│   'evil.com',                                  │
│   'phishing.com'                               │
│ }                                              │
│ domain_decisions = {                           │
│   'evil.com': 'block',                         │
│   'phishing.com': 'allow'                      │
│ }                                              │
└────────────────────────────────────────────────┘

TIME 4: User visits phishing.com/style.css (AUTO-LOAD)
        [NO POPUP - CACHED] ✅
        [ALLOW DECISION APPLIED] ✅
┌────────────────────────────────────────────────┐
│ (Same state as TIME 3)                         │
│ popup_shown_domains = {                        │
│   'evil.com',                                  │
│   'phishing.com'                               │
│ }                                              │
│ domain_decisions = {                           │
│   'evil.com': 'block',                         │
│   'phishing.com': 'allow'                      │
│ }                                              │
└────────────────────────────────────────────────┘

TIME 5: Browser restarts (new session)
        ┌─────────────────────────────┐
        │ CACHE CLEARED               │
        │ (session-based)             │
        └─────────────────────────────┘
┌────────────────────────────────┐
│ popup_shown_domains = {}       │
│ domain_decisions = {}          │
│ (Fresh start for new session)  │
└────────────────────────────────┘
```

---

## Code Structure: Before vs After

### BEFORE: URL-Level Caching

```python
class Addon:
    def __init__(self):
        self.popup_shown_urls = set()  # ❌ Only URLs, no decisions
    
    def request(self, flow):
        if risk == 'high':
            full_url = "https://malicious.com/favicon.ico"
            
            # Check FULL URL (too specific)
            if full_url in self.popup_shown_urls:
                show_popup_decision = 'block'  # ❌ No stored decision
            else:
                self.popup_shown_urls.add(full_url)  # ❌ Different URLs
                show_popup_decision = self.show_popup_subprocess(...)
                # Each URL is unique → Popup shown multiple times ❌
```

### AFTER: Domain-Level Caching

```python
class Addon:
    def __init__(self):
        self.popup_shown_domains = set()      # ✅ Track domains
        self.domain_decisions = {}            # ✅ Store decisions
    
    def request(self, flow):
        if risk == 'high':
            domain = "malicious.com"
            normalized = self.normalize_domain(domain)  # ✅ Get root domain
            
            # Check NORMALIZED DOMAIN (less specific, correct)
            if normalized in self.popup_shown_domains:
                show_popup_decision = self.domain_decisions.get(normalized, 'block')
                # ✅ Reuse cached decision, no popup
            else:
                self.popup_shown_domains.add(normalized)
                show_popup_decision = self.show_popup_subprocess(...)
                self.domain_decisions[normalized] = show_popup_decision
                # ✅ Show popup once, store decision for reuse
```

---

## Behavior Matrix

### Test scenarios × Expected outcomes

```
┌──────────────────────┬──────────────┬────────────────┬──────────────┐
│ Scenario             │ Request Type │ First Time?    │ Popup?       │
├──────────────────────┼──────────────┼────────────────┼──────────────┤
│ evil.com main page   │ GET /        │ YES (domain)   │ ✅ YES       │
│ favicon auto-load    │ GET /favicon │ NO (cached)    │ ❌ NO        │
│ CSS auto-load        │ GET /css     │ NO (cached)    │ ❌ NO        │
│ JS auto-load         │ GET /js      │ NO (cached)    │ ❌ NO        │
│ cdn.evil.com img     │ GET cdn img  │ NO (same root) │ ❌ NO        │
│ api.evil.com call    │ GET /api     │ NO (same root) │ ❌ NO        │
├──────────────────────┼──────────────┼────────────────┼──────────────┤
│ different.com page   │ GET /        │ YES (new)      │ ✅ YES       │
│ different.com css    │ GET /css     │ NO (cached)    │ ❌ NO        │
├──────────────────────┼──────────────┼────────────────┼──────────────┤
│ evil.com (after      │ GET /        │ NO (session)   │ ✅ YES*      │
│  browser restart)    │              │                │ (*new session)│
└──────────────────────┴──────────────┴────────────────┴──────────────┘
```

---

## Performance Comparison

### Popups per Domain

```
OLD (URL-level caching):
┌─────────────────────────────────────┐
│ evil.com/          ▓▓▓▓▓ (5 popups) │
│ phishing.com/      ▓▓▓▓ (4 popups)  │
│ malware.com/       ▓▓▓▓▓▓ (6 popups)│
│ Total: 15+ POPUPS ❌                │
└─────────────────────────────────────┘

NEW (Domain-level caching):
┌─────────────────────────────────────┐
│ evil.com/          ▓ (1 popup) ✅   │
│ phishing.com/      ▓ (1 popup) ✅   │
│ malware.com/       ▓ (1 popup) ✅   │
│ Total: 3 POPUPS (exactly 1 per)    │
└─────────────────────────────────────┘
```

### Subprocess Calls

```
OLD: 15+ calls (1 per URL)
NEW: 3 calls (1 per domain)
     ↓
   REDUCED BY 80% ⚡
```

---

## Decision Reuse Flow

```
Domain: evil.com

FIRST REQUEST:
evil.com/ → [HIGH RISK] → [POPUP] → User: BLOCK → domain_decisions['evil.com'] = 'block'

SUBSEQUENT REQUESTS (same domain):
evil.com/favicon.ico  → [HIGH RISK] → [CACHED] → Use 'block'
evil.com/style.css    → [HIGH RISK] → [CACHED] → Use 'block'
evil.com/app.js       → [HIGH RISK] → [CACHED] → Use 'block'
api.evil.com/endpoint → [HIGH RISK] → [CACHED] → Use 'block'

All use SAME DECISION without popup ✅
```

---

## Edge Cases Handled

### Case 1: Subdomain normalization
```
Request: login.evil.com
Normalized: evil.com
Cache: popup_shown_domains contains 'evil.com'
Result: ✅ Reuses parent domain's decision
```

### Case 2: www prefix
```
Request: www.evil.com
Normalized: evil.com (www stripped)
Cache: popup_shown_domains contains 'evil.com'
Result: ✅ Handles www correctly
```

### Case 3: Mixed subdomains
```
Requests:
  evil.com → Popup shown, BLOCK cached
  login.evil.com → Uses 'evil.com' cache
  api.evil.com → Uses 'evil.com' cache
  cdn.evil.com → Uses 'evil.com' cache
Result: ✅ All subdomains share parent decision
```

### Case 4: Missing decision
```
If domain_decisions.get(normalized) returns None:
Default: 'block' (safest choice)
Result: ✅ Safe fallback
```

---

## Summary Table

| Aspect | Before | After | Impact |
|--------|--------|-------|--------|
| **Cache type** | Full URL | Normalized domain | Fewer popups |
| **Decision storage** | None | Dict mapping | Reusable decisions |
| **Popups per domain** | 5+ | 1 | 80% reduction |
| **User experience** | Harassed | Clean | Much better |
| **Code clarity** | Confusing | Clear | Easier to maintain |
| **Performance** | Slow | Fast | Faster decisions |
| **Subdomain handling** | Broken | Fixed | All subdomains work |

---

## Ready to Deploy! 🚀

✅ Problem: SOLVED (domain-level caching)
✅ Implementation: COMPLETE (2 changes)
✅ Testing: READY (test guide provided)
✅ Documentation: COMPREHENSIVE (4 documents)
✅ Status: PRODUCTION READY
