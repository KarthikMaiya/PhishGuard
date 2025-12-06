# Domain-Level Caching: Testing Guide

## 🚀 Quick Start

### Step 1: Deploy the Fix
```powershell
cd 'C:\Users\Karthik Maiya\Desktop\PhishGuard_v2'

# Verify syntax
python -m py_compile proxy_simple.py
# Expected: (no output = success)

# Start mitmproxy
python launcher.py
```

### Step 2: Start Chrome with mitmproxy
```powershell
# In a new terminal
start "C:\Program Files\Google\Chrome\Application\chrome.exe" --proxy-server="http://127.0.0.1:8080"
```

### Step 3: Test

Visit test URLs and verify behavior matches expectations.

---

## 🧪 Test Suite

### TEST 1: Single Domain, Multiple Resources
**Objective:** Verify popup appears ONCE even with multiple resources

**Setup:**
- Ensure high-risk domain in ML analyzer
- Open Chrome with mitmproxy proxy
- Clear proxy_errors.log

**Steps:**
```
1. Navigate to: https://[HIGH-RISK-DOMAIN]/
   Expected: Popup appears with red pulsing border
   
2. Wait for favicon auto-load
   Expected: NO popup (same domain cached)
   
3. Wait for CSS/JS auto-load
   Expected: NO popup (same domain cached)
   
4. Trigger manifest.json load
   Expected: NO popup (same domain cached)
```

**Verification:**
```powershell
# Check log shows domain cached
Get-Content proxy_errors.log | Select-String "HIGH RISK - NEW domain" | Measure-Object
# Should show: Count = 1

Get-Content proxy_errors.log | Select-String "Popup already shown for domain" | Measure-Object
# Should show: Count = 3+ (one per additional resource)
```

**Result:** ✅ PASS if popup appeared only once
**Result:** ❌ FAIL if popup appeared multiple times

---

### TEST 2: BLOCK Decision Persistence
**Objective:** Verify BLOCK decision cached and reused

**Setup:**
- Same high-risk domain
- Popup visible

**Steps:**
```
1. Popup appears
   Expected: Red border pulsing, countdown showing

2. Click "BLOCK THIS WEBSITE" button
   Expected: Popup closes, block page shows

3. Wait 2 seconds for subresources to load
   Expected: NO new popups appear
   Expected: Resources blocked

4. Refresh page (F5)
   Expected: Block page shown immediately (no popup, reused BLOCK decision)
```

**Verification:**
```powershell
# Check log shows BLOCK decision cached
Get-Content proxy_errors.log | Select-String "User decision.*BLOCK"
# Should show: BLOCK logged for domain

Get-Content proxy_errors.log | Select-String "Cached decision.*BLOCK"
# Should show multiple times (once per resource after first)
```

**Result:** ✅ PASS if BLOCK decision cached and reused
**Result:** ❌ FAIL if popup reappears after block

---

### TEST 3: ALLOW Decision Persistence
**Objective:** Verify ALLOW decision cached and reused

**Setup:**
- Different high-risk domain than TEST 1
- Open proxy_errors.log for monitoring

**Steps:**
```
1. Navigate to: https://[HIGH-RISK-DOMAIN-2]/
   Expected: Popup appears

2. Click "Allow Anyway" button
   Expected: Popup closes, page loads normally

3. Page loads resources
   Expected: NO popups appear

4. Check that page content loads normally
   Expected: Images, CSS, JS all load
   Expected: Page displays correctly
```

**Verification:**
```powershell
# Check log shows ALLOW decision cached
Get-Content proxy_errors.log | Select-String "User decision.*ALLOW"
# Should show: ALLOW logged

Get-Content proxy_errors.log | Select-String "Cached decision.*ALLOW"
# Should show multiple times
```

**Result:** ✅ PASS if ALLOW decision works and page loads
**Result:** ❌ FAIL if page doesn't load or popup reappears

---

### TEST 4: Subdomain Handling
**Objective:** Verify subdomains treated as same root domain

**Setup:**
- High-risk domain with subdomains
- Example: `evil.com`, `login.evil.com`, `api.evil.com`

**Steps:**
```
1. Navigate to: https://evil.com/
   Expected: Popup appears once

2. Click "BLOCK THIS WEBSITE"
   Expected: Block page shown

3. Navigate to: https://login.evil.com/
   Expected: NO popup (same root domain, already cached)
   Expected: Block page shown (cached BLOCK decision)

4. Navigate to: https://api.evil.com/
   Expected: NO popup (same root domain)
   Expected: Block page shown (cached BLOCK decision)
```

**Verification:**
```powershell
# Check log shows normalized domain
Get-Content proxy_errors.log | Select-String "evil.com"
# Should show: All subdomains reference same "evil.com" domain

# Count HIGH RISK popups for evil domain
Get-Content proxy_errors.log | Select-String "HIGH RISK.*evil.com" | Measure-Object
# Should show: Count = 1 (only first request)
```

**Result:** ✅ PASS if subdomains share same decision
**Result:** ❌ FAIL if subdomains trigger separate popups

---

### TEST 5: Different Domains Independently
**Objective:** Verify different domains have independent decisions

**Setup:**
- Three high-risk domains ready
- Example: `domain-a.com`, `domain-b.com`, `domain-c.com`

