# Code Reference - All Changes Made

## popup_simple.py Changes

### Change 1: Updated Constructor (lines 18-28)

```python
class PhishGuardPopup:
    """Aggressive enterprise-grade security popup for suspicious domain detection"""
    
    def __init__(self, domain: str, timeout_sec: int = 8, reasons: list = None):
        self.domain = domain
        self.timeout_sec = timeout_sec
        self.countdown = timeout_sec
        self.result = None
        self.details_expanded = False
        self.border_pulse_state = 0  # 0 = bright red, 1 = dark red
        self.animation_id = None
        self.countdown_animation_id = None  # NEW: Track countdown timer
        self.reasons = reasons if reasons else []  # NEW: Accept reasons
```

### Change 2: Updated populate_details() (lines 310-345)

**BEFORE:**
```python
def populate_details(self):
    """Populate details frame with threat information"""
    c = self.colors
    
    details_text = f"""Domain: {self.domain}

Threat Assessment:
  - Classified as high-risk phishing/malware domain
  - Malicious domain pattern detected
  - Potential credential theft attempt
  - Suspicious redirects or exploits identified

Recommended Action:
  - Block and report this domain
  - Do not enter any sensitive information
  - Contact your network administrator if this is a false positive

PhishGuard Risk Level: HIGH
Last Updated: Ongoing Monitoring"""
```

**AFTER:**
```python
def populate_details(self):
    """Populate details frame with threat information"""
    c = self.colors
    
    # Build threat assessment from actual reasons
    threat_section = "Threat Assessment:\n"
    if self.reasons and len(self.reasons) > 0:
        for reason in self.reasons:
            threat_section += f"  • {reason}\n"
    else:
        threat_section += """  • Classified as high-risk phishing/malware domain
  • Malicious domain pattern detected
  • Potential credential theft attempt
  • Suspicious redirects or exploits identified
"""
    
    details_text = f"""Domain: {self.domain}

{threat_section}
Recommended Action:
  • Block and report this domain
  • Do not enter any sensitive information
  • Contact your network administrator if this is a false positive

PhishGuard Risk Level: HIGH
Last Updated: Ongoing Monitoring"""
```

### Change 3: Updated show_popup_gui() (lines 419-432)

**BEFORE:**
```python
def show_popup_gui(domain: str, timeout_sec: int = 8) -> str:
    """
    Show aggressive antivirus-style popup for suspicious domain detection.
    
    Args:
        domain: The suspicious domain detected
        timeout_sec: Auto-block countdown in seconds (default 8)
    
    Returns:
        "BLOCK" or "ALLOW" string
    """
    popup = PhishGuardPopup(domain, timeout_sec)
    return popup.run()
```

**AFTER:**
```python
def show_popup_gui(domain: str, timeout_sec: int = 8, reasons: list = None) -> str:
    """
    Show aggressive antivirus-style popup for suspicious domain detection.
    
    Args:
        domain: The suspicious domain detected
        timeout_sec: Auto-block countdown in seconds (default 8)
        reasons: List of detection reasons (optional)
    
    Returns:
        "BLOCK" or "ALLOW" string
    """
    popup = PhishGuardPopup(domain, timeout_sec, reasons)
    return popup.run()
```

### Change 4: Enhanced stop_animation() (lines 355-363)

**BEFORE:**
```python
def stop_animation(self):
    """Stop the border pulsation animation"""
    if self.animation_id is not None:
        self.root.after_cancel(self.animation_id)
        self.animation_id = None
```

**AFTER:**
```python
def stop_animation(self):
    """Stop both border pulsation and countdown animations"""
    if self.animation_id is not None:
        self.root.after_cancel(self.animation_id)
        self.animation_id = None
    if self.countdown_animation_id is not None:
        self.root.after_cancel(self.countdown_animation_id)
        self.countdown_animation_id = None
```

### Change 5: Updated update_countdown() (lines 345-355)

**BEFORE:**
```python
def update_countdown(self):
    """Update countdown timer every second"""
    if self.countdown > 0:
        self.countdown_label.config(text=f"Auto-block in: {self.countdown} seconds")
        self.countdown -= 1
        self.root.after(1000, self.update_countdown)
    else:
        # Auto-block when countdown reaches zero
        self.result = "BLOCK"
        self.stop_animation()
        self.root.destroy()
```

**AFTER:**
```python
def update_countdown(self):
    """Update countdown timer every second"""
    if self.countdown > 0:
        self.countdown_label.config(text=f"Auto-block in: {self.countdown} seconds")
        self.countdown -= 1
        self.countdown_animation_id = self.root.after(1000, self.update_countdown)  # CHANGED
    else:
        # Auto-block when countdown reaches zero
        self.result = "BLOCK"
        self.stop_animation()
        self.root.destroy()
```

### Change 6: Updated main() (lines 536-562)

