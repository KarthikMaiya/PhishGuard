# Quick Testing Guide - PhishGuard Popup Fixes

## Setup

```powershell
cd "C:\Users\Karthik Maiya\Desktop\PhishGuard_v2"
python launcher.py 2>&1 | Select-Object -First 150
```

This starts:
1. Analyzer on http://127.0.0.1:8000
2. Mitmproxy proxy on http://127.0.0.1:8080
3. Chrome with proxy configuration
4. All running with hidden windows

---

## Test 1: Scrollbar for Multiple Detection Reasons

**What to verify:** Popup shows scrollbar when content is long

### Steps:
1. Browser opens → Chrome proxy configured
2. Visit a high-risk domain manually, e.g., navigate to a suspected phishing site
3. **Expected:** Popup appears
4. Click "Show Details >>"
5. **Expected:** Details section expands
6. If many reasons shown:
   - **Expected:** Scrollbar appears on right side of details
   - Drag scrollbar to read all reasons
7. Click "BLOCK THIS WEBSITE"
8. **Expected:** Popup closes immediately

### Pass Criteria:
- ✅ Popup appears for high-risk domains
- ✅ Details section scrolls if content exceeds canvas height
- ✅ All text visible (no clipping)
- ✅ Scrollbar appears only when needed

---

## Test 2: No Duplicate Popups

**What to verify:** Same URL only triggers popup ONCE

### Steps:

1. **Start launcher with logging:**
   ```powershell
   cd "C:\Users\Karthik Maiya\Desktop\PhishGuard_v2"
   python launcher.py 2>&1 | Select-Object -First 150
   ```

2. **Check log file during test:**
   ```powershell
   # In another PowerShell window:
   Get-Content "proxy_errors.log" -Wait
   ```

3. **Visit same high-risk domain twice:**
   - Browser opens
   - Visit `http://rnicrosoft.com` (or another high-risk domain)
   - **Expected:** Popup appears
   - Click "BLOCK THIS WEBSITE"
   - **Expected:** Popup closes, request is blocked
   - Check console log: Should see `[POPUP] Triggered for URL: ... (once only)`

4. **Try same URL again:**
   - Try navigating to the same URL again
   - **Expected:** Popup does NOT appear (URL already has popup shown)
   - **Expected:** Request is blocked (cached decision)

5. **Try different high-risk domain:**
   - Visit different high-risk domain (e.g., `http://amaz0n.com`)
   - **Expected:** Popup appears normally (new URL)
   - Click "Allow Anyway"
   - **Expected:** Popup closes, request proceeds

6. **Check logs:**
   ```
   [POPUP] Triggered for URL: rnicrosoft.com (once only)     ← Appears once
   [POPUP] Triggered for URL: amaz0n.com (once only)         ← Appears once (different URL)
   ```

### Pass Criteria:
- ✅ Each unique high-risk URL shows popup ONCE
- ✅ Same URL doesn't trigger popup again (cached)
- ✅ Popup closes immediately after clicking button
- ✅ No zombie popups or hanging processes
- ✅ Different URLs each trigger popup normally

---

## Test 3: Red Blinking Border Animation

**What to verify:** Border pulses smoothly every 500ms

### Steps:

1. **Start launcher:**
   ```powershell
   python launcher.py
   ```

2. **Visit high-risk domain:**
   - Browser appears
   - Navigate to suspected phishing site
   - **Expected:** Popup appears