**Steps:**
```
1. Navigate to: https://domain-a.com/
   Expected: Popup appears
   Click: "BLOCK THIS WEBSITE"
   Expected: Block page shown

2. Navigate to: https://domain-b.com/
   Expected: NEW popup appears (different domain)
   Click: "Allow Anyway"
   Expected: Page loads normally

3. Navigate to: https://domain-c.com/
   Expected: NEW popup appears (third domain)
   Click: "BLOCK THIS WEBSITE"
   Expected: Block page shown

4. Navigate back to: https://domain-a.com/
   Expected: NO popup (reused cached BLOCK decision)
   Expected: Block page shown

5. Navigate back to: https://domain-b.com/
   Expected: NO popup (reused cached ALLOW decision)
   Expected: Page loads normally
```

**Verification:**
```powershell
# Check each domain has independent decisions
Get-Content proxy_errors.log | Select-String "User decision"
# Should show:
#   domain-a.com: BLOCK
#   domain-b.com: ALLOW
#   domain-c.com: BLOCK

# Count total HIGH RISK NEW popups shown
Get-Content proxy_errors.log | Select-String "HIGH RISK - NEW domain" | Measure-Object
# Should show: Count = 3 (one per domain, first request only)
```

**Result:** ✅ PASS if each domain maintains independent decision
**Result:** ❌ FAIL if decisions interfere with each other

---

### TEST 6: Log Output Quality
**Objective:** Verify logging is clear and informative

**Setup:**
- Run TEST 1 while monitoring logs

**Expected Log Sequence:**
```
[Decision] HIGH RISK - NEW domain, showing popup: domain.com
[POPUP] Calling subprocess: C:\...\popup_simple.py domain.com
[Popup] User decision for domain.com: BLOCK
[Decision] Blocking domain: domain.com

[Decision] Popup already shown for domain, using cached decision: domain.com
[Decision] Cached decision for domain.com: BLOCK
[Decision] Blocking domain: domain.com

[Decision] Popup already shown for domain, using cached decision: domain.com
[Decision] Cached decision for domain.com: BLOCK
[Decision] Blocking domain: domain.com
```

**Verification:**
```powershell
# View log file
Get-Content proxy_errors.log -Tail 50

# Should show clear progression:
# 1. First request: "HIGH RISK - NEW domain"
# 2. Subsequent requests: "Popup already shown for domain"
```

**Result:** ✅ PASS if logs are clear and show caching working
**Result:** ❌ FAIL if logs show multiple "NEW domain" messages

---

## 🔍 Debugging Tips

### Popup Not Appearing at All
```powershell
# Check ML analyzer running
curl http://127.0.0.1:8000/score -Method POST -Body '{"url":"test"}'
# Should get response (not timeout)

# Check popup_simple.py exists
Test-Path 'C:\Users\Karthik Maiya\Desktop\PhishGuard_v2\popup_simple.py'
# Should output: True

# Check mitmproxy log for errors
Get-Content proxy_errors.log | Select-String "ERROR"
```

### Popup Appearing Multiple Times
```powershell
# Check normalize_domain working
# Add test code:
#   print(self.normalize_domain("www.evil.com"))  # Should print: evil.com
#   print(self.normalize_domain("login.evil.com")) # Should print: evil.com

# Check popup_shown_domains being populated
Get-Content proxy_errors.log | Select-String "popup_shown_domains"

# Verify domain-level caching initialized
python -c "
import proxy_simple
addon = proxy_simple.Addon()
print(f'popup_shown_domains: {addon.popup_shown_domains}')
print(f'domain_decisions: {addon.domain_decisions}')
"
```

### Decisions Not Persisting
```powershell
# Check domain_decisions dict being updated
Get-Content proxy_errors.log | Select-String "User decision"

# Should show decision being stored on first request
# And reused on subsequent requests
```

---

## 📊 Expected Results Summary

| Test | Expected | Status |
|------|----------|--------|
| TEST 1: Single domain, multiple resources | 1 popup | ✅ |
| TEST 2: BLOCK decision cached | No popup on refresh | ✅ |
| TEST 3: ALLOW decision cached | Page loads on second visit | ✅ |
| TEST 4: Subdomain handling | All subdomains share decision | ✅ |
| TEST 5: Different domains independent | Each domain has own decision | ✅ |
| TEST 6: Logging clear | Shows "NEW domain" once, then "cached" | ✅ |

---

## ✅ Completion Checklist

After running all tests:

- [ ] TEST 1: PASS - Single domain shows popup once ✅
- [ ] TEST 2: PASS - BLOCK decision cached ✅
- [ ] TEST 3: PASS - ALLOW decision cached ✅
- [ ] TEST 4: PASS - Subdomains handled correctly ✅
- [ ] TEST 5: PASS - Different domains independent ✅
- [ ] TEST 6: PASS - Logging is clear ✅

**Final Result:**
- All tests pass: ✅ **DOMAIN-LEVEL CACHING WORKING**
- Any test fails: ❌ Check proxy_errors.log and debug

---

## 🚀 Production Deployment

Once all tests pass:

```powershell
# 1. Keep mitmproxy running with fixed addon
python launcher.py

# 2. Users can now browse safely
# - Popups appear once per domain
# - No popup spam from subresources
# - Decisions cached within session
# - Works like enterprise security tools

# 3. Monitor proxy_errors.log for issues
Get-Content -Path proxy_errors.log -Wait -Tail 5
```

---

**Test Duration:** ~10-15 minutes
**Difficulty:** Easy (just navigate and click)
**Automation:** Optional (can automate with Selenium)

**Status:** Ready for testing! 🎉
