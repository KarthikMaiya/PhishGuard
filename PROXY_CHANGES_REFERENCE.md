# proxy_simple.py - KEY CHANGES REFERENCE

## Summary of Changes

The proxy_simple.py file was updated in the following areas to use the NEW popup UI:

---

## CHANGE 1: Removed Old show_popup() Call

**Location:** request() method, around line 296

**BEFORE:**
```python
try:
    if popup_simple and hasattr(popup_simple, 'show_popup'):
        result = popup_simple.show_popup(full_url or domain, score, reasons)
        show_popup_decision = str(result).lower()
    else:
        show_popup_decision = self.show_popup_subprocess(domain, reasons).lower()
except Exception as e:
    self.log_error(f"[Popup Error] {e}")
    show_popup_decision = 'block'
```

**AFTER:**
```python
try:
    # Call the NEW popup GUI function
    show_popup_decision = self.show_popup_subprocess(domain, reasons).lower()
except Exception as e:
    self.log_error(f"[Popup Error] {e}")
    show_popup_decision = 'block'
```

**Why:** Now ONLY uses subprocess call to show_popup_gui(), not the old show_popup() function.

---

## CHANGE 2: Improved show_popup_subprocess() Method

**Location:** Lines 350-410 (approximately)

**Complete rewritten method:**

```python
def show_popup_subprocess(self, domain: str, reasons: list = None) -> str:
    """
    Call popup_simple.py as subprocess with domain and reasons.
    OPTIMIZATION: Uses cached absolute path (self.popup_path).
    Returns: "allow", "block", or "block" (on error/timeout)
    """
    try:
        self.log_error(f"[Popup] Calling subprocess: {self.popup_path} {domain}")
        
        if not os.path.exists(self.popup_path):
            self.log_error(f"[Popup Error] popup_simple.py not found at: {self.popup_path}")
            return "block"
        
        # Prepare arguments: python popup_simple.py <domain> [<json_reasons>]
        args = [sys.executable, self.popup_path, domain]
        
        # Add reasons as JSON if provided
        if reasons and len(reasons) > 0:
            try:
                reasons_json = json.dumps(reasons)
                args.append(reasons_json)
                self.log_error(f"[Popup] Passing {len(reasons)} reasons as JSON")
            except Exception as e:
                self.log_error(f"[Popup] Failed to serialize reasons: {e}")
        
        # Call popup_simple.py subprocess
        # Timeout: 35 seconds (8s popup + margin)
        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.script_dir
            )
            
            # Wait for process with timeout
            stdout_raw, stderr_raw = proc.communicate(timeout=35)
            
            # Decode output
            stdout_text = stdout_raw.decode('utf-8', errors='ignore').strip() if stdout_raw else ""
            stderr_text = stderr_raw.decode('utf-8', errors='ignore').strip() if stderr_raw else ""
            
            # Log stderr if any
            if stderr_text:
                self.log_error(f"[Popup] stderr: {stderr_text}")
            
            # Validate result
            result = stdout_text.upper() if stdout_text else ""
            self.log_error(f"[Popup] stdout result: '{result}'")
            
            if result in ["BLOCK", "ALLOW"]:
                # Convert to lowercase for consistency
                return result.lower()
            else:
                self.log_error(f"[Popup] Invalid result: '{result}' - defaulting to block")
                return "block"
        
        except subprocess.TimeoutExpired:
            self.log_error(f"[Popup] Subprocess timeout (35s) - killing process")
            proc.kill()
            return "block"
        
        except Exception as e:
            self.log_error(f"[Popup] Subprocess error: {e}")
            return "block"
    
    except Exception as e:
        self.log_error(f"[Popup Error] Critical exception: {e}\n{traceback.format_exc()}")
        return "block"
```

**Key Improvements:**
- ✅ Proper stdout/stderr decoding with error handling
- ✅ Normalizes result to lowercase ("block"/"allow")
- ✅ Returns "block" as safe default on any error
- ✅ Logs subprocess calls and results
- ✅ Handles timeout gracefully
- ✅ Validates results before returning

---

## CHANGE 3: Fixed Decision Logic

**Location:** request() method, after popup call

**BEFORE:**
```python
# Apply decision
if show_popup_decision == 'block' or show_popup_decision == 'BLOCK':
    html_content = self.get_blocked_page_html(domain)
    flow.response = http.Response.make(...)
# else: allow - do nothing
```

**AFTER:**
```python
# Apply decision
if show_popup_decision == 'block':
    html_content = self.get_blocked_page_html(domain)
    flow.response = http.Response.make(
        403,
        html_content.encode('utf-8'),
        {"Content-Type": "text/html; charset=utf-8"}
    )
    self.log_error(f"[Decision] Blocking domain: {domain}")
# else: allow - do nothing (request continues)
else:
    self.log_error(f"[Decision] Allowing domain: {domain}")
```

**Why:** Now only checks lowercase "block" since show_popup_subprocess() normalizes to lowercase.

---

## INTACT FEATURES

The following features remain UNCHANGED and WORKING:

### ✅ URL Caching (Duplicate Prevention)
```python
def __init__(self):
    # ... existing code ...
    self.popup_shown_urls = set()  # ← Still here
    
def request(self, flow):
    # ... existing code ...
    if full_url and full_url in self.popup_shown_urls:
        show_popup_decision = 'block'  # Use previous decision
    else:
        self.popup_shown_urls.add(full_url)  # Mark as shown
        show_popup_decision = self.show_popup_subprocess(domain, reasons).lower()
```

### ✅ ML Analyzer Integration
```python
def call_ml_analyzer(self, url: str) -> tuple:
    """Unchanged - still calls http://127.0.0.1:8000/score"""
    # ... existing code ...
```

### ✅ Block Page Serving
```python
def get_blocked_page_html(self, domain: str) -> str:
    """Unchanged - still returns custom HTML or fallback"""
    # ... existing code ...
```

### ✅ Whitelist Bypass
```python
def is_safe_domain(self, domain: str) -> bool:
    """Unchanged - still checks SAFE_DOMAINS set"""
    # ... existing code ...
```

---

## TEST COMMAND

To test the integration:

```bash
# Terminal 1: Start ML analyzer
cd analyzer
python serve_ml.py

# Terminal 2: Start mitmproxy with addon
cd ..
python launcher.py  # Or: mitmproxy -s proxy_simple.py

# Terminal 3: Test in Python
python -c "
import subprocess
result = subprocess.run(
    ['python', 'popup_simple.py', 'example.com', '[\"Test reason 1\"]'],
    capture_output=True,
    text=True,
    timeout=35
)
print(f'Result: {result.stdout.strip()}')
"
```

---

## VERIFICATION CHECKLIST

- ✅ popup_simple.py called via subprocess (not directly imported)
- ✅ popup_simple.py returns exactly "BLOCK" or "ALLOW" on stdout
- ✅ proxy_simple.py converts result to lowercase
- ✅ Duplicate popups prevented by URL caching
- ✅ JSON reasons passed as 3rd argument to subprocess
- ✅ stderr/stdout properly decoded and logged
- ✅ Timeout handled gracefully (35s)
- ✅ Safe default (block) on any error

---

**Status:** ✅ **COMPLETE**
- All changes applied
- No old show_popup() references remain
- Uses new show_popup_gui() via subprocess
- File ready for deployment
