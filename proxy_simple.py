"""
PhishGuard Proxy - OPTIMIZED mitmproxy addon for suspicious URL detection
Performance improvements:
  1. Whitelist of trusted domains (fast-path bypass)
  2. Domain normalization for fast checks
  3. Non-blocking HTTPS inspection (SNI only, no decryption)
  4. Efficient domain matching with Python sets
  5. Comprehensive error handling with try/except
  6. Absolute paths for all file references
Uses subprocess to call popup_simple.py for user decision.
"""
import os
import sys
import subprocess
import traceback
import json
import urllib.request
import urllib.error
from mitmproxy import http, ctx
import requests
import json


# Import popup_simple.show_popup (will be implemented in popup_simple.py)
try:
    import popup_simple
except Exception:
    popup_simple = None


# WHITELIST: Trusted domains that bypass all checks (HIGH PERFORMANCE)
SAFE_DOMAINS = {
    'google.com',
    'gstatic.com',
    'googleapis.com',
    'youtube.com',
    'ytimg.com',
    'amazon.com',
    'amazon.in',
    'ssl-images-amazon.com',
    'cloudfront.net',
    'microsoft.com',
    'windows.com',
    'github.com',
    'facebook.com',
    'whatsapp.com',
    'instagram.com',
    'reddit.com'
}


