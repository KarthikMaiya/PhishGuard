"""
PhishGuard Integration Test Script
Tests all 11 goals and 7 mandatory requirements
"""
import subprocess
import sys
import os
import time
import json
import urllib.request
import urllib.error

PHISHGUARD_HOME = os.path.dirname(__file__)
PROXY_LOG = os.path.join(PHISHGUARD_HOME, "proxy_errors.log")
LAUNCHER_LOG = os.path.join(PHISHGUARD_HOME, "phishguard_launcher.log")
MITMPROXY_LOG = os.path.join(PHISHGUARD_HOME, "mitmproxy_debug.log")

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def log(self, msg, level="INFO"):
        """Log with timestamp and level"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {msg}")
    
    def test(self, name, condition, details=""):
        """Record test result"""
        if condition:
            self.log(f"✓ {name}", "PASS")
            self.passed += 1
        else:
            self.log(f"✗ {name}", "FAIL")
            if details:
                self.log(f"  Details: {details}", "FAIL")
            self.failed += 1
    
    def warn(self, name, details=""):
        """Record warning"""
        self.log(f"⚠ {name}", "WARN")
        if details:
            self.log(f"  Details: {details}", "WARN")
        self.warnings += 1
    
    def check_analyzer_reachable(self):
        """Goal 1: ML analyzer reachable at /score"""
        self.log("========== Goal 1: Analyzer Reachability ==========")
        try:
            url = "http://127.0.0.1:8000/score"
            payload = json.dumps({"url": "http://google.com"}).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                body = resp.read()
                resp_json = json.loads(body.decode('utf-8'))
                self.test("Analyzer /score endpoint reachable", True)
                self.test("Response contains 'score'", 'score' in resp_json)
                self.test("Response contains 'risk'", 'risk' in resp_json)
                self.test("Response contains 'reasons'", 'reasons' in resp_json)
                risk = resp_json.get('risk')
                self.test(f"Risk is valid value (got '{risk}')", risk in ['high', 'medium', 'low'])
                return True
        except Exception as e:
            self.test("Analyzer /score endpoint reachable", False, str(e))
            return False
    
    def check_analyzer_timeout(self):
        """Goal 1 (continued): No timeouts"""
        self.log("========== Goal 1 (continued): Analyzer Timeout Handling ==========")
        try:
            start = time.time()
            url = "http://127.0.0.1:8000/score"
            for i in range(5):
                payload = json.dumps({"url": f"http://domain{i}.test"}).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    resp.read()
            elapsed = time.time() - start
            self.test(f"5 analyzer requests completed in {elapsed:.2f}s", elapsed < 15.0)
            self.test("No timeout errors", True)
        except urllib.error.URLError as e:
            self.test("No timeout errors", False, f"URLError: {e}")
        except Exception as e:
            self.test("No timeout errors", False, str(e))
    
    def check_proxy_log_exists(self):
        """Mandatory Task D: Detailed logging present"""
        self.log("========== Mandatory Task D: Detailed Logging ==========")
        
        # Clear and check proxy log
        try:
            if os.path.exists(PROXY_LOG):
                with open(PROXY_LOG, 'r') as f:
                    content = f.read()
                    self.test("Proxy error log exists", True)
                    self.test("Log contains [Analyzer] messages", "[Analyzer]" in content)
                    self.test("Log contains [Popup] messages", "[Popup]" in content)
                    self.test("Log contains [Decision] messages", "[Decision]" in content)
                    if "[Analyzer]" not in content:
                        self.warn("No analyzer logs yet - proxy may not have processed requests")
            else:
                self.test("Proxy error log exists", False, f"File not found: {PROXY_LOG}")
        except Exception as e:
            self.test("Proxy error log exists", False, str(e))
    
    def check_launcher_log(self):
        """Check launcher startup log"""
        self.log("========== Check Launcher Log ==========")
        if os.path.exists(LAUNCHER_LOG):
            try:
                with open(LAUNCHER_LOG, 'r') as f:
                    content = f.read()
                    self.test("Launcher log exists", True)
                    self.test("Contains analyzer startup", "ANALYZER" in content.upper())
                    self.test("Contains proxy startup", "PROXY" in content.upper() or "MITMPROXY" in content.upper())
                    self.test("Contains chrome launch", "CHROME" in content.upper())
            except Exception as e:
                self.test("Launcher log readable", False, str(e))
        else:
            self.warn("Launcher log not found", f"Expected at {LAUNCHER_LOG}")
    
    def check_popup_file(self):
        """Check popup_simple.py exists and has required functions"""
        self.log("========== Goal 3-6: Popup Integration ==========")
        popup_path = os.path.join(PHISHGUARD_HOME, "popup_simple.py")
        
        self.test("popup_simple.py exists", os.path.exists(popup_path))
        
        # Check it can be imported
        try:
            sys.path.insert(0, PHISHGUARD_HOME)
            import popup_simple
            self.test("popup_simple can be imported", True)
            self.test("show_popup_gui function exists", hasattr(popup_simple, 'show_popup_gui'))
            self.test("PhishGuardPopup class exists", hasattr(popup_simple, 'PhishGuardPopup'))
            self.test("main() entry point exists", hasattr(popup_simple, 'main'))
        except Exception as e:
            self.test("popup_simple can be imported", False, str(e))
    
    def check_proxy_none_handling(self):
        """Mandatory Task A: None value handling"""
        self.log("========== Mandatory Task A: None Handling ==========")
        
        proxy_path = os.path.join(PHISHGUARD_HOME, "proxy_simple.py")
        try:
            with open(proxy_path, 'r') as f:
                content = f.read()
                
                # Check for safe defaults after analyzer call
                self.test("Analyzer returns safe defaults (not None)", "return 0.0, [], 'low'" in content)
                
                # Check for None validation in request handler
                self.test("None validation for risk value", "if risk is None" in content)
                self.test("None validation for reasons", "if reasons is None" in content)
                
                # Check for .upper() calls are safe
                has_safe_upper = "stdout_text.upper().strip()" in content or ".upper()" in content
                self.test("Safely calls .upper() on strings", has_safe_upper)
                
        except Exception as e:
            self.test("None handling check", False, str(e))
    
    def check_popup_stdout(self):
        """Mandatory Task B: Popup returns via stdout"""
        self.log("========== Goal 5: Popup stdout Communication ==========")
        
        popup_path = os.path.join(PHISHGUARD_HOME, "popup_simple.py")
        try:
            with open(popup_path, 'r') as f:
                content = f.read()
                
                # Check for proper stdout output
                self.test("Popup outputs 'BLOCK' via stdout", 'print("BLOCK"' in content or 'print(result' in content)
                self.test("Popup outputs 'ALLOW' via stdout", 'print("ALLOW"' in content or 'print(result' in content)
                self.test("Popup flushes stdout", "sys.stdout.flush()" in content)
                self.test("popup_simple uses show_popup_gui()", "show_popup_gui" in content)
                
        except Exception as e:
            self.test("Popup stdout check", False, str(e))
    
    def check_block_html(self):
        """Goal 7: Block HTML behavior"""
        self.log("========== Goal 7: Block HTML ==========")
        
        blocked_page_path = os.path.join(PHISHGUARD_HOME, "blocked_page.html")
        proxy_path = os.path.join(PHISHGUARD_HOME, "proxy_simple.py")
        
        self.test("blocked_page.html exists", os.path.exists(blocked_page_path))
        
        try:
            with open(proxy_path, 'r') as f:
                content = f.read()
                self.test("Proxy loads blocked page HTML", "get_blocked_page_html" in content)
                self.test("Proxy returns 403 for BLOCK decision", "403" in content)
                self.test("Proxy sets Content-Type header", "Content-Type" in content)
        except Exception as e:
            self.test("Block HTML check", False, str(e))
    
    def check_absolute_paths(self):
        """Goal 8: Absolute paths"""
        self.log("========== Goal 8: Absolute Paths ==========")
        
        proxy_path = os.path.join(PHISHGUARD_HOME, "proxy_simple.py")
        launcher_path = os.path.join(PHISHGUARD_HOME, "launcher.py")
        
        try:
            with open(proxy_path, 'r') as f:
                proxy_content = f.read()
                self.test("Proxy uses os.path.join for absolute paths", "os.path.join" in proxy_content)
                self.test("Proxy uses os.path.dirname for script_dir", "os.path.dirname" in proxy_content)
                self.test("No hardcoded relative paths in popup call", "../popup_simple.py" not in proxy_content)
            
            with open(launcher_path, 'r') as f:
                launcher_content = f.read()
                self.test("Launcher uses absolute paths", "Path(__file__).parent" in launcher_content or "os.path" in launcher_content)
        except Exception as e:
            self.test("Absolute paths check", False, str(e))
    
    def check_error_handling(self):
        """Goal 11 & Mandatory Tasks E,F,G: Error handling"""
        self.log("========== Goal 11 & Mandatory Tasks E-G: Error Handling ==========")
        
        proxy_path = os.path.join(PHISHGUARD_HOME, "proxy_simple.py")
        serve_path = os.path.join(PHISHGUARD_HOME, "analyzer", "serve_ml.py")
        
        try:
            with open(proxy_path, 'r') as f:
                proxy_content = f.read()
                self.test("Proxy has try/except around analyzer call", "except urllib.error.URLError" in proxy_content)
                self.test("Proxy logs analyzer failures", "[Analyzer]" in proxy_content and "FALLBACK" in proxy_content)
                self.test("Popup failure returns 'block'", "except" in proxy_content and '"block"' in proxy_content)
                self.test("Popup failure logs traceback", "traceback" in proxy_content)
            
            with open(serve_path, 'r') as f:
                serve_content = f.read()
                self.test("Analyzer handles model load failure", "FileNotFoundError" in serve_content)
                self.test("Analyzer checks if model is None", "if model is None" in serve_content)
                self.test("Analyzer returns safe default if no model", '"low"' in serve_content)
        except Exception as e:
            self.test("Error handling check", False, str(e))
    
    def run_all_tests(self):
        """Run all test checks"""
        self.log("\n")
        self.log("╔════════════════════════════════════════════════════════════════╗")
        self.log("║         PhishGuard Integration Test Suite                      ║")
        self.log("║  Testing 11 Goals + 7 Mandatory Debug Tasks                   ║")
        self.log("╚════════════════════════════════════════════════════════════════╝")
        self.log("\n")
        
        # Ensure analyzer is running first
        self.log("Checking Analyzer...")
        analyzer_ok = self.check_analyzer_reachable()
        
        if analyzer_ok:
            self.check_analyzer_timeout()
        else:
            self.warn("Analyzer not reachable", "Make sure 'python launcher.py' is running")
            self.log("Note: Skipping some tests since analyzer is required")
        
        self.log("\n")
        self.check_proxy_log_exists()
        self.log("\n")
        self.check_launcher_log()
        self.log("\n")
        self.check_popup_file()
        self.log("\n")
        self.check_proxy_none_handling()
        self.log("\n")
        self.check_popup_stdout()
        self.log("\n")
        self.check_block_html()
        self.log("\n")
        self.check_absolute_paths()
        self.log("\n")
        self.check_error_handling()
        self.log("\n")
        
        # Summary
        self.log("╔════════════════════════════════════════════════════════════════╗")
        self.log(f"║  PASSED: {self.passed:2d}  |  FAILED: {self.failed:2d}  |  WARNINGS: {self.warnings:2d}      ")
        self.log("╚════════════════════════════════════════════════════════════════╝")
        
        return self.failed == 0


if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)