**BEFORE:**
```python
def main():
    """
    Main entry point - called from proxy_simple.py subprocess.
    Arguments: domain_name
    Returns: BLOCK or ALLOW via stdout
    """
    if len(sys.argv) < 2:
        print("BLOCK", file=sys.stdout)
        sys.exit(0)
    
    domain = sys.argv[1]
    
    try:
        # Show popup with 8-second auto-block countdown
        result = show_popup_gui(domain, timeout_sec=8)
        
        # Output result to stdout (proxy_simple.py will read this)
        if result in ["BLOCK", "ALLOW"]:
            print(result, file=sys.stdout)
            sys.exit(0)
        else:
            print("BLOCK", file=sys.stdout)
            sys.exit(0)
    except Exception as e:
        print("BLOCK", file=sys.stderr)
        sys.exit(0)
```

**AFTER:**
```python
def main():
    """
    Main entry point - called from proxy_simple.py subprocess.
    Arguments: domain_name [reasons_json]
    Returns: BLOCK or ALLOW via stdout
    """
    if len(sys.argv) < 2:
        print("BLOCK", file=sys.stdout)
        sys.exit(0)
    
    domain = sys.argv[1]
    reasons = []
    
    # Parse optional reasons as JSON
    if len(sys.argv) > 2:
        try:
            import json
            reasons = json.loads(sys.argv[2])
            if not isinstance(reasons, list):
                reasons = []
        except Exception:
            reasons = []
    
    try:
        # Show popup with 8-second auto-block countdown
        result = show_popup_gui(domain, timeout_sec=8, reasons=reasons)
        
        # Output result to stdout (proxy_simple.py will read this)
        if result in ["BLOCK", "ALLOW"]:
            print(result, file=sys.stdout)
            sys.exit(0)
        else:
            print("BLOCK", file=sys.stdout)
            sys.exit(0)
    except Exception as e:
        print("BLOCK", file=sys.stderr)
        sys.exit(0)
```

---

## proxy_simple.py Changes

### Change 1: Updated Addon.__init__() (line 60)

**BEFORE:**
```python
class Addon:
    """mitmproxy addon for phishing detection - optimized performance"""
    
    def __init__(self):
        """Initialize addon with ML analyzer"""
        self.script_dir = os.path.dirname(__file__)
        self.error_log_file = os.path.join(self.script_dir, "proxy_errors.log")
        
        # Absolute paths for critical files
        self.popup_path = os.path.join(self.script_dir, "popup_simple.py")
        self.blocked_page_path = os.path.join(self.script_dir, "blocked_page.html")
        self.ml_api_url = "http://127.0.0.1:8000/score"
        
        # Clear old log on startup
        try:
            if os.path.exists(self.error_log_file):
                open(self.error_log_file, 'w').close()
        except:
            pass
        
        self.log_error("[PhishGuard] Addon initialized - ML ANALYZER MODE")
```

**AFTER:**
```python
class Addon:
    """mitmproxy addon for phishing detection - optimized performance"""
    
    def __init__(self):
        """Initialize addon with ML analyzer"""
        self.script_dir = os.path.dirname(__file__)
        self.error_log_file = os.path.join(self.script_dir, "proxy_errors.log")
        
        # Absolute paths for critical files
        self.popup_path = os.path.join(self.script_dir, "popup_simple.py")
        self.blocked_page_path = os.path.join(self.script_dir, "blocked_page.html")
        self.ml_api_url = "http://127.0.0.1:8000/score"
        
        # Track URLs where popup has been shown to prevent duplicate popups
        self.popup_shown_urls = set()  # NEW
        
        # Clear old log on startup
        try:
            if os.path.exists(self.error_log_file):
                open(self.error_log_file, 'w').close()
        except:
            pass
        
        self.log_error("[PhishGuard] Addon initialized - ML ANALYZER MODE")
```

### Change 2: Updated request() Method (lines 209-226)

**Key additions in the HIGH RISK decision block:**

```python
if risk == 'high':
    # GUARD: Check if popup already shown for this URL (prevent duplicate popups)
    if full_url and full_url in self.popup_shown_urls:
        self.log_error(f"[Decision] Popup already shown for this URL, skipping: {full_url}")
        # Use previous decision (block)
        show_popup_decision = 'block'
    else:
        self.log_error(f"[Decision] HIGH RISK detected, showing popup: {domain}")
        self.log_error(f"[POPUP] Triggered for URL: {full_url or domain} (once only)")  # NEW: Debug log
        
        # Mark this URL as having a popup shown
        if full_url:
            self.popup_shown_urls.add(full_url)  # NEW: Add to cache
        
        try:
            if popup_simple and hasattr(popup_simple, 'show_popup'):
                result = popup_simple.show_popup(full_url or domain, score, reasons)
                show_popup_decision = str(result).lower()
            else:
                show_popup_decision = self.show_popup_subprocess(domain, reasons).lower()  # CHANGED: Pass reasons
        except Exception as e:
            self.log_error(f"[Popup Error] {e}")
            show_popup_decision = 'block'
```

### Change 3: Updated show_popup_subprocess() (lines 300-345)