class Addon:
    """mitmproxy addon for phishing detection - optimized performance"""
    
    def __init__(self):
        """Initialize addon and load suspicious domains list"""
        self.suspicious_domains = set()
        self.script_dir = os.path.dirname(__file__)
        self.error_log_file = os.path.join(self.script_dir, "proxy_errors.log")
        
        # Absolute paths for critical files
        self.popup_path = os.path.join(self.script_dir, "popup_simple.py")
        self.blocked_page_path = os.path.join(self.script_dir, "blocked_page.html")
        
        # Clear old log on startup
        try:
            if os.path.exists(self.error_log_file):
                open(self.error_log_file, 'w').close()
        except:
            pass
        
        self.log_error("[PhishGuard] Addon initialized - OPTIMIZED MODE")
        self.load_suspicious_list()
    
    def log_error(self, message):
        """Log error messages to proxy_errors.log"""
        try:
            with open(self.error_log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except Exception as e:
            ctx.log.error(f"[PhishGuard] Could not write to error log: {e}")
    
    def load_suspicious_list(self):
        """Load suspicious domains from suspicious_urls.txt using os.path"""
        try:
            suspicious_file = os.path.join(self.script_dir, "suspicious_urls.txt")
            
            self.log_error(f"[Loading] Script directory: {self.script_dir}")
            self.log_error(f"[Loading] Suspicious list file: {suspicious_file}")
            ctx.log.info(f"[PhishGuard] Loading suspicious domains from: {suspicious_file}")
            
            if os.path.exists(suspicious_file):
                with open(suspicious_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        domain = line.strip().lower()
                        if domain and not domain.startswith('#'):
                            self.suspicious_domains.add(domain)
                
                msg = f"[Loading] SUCCESS: Loaded {len(self.suspicious_domains)} suspicious domains"
                self.log_error(msg)
                ctx.log.info(f"[PhishGuard] Loaded {len(self.suspicious_domains)} domains")
            else:
                msg = f"[Loading] ERROR: Suspicious list not found at {suspicious_file}"
                self.log_error(msg)
                ctx.log.warn(f"[PhishGuard] Suspicious list NOT FOUND at {suspicious_file}")
        except Exception as e:
            msg = f"[Loading] ERROR: {e}\n{traceback.format_exc()}"
            self.log_error(msg)
            ctx.log.error(f"[PhishGuard] Error loading suspicious list: {e}")
    
    def normalize_domain(self, domain: str) -> str:
        """
        Normalize domain: lowercase, strip www prefix.
        OPTIMIZATION: Fast path for domain checking.
        """
        if not domain:
            return ""
        domain = domain.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    
    def is_safe_domain(self, domain: str) -> bool:
        """
        FAST-PATH CHECK: Return True if domain is in whitelist.
        Subdomains of safe domains are also allowed.
        Example: mail.google.com ends with google.com -> SAFE
        """
        if not domain:
            return False
        
        normalized = self.normalize_domain(domain)
        
        # Check exact match
        if normalized in SAFE_DOMAINS:
            return True
        
        # Check if domain ends with any safe domain (subdomain check)
        for safe in SAFE_DOMAINS:
            if normalized == safe or normalized.endswith('.' + safe):
                return True
        
        return False
    
    def is_suspicious_domain(self, domain: str) -> bool:
        """
        Check if domain is in suspicious list.
        Subdomains of suspicious domains are NOT treated as suspicious.
        Only exact match or after www. stripping.
        """
        if not domain:
            return False
        
        normalized = self.normalize_domain(domain)
        return normalized in self.suspicious_domains
    
    def get_blocked_page_html(self, domain: str) -> str:
        """
        Load blocked_page.html and replace {domain} placeholder.
        Returns custom HTML block page or fallback HTML if file not found.
        Uses cached absolute path (self.blocked_page_path).
        """
        try:
            if os.path.exists(self.blocked_page_path):
                with open(self.blocked_page_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                # Replace domain placeholder
                html_content = html_content.replace("{domain}", domain)
                self.log_error(f"[BlockPage] Loaded custom blocked page for: {domain}")
                return html_content
            else:
                self.log_error(f"[BlockPage] blocked_page.html not found at {self.blocked_page_path}, using fallback")
                return self.get_fallback_blocked_html(domain)
        except Exception as e:
            self.log_error(f"[BlockPage] Error loading blocked page: {e}")
            return self.get_fallback_blocked_html(domain)
    
    def get_fallback_blocked_html(self, domain: str) -> str:
        """
        Return fallback HTML block page (ASCII-only, no external dependencies).
        """
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Blocked by PhishGuard</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #1a1a1a; margin: 0; padding: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }}
        .container {{ background: #fff; border-radius: 8px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); max-width: 600px; width: 100%; }}
        .header {{ background: #d32f2f; color: #fff; padding: 40px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .content {{ padding: 40px; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px; }}
        .domain-box {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .domain-label {{ color: #666; font-size: 12px; text-transform: uppercase; margin-bottom: 8px; }}
        .domain-name {{ color: #d32f2f; font-size: 18px; font-weight: bold; font-family: monospace; word-break: break-all; }}
        .reasons {{ margin-bottom: 20px; }}
        .reasons h3 {{ color: #333; margin-bottom: 10px; text-transform: uppercase; font-size: 14px; }}
        .reasons ul {{ list-style: none; padding: 0; }}
        .reasons li {{ color: #555; padding: 8px 0; padding-left: 24px; position: relative; }}
        .reasons li:before {{ content: "[!]"; position: absolute; left: 0; color: #d32f2f; font-weight: bold; }}
        .footer {{ background: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0; color: #888; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Website Blocked by PhishGuard</h1>
            <p>Access to this website has been denied for your security</p>
        </div>
        <div class="content">
            <div class="warning">
                <p>PhishGuard has blocked this website because it appears to be suspicious and potentially dangerous.</p>
            </div>
            <div class="domain-box">
                <div class="domain-label">Detected Domain</div>
                <div class="domain-name">{domain}</div>
            </div>
            <div class="reasons">
                <h3>Why was this blocked?</h3>
                <ul>
                    <li>Domain matches known phishing or malicious website patterns</li>
                    <li>Suspicious characteristics detected in website behavior</li>
                    <li>PhishGuard security policies identified potential threats</li>
                </ul>
            </div>
            <div class="reasons">
                <h3>What should you do?</h3>
                <ul>
                    <li>Do not proceed to this website if unsure of its legitimacy</li>
                    <li>If this website should be trusted, contact your administrator</li>
                    <li>Report suspicious sites to security@phishguard.local</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            <p><strong>PhishGuard</strong> - Enterprise Security Protection</p>
            <p>This is a security block page. If you believe this is an error, please contact your network administrator.</p>
        </div>
    </div>
</body>
</html>"""
    
    def request(self, flow: http.HTTPFlow) -> None:
        """
        OPTIMIZED request interceptor with fast-path checking.
        
        Flow:
          1. Extract domain (SNI for HTTPS, pretty_host for HTTP)
          2. Check WHITELIST first (safe domains bypass all checks)
          3. Check SUSPICIOUS list (domain normalization for fast lookup)
          4. If suspicious: Call popup subprocess, get user decision
          5. If BLOCK: Return custom HTML block page
          6. If ALLOW or not suspicious: Allow request to pass through
        
        Full try/except wrapper to catch ALL errors.
        Non-blocking: Request passes immediately unless BLOCK response set.
        """
        try:
            # Extract domain from request (works for both HTTP and HTTPS via SNI)
            domain = flow.request.pretty_host
            
            if not domain:
                return
            
            # OPTIMIZATION 1: WHITELIST FAST-PATH
            # If domain is in whitelist (google.com, amazon.com, etc),
            # bypass ALL checks and allow immediately
            if self.is_safe_domain(domain):
                self.log_error(f"[FastPath] SAFE domain (whitelist), allowing: {domain}")
                return  # Allow request - no popup, no inspection needed
            
            # OPTIMIZATION 2: Use ML analyzer for real-time scoring
            try:
                # Build full URL from flow
                try:
                    full_url = flow.request.pretty_url
                except Exception:
                    full_url = None

                analyzer_hit = False
                score = None
                reasons = []

                if full_url:
                    analyzer_url = "http://127.0.0.1:8000/score"
                    payload = json.dumps({"url": full_url}).encode('utf-8')
                    req = urllib.request.Request(analyzer_url, data=payload, headers={"Content-Type": "application/json"}, method='POST')
                    try:
                        with urllib.request.urlopen(req, timeout=0.8) as resp:
                            body = resp.read()
                            try:
                                resp_json = json.loads(body.decode('utf-8', errors='ignore'))
                                score = float(resp_json.get('score', 0.0))
                                reasons = resp_json.get('reasons', []) or []
                                analyzer_hit = True
                                self.log_error(f"[Analyzer] Score for {full_url}: {score}")
                            except Exception as e:
                                self.log_error(f"[Analyzer] Invalid JSON response: {e}")
                    except Exception as e:
                        # Analyzer unreachable or timed out - fallback to rule-based detection
                        self.log_error(f"[Analyzer] Unreachable or timeout: {e}")

                # Decision logic: if analyzer indicates high risk, show popup
                show_popup_decision = None
                if analyzer_hit and score is not None:
                    if score >= 0.75:
                        # Ensure popup API exists
                        try:
                            if popup_simple and hasattr(popup_simple, 'show_popup'):
                                res = popup_simple.show_popup(full_url, score, reasons)
                                show_popup_decision = str(res).lower()
                            else:
                                # Fallback: use subprocess popup for compatibility
                                show_popup_decision = self.show_popup_subprocess(domain).lower()
                        except Exception as e:
                            self.log_error(f"[Popup Error] Exception when calling show_popup: {e}")
                            show_popup_decision = 'block'
                    else:
                        # Low/medium risk -> allow
                        show_popup_decision = 'allow'
                else:
                    # Analyzer not available: fallback to rule-based (suspicious list)
                    if self.is_suspicious_domain(domain):
                        try:
                            if popup_simple and hasattr(popup_simple, 'show_popup'):
                                res = popup_simple.show_popup(full_url or domain, None, ["Matched suspicious list"]) 
                                show_popup_decision = str(res).lower()
                            else:
                                show_popup_decision = self.show_popup_subprocess(domain).lower()
                        except Exception as e:
                            self.log_error(f"[Popup Error] Exception when calling fallback popup: {e}")
                            show_popup_decision = 'block'
                    else:
                        show_popup_decision = 'allow'

                # Apply decision
                if show_popup_decision == 'block' or show_popup_decision == 'BLOCK':
                    html_content = self.get_blocked_page_html(domain)
                    flow.response = http.Response.make(
                        403,
                        html_content.encode('utf-8'),
                        {"Content-Type": "text/html; charset=utf-8"}
                    )
                else:
                    # allow - do nothing
                    pass

            except Exception as e:
                self.log_error(f"[Critical] ML decision path failed: {e}\n{traceback.format_exc()}")
                # Safe default: block
                html_content = self.get_blocked_page_html(domain)
                flow.response = http.Response.make(
                    403,
                    html_content.encode('utf-8'),
                    {"Content-Type": "text/html; charset=utf-8"}
                )
            else:
                # Domain is not suspicious, allow it to pass through
                self.log_error(f"[AllowPass] Domain not suspicious: {domain}")
        
        except Exception as e:
            self.log_error(f"[Critical Error] request() handler failed: {e}\n{traceback.format_exc()}")
            ctx.log.error(f"[PhishGuard] CRITICAL: {e}")
    
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
            
            # Wait for process to complete (with timeout)
            try:
                stdout, stderr = proc.communicate(timeout=35)
                result = stdout.decode('utf-8', errors='ignore').strip().upper()
                
                if stderr:
                    self.log_error(f"[Popup] stderr: {stderr.decode('utf-8', errors='ignore')}")
                
                self.log_error(f"[Popup] stdout result: '{result}'")
                
                if result in ["ALLOW", "BLOCK"]:
                    return result
                else:
                    self.log_error(f"[Popup] Invalid result: '{result}'")
                    return "TIMEOUT"
            
            except subprocess.TimeoutExpired:
                self.log_error(f"[Popup] Timeout waiting for popup process")
                proc.kill()
                return "TIMEOUT"
        
        except Exception as e:
            self.log_error(f"[Popup Error] Exception: {e}\n{traceback.format_exc()}")
            ctx.log.error(f"[PhishGuard] Popup exception: {e}")
            return "TIMEOUT"


# Register addon with mitmproxy
# mitmproxy automatically loads addons from this list
addons = [Addon()]

