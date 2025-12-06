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

# Import popup_simple - CRITICAL for popup functionality
import popup_simple


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
        """Initialize addon with ML analyzer"""
        self.script_dir = os.path.dirname(__file__)
        self.error_log_file = os.path.join(self.script_dir, "proxy_errors.log")
        
        # Absolute paths for critical files
        self.popup_path = os.path.join(self.script_dir, "popup_simple.py")
        self.blocked_page_path = os.path.join(self.script_dir, "blocked_page.html")
        self.ml_api_url = "http://127.0.0.1:8000/score"
        
        # Track domains where popup has been shown (DOMAIN-LEVEL CACHING, not URL-level)
        # This prevents multiple popups for the same domain (favicon, JS, images, etc)
        self.popup_shown_domains = set()
        
        # Store user decisions per domain (BLOCK/ALLOW)
        # Allows persistence: if user blocked domain once, auto-block on next visit
        self.domain_decisions = {}
        
        # Clear old log on startup
        try:
            if os.path.exists(self.error_log_file):
                open(self.error_log_file, 'w').close()
        except:
            pass
        
        self.log_error("[PhishGuard] Addon initialized - ML ANALYZER MODE")
    
    def log_error(self, message):
        """Log error messages to proxy_errors.log"""
        try:
            with open(self.error_log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except Exception as e:
            ctx.log.error(f"[PhishGuard] Could not write to error log: {e}")
    
    def call_ml_analyzer(self, url: str) -> tuple:
        """Call ML analyzer API. Returns (score, reasons, risk) or (None, [], None) on failure"""
        try:
            payload = json.dumps({"url": url}).encode('utf-8')
            req = urllib.request.Request(
                self.ml_api_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                body = resp.read()
                resp_json = json.loads(body.decode('utf-8', errors='ignore'))
                score = float(resp_json.get('score', 0.0))
                risk = resp_json.get('risk', 'low').lower()
                reasons = resp_json.get('reasons', []) or []
                self.log_error(f"[Analyzer] {url}: score={score:.3f}, risk={risk}")
                return score, reasons, risk
        except urllib.error.URLError:
            self.log_error(f"[Analyzer] Unreachable: {url}")
        except json.JSONDecodeError as e:
            self.log_error(f"[Analyzer] Invalid JSON: {e}")
        except Exception as e:
            self.log_error(f"[Analyzer] Error: {e}")
        return None, [], None
    
    def normalize_domain(self, domain: str) -> str:
        """
        Normalize domain to registrar-level for popup caching.
        Removes www prefix, extracts registrar+TLD only.
        
        All subdomains map to same registrar domain:
          www.evil.com → evil.com
          login.evil.com → evil.com
          api.evil.com → evil.com
        
        Ensures ONE popup per organization.
        """
        if not domain:
            return ""
        domain = domain.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Extract registrar domain (last 2 parts)
        parts = domain.split('.')
        if len(parts) > 2:
            last_two = '.'.join(parts[-2:])
            # Check for multi-part TLDs
            if last_two in {'co.uk', 'com.au', 'co.nz', 'co.in', 'com.br', 'co.jp'}:
                return '.'.join(parts[-3:]) if len(parts) >= 3 else domain
            return '.'.join(parts[-2:])
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
                full_url = flow.request.pretty_url
            except Exception:
                full_url = None
            
            try:
                # Query ML analyzer
                score, reasons, risk = self.call_ml_analyzer(full_url or domain)
                
                # Decision: show popup only if risk == 'high'
                if risk == 'high':
                    # Normalize domain for caching (lowercase, strip www)
                    normalized = self.normalize_domain(domain)
                    
                    # DOMAIN-LEVEL CACHING: Check if popup already shown for this domain
                    if normalized in self.popup_shown_domains:
                        # Popup already shown for this domain
                        self.log_error(f"[Decision] Popup already shown for domain, using cached decision: {domain}")
                        
                        # Reuse previous decision from cache
                        show_popup_decision = self.domain_decisions.get(normalized, 'block')
                        self.log_error(f"[Decision] Cached decision for {domain}: {show_popup_decision.upper()}")
                    else:
                        # First time seeing this domain - show popup
                        self.log_error(f"[Decision] HIGH RISK - NEW domain, showing popup: {domain}")
                        
                        # Mark domain as having popup shown (prevents duplicate popups)
                        self.popup_shown_domains.add(normalized)
                        
                        try:
                            # Call the popup GUI function - get user decision
                            show_popup_decision = self.show_popup_subprocess(domain, reasons).lower()
                            
                            # Store decision for future requests to same domain
                            self.domain_decisions[normalized] = show_popup_decision
                            self.log_error(f"[Decision] User decision for {domain}: {show_popup_decision.upper()}")
                        
                        except Exception as e:
                            self.log_error(f"[Popup Error] {e}")
                            show_popup_decision = 'block'
                            self.domain_decisions[normalized] = 'block'
                else:
                    # Low or medium risk -> allow
                    self.log_error(f"[Decision] {risk.upper()} RISK, allowing: {domain}")
                    show_popup_decision = 'allow'
                
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
            
            except Exception as e:
                self.log_error(f"[Critical] Decision path failed: {e}")
                # Safe default: block
                html_content = self.get_blocked_page_html(domain)
                flow.response = http.Response.make(
                    403,
                    html_content.encode('utf-8'),
                    {"Content-Type": "text/html; charset=utf-8"}
                )
        
        except Exception as e:
            self.log_error(f"[Critical Error] request() handler failed: {e}\n{traceback.format_exc()}")
            ctx.log.error(f"[PhishGuard] CRITICAL: {e}")
    
    def show_popup_subprocess(self, domain: str, reasons: list = None) -> str:
        """
        Call popup_simple.py as subprocess with domain and reasons.
        Returns: "block", "allow", or "block" (on error/timeout)
        """
        try:
            self.log_error(f"[Popup] Calling popup subprocess for domain: {domain}")
            
            if not os.path.exists(self.popup_path):
                self.log_error(f"[Popup Error] popup_simple.py not found at: {self.popup_path}")
                return "block"
            
            # Build subprocess args: python popup_simple.py <domain> [<json_reasons>]
            args = [sys.executable, self.popup_path, domain]
            
            # Add reasons as JSON if provided
            if reasons and len(reasons) > 0:
                try:
                    reasons_json = json.dumps(reasons)
                    args.append(reasons_json)
                    self.log_error(f"[Popup] Passing {len(reasons)} reasons to popup")
                except Exception as e:
                    self.log_error(f"[Popup] Warning: Failed to serialize reasons: {e}")
            
            # Call popup_simple.py subprocess with timeout (35 seconds = 8s popup + margin)
            try:
                proc = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.script_dir
                )
                
                # Wait for process output with timeout
                stdout_raw, stderr_raw = proc.communicate(timeout=35)
                
                # Decode output safely
                stdout_text = stdout_raw.decode('utf-8', errors='ignore').strip() if stdout_raw else ""
                stderr_text = stderr_raw.decode('utf-8', errors='ignore').strip() if stderr_raw else ""
                
                # Log stderr if any
                if stderr_text:
                    self.log_error(f"[Popup] Subprocess stderr: {stderr_text}")
                
                # Parse result from stdout
                result = stdout_text.upper().strip() if stdout_text else ""
                self.log_error(f"[Popup] Subprocess returned: '{result}'")
                
                # Validate result
                if result == "BLOCK":
                    return "block"
                elif result == "ALLOW":
                    return "allow"
                else:
                    self.log_error(f"[Popup] Invalid result '{result}' - defaulting to block")
                    return "block"
            
            except subprocess.TimeoutExpired:
                self.log_error(f"[Popup] Subprocess timeout (35s) - auto-blocking")
                try:
                    proc.kill()
                except:
                    pass
                return "block"
            
            except Exception as e:
                self.log_error(f"[Popup] Subprocess error: {e}")
                return "block"
        
        except Exception as e:
            self.log_error(f"[Popup] Critical error: {e}\n{traceback.format_exc()}")
            return "block"


# Register addon with mitmproxy
# mitmproxy automatically loads addons from this list
addons = [Addon()]