**BEFORE:**
```python
def show_popup_subprocess(self, domain: str) -> str:
    """
    Call popup_simple.py as subprocess.
    OPTIMIZATION: Uses cached absolute path (self.popup_path).
    Returns: "ALLOW", "BLOCK", or "TIMEOUT"
    """
    try:
        self.log_error(f"[Popup] Calling: {self.popup_path} with domain: {domain}")
        ctx.log.info(f"[PhishGuard] Calling popup: {domain}")
        
        if not os.path.exists(self.popup_path):
            self.log_error(f"[Popup Error] popup_simple.py not found at: {self.popup_path}")
            ctx.log.error(f"[PhishGuard] popup_simple.py not found")
            return "TIMEOUT"
        
        # Call popup_simple.py with domain as argument
        # Wait for stdout result with 35-second timeout (includes 8-second popup countdown)
        proc = subprocess.Popen(
            [sys.executable, self.popup_path, domain],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.script_dir
        )
        
        # ... rest of method
```

**AFTER:**
```python
def show_popup_subprocess(self, domain: str, reasons: list = None) -> str:  # CHANGED: Added reasons parameter
    """
    Call popup_simple.py as subprocess with domain and reasons.
    OPTIMIZATION: Uses cached absolute path (self.popup_path).
    Returns: "ALLOW", "BLOCK", or "TIMEOUT"
    """
    try:
        self.log_error(f"[Popup] Calling: {self.popup_path} with domain: {domain}")
        ctx.log.info(f"[PhishGuard] Calling popup: {domain}")
        
        if not os.path.exists(self.popup_path):
            self.log_error(f"[Popup Error] popup_simple.py not found at: {self.popup_path}")
            ctx.log.error(f"[PhishGuard] popup_simple.py not found")
            return "TIMEOUT"
        
        # Prepare arguments  # NEW BLOCK
        args = [sys.executable, self.popup_path, domain]
        
        # Add reasons as JSON if provided
        if reasons and len(reasons) > 0:
            import json
            reasons_json = json.dumps(reasons)
            args.append(reasons_json)
        
        # Call popup_simple.py with domain and optional reasons
        # Wait for stdout result with 35-second timeout (includes 8-second popup countdown)
        proc = subprocess.Popen(
            args,  # CHANGED: Use args instead of hardcoded list
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.script_dir
        )
        
        # ... rest of method unchanged
```

---

## Summary of All Changes

| File | Lines | Change Type | Impact |
|------|-------|-------------|--------|
| popup_simple.py | 18-28 | Constructor enhancement | Accept reasons |
| popup_simple.py | 310-345 | Method update | Dynamic reason display |
| popup_simple.py | 345-355 | Method update | Track countdown timer |
| popup_simple.py | 355-363 | Method enhancement | Clean animation stop |
| popup_simple.py | 419-432 | Function signature | Accept reasons param |
| popup_simple.py | 536-562 | Main function | Parse JSON reasons |
| proxy_simple.py | 60 | Constructor enhancement | Add popup cache |
| proxy_simple.py | 209-226 | Method update | Duplicate prevention |
| proxy_simple.py | 300-345 | Function signature | Pass reasons to popup |

---

## Testing the Changes

### Test 1: Scroll Support
```python
# popup_simple.py should parse and display reasons:
python popup_simple.py "example.com" '["Reason 1", "Reason 2", "Reason 3", "Reason 4", "Reason 5"]'
# Expected: Popup with scrollbar
```

### Test 2: Duplicate Prevention
```python
# In proxy_simple.py, check logs for:
[POPUP] Triggered for URL: ... (once only)
# Should appear only ONCE per unique URL
```

### Test 3: Animation
```python
# Run launcher:
python launcher.py
# Expected: Red border pulses continuously (bright ↔ dark) every 500ms
```

---

## Integration Flow

```
user visits risky domain
    ↓
proxy_simple.py::request() called
    ↓
ML analyzer scores domain (HIGH RISK)
    ↓
Check popup_shown_urls set
    ├─ URL in cache? → Block directly
    └─ URL not in cache?
        ↓
        Add URL to popup_shown_urls
        ↓
        Call show_popup_subprocess(domain, reasons)
        ↓
        subprocess: python popup_simple.py domain reasons_json
        ↓
        popup_simple.py::main() parses arguments
        ↓
        show_popup_gui(domain, timeout_sec=8, reasons=reasons)
        ↓
        PhishGuardPopup.__init__() with reasons
        ↓
        populate_details() renders dynamic threat assessment
        ↓
        animate_border() pulses red (with timer tracking)
        ↓
        User clicks BLOCK/ALLOW
        ↓
        on_block() / on_allow() calls stop_animation()
        ↓
        Popup returns result to stdout
        ↓
        proxy_simple.py receives result
        ↓
        Apply decision (block or allow request)
```

---

## Verification Commands

```powershell
# Check Python syntax
python -m py_compile popup_simple.py
python -m py_compile proxy_simple.py

# Run launcher with verbose output
python launcher.py 2>&1 | Select-Object -First 200

# Monitor logs in real-time
Get-Content proxy_errors.log -Wait

# Check popup is triggered only once
Get-Content proxy_errors.log | Select-String "\[POPUP\]"
# Should show each URL only once
```