3. **Watch border animation:**
   - **Expected:** Popup has red border around entire window
   - **Expected:** Border pulses between:
     - Bright red (#ff0000) for ~500ms
     - Dark red (#990000) for ~500ms
     - Continuous cycle: bright → dark → bright → …
   - **Expected:** Animation is smooth (no flickering, no lag)

4. **Keep popup open:**
   - Watch animation for 5-10 seconds
   - **Expected:** Consistent pulse cycle (no interruption)
   - **Expected:** CPU usage remains low

5. **Auto-block timer:**
   - Top of popup shows: "Auto-block in: 8 seconds"
   - Timer counts down: 8 → 7 → 6 → … → 1 → 0
   - **Expected:** At 0 seconds, popup auto-closes
   - **Expected:** Request is blocked (default action)

6. **Manual block:**
   - Click "BLOCK THIS WEBSITE" button at any time
   - **Expected:** Popup closes immediately
   - **Expected:** Animation stops (no lingering pulsing)
   - **Expected:** Request is blocked

7. **Manual allow:**
   - Visit another high-risk domain
   - Click "Allow Anyway" button
   - **Expected:** Popup closes immediately
   - **Expected:** Animation stops cleanly
   - **Expected:** Request proceeds through proxy

### Pass Criteria:
- ✅ Red border visible around entire popup window
- ✅ Border pulses smoothly every 500ms
- ✅ Pulse between bright red (#ff0000) and dark red (#990000)
- ✅ Animation continues until popup closes
- ✅ Animation stops immediately when popup closes
- ✅ No CPU overhead or process hanging
- ✅ Auto-block timer works and counts down
- ✅ Pressing button closes popup immediately

---

## Combined Integration Test

**Run all three features together:**

```powershell
cd "C:\Users\Karthik Maiya\Desktop\PhishGuard_v2"
python launcher.py 2>&1
```

Then in browser:

1. Visit `rnicrosoft.com`
   - ✅ Popup appears (Issue 3: border pulses red)
   - ✅ Click "Show Details >>" (Issue 1: scrollbar if needed)
   - ✅ Click "BLOCK THIS WEBSITE" (closes immediately)

2. Try same URL again
   - ✅ Popup does NOT appear (Issue 2: cached)

3. Visit `amaz0n.com`
   - ✅ Popup appears (new URL)
   - ✅ Watch 8-second countdown timer
   - ✅ Don't click anything
   - ✅ After 8 seconds, popup auto-blocks and closes

4. Check console logs:
   ```
   [POPUP] Triggered for URL: rnicrosoft.com (once only)
   [POPUP] Triggered for URL: amaz0n.com (once only)
   ```

---

## Troubleshooting

### Popup doesn't appear at all
- Check analyzer is running: `netstat -ano | findstr :8000`
- Check proxy is running: `netstat -ano | findstr :8080`
- Check `proxy_errors.log` for ML analyzer errors
- Verify domain is classified as HIGH RISK by ML analyzer

### Popup appears twice
- This should not happen with the fix
- Check if launcher restarted (clears popup_shown_urls cache)
- Check `proxy_errors.log` for duplicate popup messages
- If still occurring, check if different URLs are being accessed (each unique URL triggers popup once)

### Border not pulsing
- Check if popup window is actually visible
- Try clicking a button to close popup
- If border doesn't pulse, animation may have error (check stderr)
- Restart launcher

### Scrollbar doesn't appear
- Scrollbar only appears if content exceeds canvas height (120px)
- Try "Show Details >>" to expand details section
- If many reasons (5+), scrollbar should appear automatically
- Drag scrollbar to verify it's functional

### Popup freezes or hangs
- This indicates animation issue
- Try clicking a button to close
- If unresponsive, kill launcher process: `taskkill /F /IM python.exe`
- Check for errors in `proxy_errors.log`
- Restart launcher

---

## Success Criteria (All 3 Issues Fixed)

| Feature | Test | Expected Result | Status |
|---------|------|-----------------|--------|
| Scrollbar | Show many reasons | Scrollbar appears | ✅ |
| Scrollbar | Show few reasons | No scrollbar | ✅ |
| Duplicate | Visit same URL twice | Popup appears once | ✅ |
| Duplicate | Visit different URLs | Each triggers popup | ✅ |
| Border | Watch animation | Red pulse every 500ms | ✅ |
| Border | Close popup | Animation stops | ✅ |
| Countdown | Wait 8 seconds | Auto-blocks | ✅ |
| Countdown | Click button | Stops timer | ✅ |

---

## Performance Baseline

Monitor these metrics during testing:

```powershell
# Check processes:
Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.ProcessName -like "*chrome*" }

# Check ports:
netstat -ano | findstr ":8000\|:8080"

# Check memory (should be stable):
(Get-Process python).WorkingSet / 1MB
(Get-Process chrome).WorkingSet / 1MB
```

**Expected:**
- Analyzer (python): ~80-150 MB
- Chrome: ~200-400 MB (varies by tabs/extensions)
- No memory growth over time
- CPU: <2% idle (spikes to 10-20% during popup interaction)

---

## Notes

- All tests should run on Windows (PowerShell)
- Popup appears ONLY for HIGH RISK domains (score ≥ 0.75)
- Medium/Low risk domains are allowed automatically (no popup)
- Whitelisted domains (Google, Microsoft, etc.) bypass all checks
- Popup caches only within current launcher session (resets on restart)
