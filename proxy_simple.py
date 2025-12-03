"""
PhishGuard Proxy - mitmproxy addon for suspicious URL detection
Intercepts HTTP/HTTPS traffic and checks domains against a suspicious list.
Uses subprocess to call popup_simple.py for user decision.
Includes comprehensive error logging to proxy_errors.log.
"""
import os
import sys
import subprocess
import traceback
from mitmproxy import http, ctx


class Addon:
    """mitmproxy addon for phishing detection - properly named for mitmproxy recognition"""
    
    def __init__(self):
        """Initialize addon and load suspicious domains list"""
        self.suspicious_domains = set()
        self.script_dir = os.path.dirname(__file__)
        self.error_log_file = os.path.join(self.script_dir, "proxy_errors.log")
        
        # Clear old log on startup
        try:
            if os.path.exists(self.error_log_file):
                open(self.error_log_file, 'w').close()
        except:
            pass
        
        self.log_error("[PhishGuard] Addon initialized")
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
            # Use os.path for absolute path resolution (exactly as specified)
            suspicious_file = os.path.join(os.path.dirname(__file__), "suspicious_urls.txt")
            
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
                ctx.log.info(f"[PhishGuard]  Loaded {len(self.suspicious_domains)} domains")
            else:
                msg = f"[Loading] ERROR: Suspicious list not found at {suspicious_file}"
                self.log_error(msg)
                ctx.log.warn(f"[PhishGuard]  Suspicious list NOT FOUND at {suspicious_file}")
        except Exception as e:
            msg = f"[Loading] ERROR: {e}\n{traceback.format_exc()}"
            self.log_error(msg)
            ctx.log.error(f"[PhishGuard]  Error loading suspicious list: {e}")
    
    def get_blocked_page_html(self, domain: str) -> str:
        """
        Load blocked_page.html and replace {domain} placeholder.
        Returns custom HTML block page or fallback HTML if file not found.
        """
        try:
            blocked_page_path = os.path.join(self.script_dir, "blocked_page.html")
            
            if os.path.exists(blocked_page_path):
                with open(blocked_page_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                # Replace domain placeholder
                html_content = html_content.replace("{domain}", domain)
                self.log_error(f"[BlockPage] Loaded custom blocked page for: {domain}")
                return html_content
            else:
                self.log_error(f"[BlockPage] blocked_page.html not found, using fallback")
                # Fallback inline HTML (ASCII-only)
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
    
    def is_suspicious(self, domain):
        """Check if a domain is in the suspicious list"""
        if not domain:
            return False
        domain_lower = domain.lower()
        return domain_lower in self.suspicious_domains
    
    def request(self, flow: http.HTTPFlow) -> None:
        """
        Intercept each HTTP/HTTPS request.
        Extract domain and check against suspicious list.
        Call popup_simple.py as subprocess to get user decision.
        Full try/except wrapper to catch ALL errors.
        """
        try:
            # Extract domain from request
            domain = flow.request.pretty_host
            
            if not domain:
                return
            
            # Log request (for debugging)
            self.log_error(f"[Request] Processing: {domain}")
            
            # Check if domain is suspicious
            if self.is_suspicious(domain):
                self.log_error(f"[Detection] SUSPICIOUS domain detected: {domain}")
                ctx.log.warn(f"[PhishGuard]  Suspicious domain: {domain}")
                
                # Call popup and get user decision
                try:
                    result = self.show_popup_subprocess(domain)
                    self.log_error(f"[Popup] Result for {domain}: {result}")
                    
                    if result == "BLOCK":
                        self.log_error(f"[Decision] User BLOCKED: {domain}")
                        ctx.log.warn(f"[PhishGuard]  BLOCKED: {domain}")
                        # Block the request with custom HTML page
                        html_content = self.get_blocked_page_html(domain)
                        flow.response = http.Response.make(
                            403,
                            html_content.encode('utf-8'),
                            {"Content-Type": "text/html; charset=utf-8"}
                        )
                    elif result == "ALLOW":
                        self.log_error(f"[Decision] User ALLOWED: {domain}")
                        ctx.log.info(f"[PhishGuard]  ALLOWED: {domain}")
                        # Allow request to proceed
                        pass
                    else:
                        # Timeout or error - default to BLOCK (safer) with custom page
                        self.log_error(f"[Decision] Invalid result '{result}', blocking by default: {domain}")
                        ctx.log.warn(f"[PhishGuard] Invalid popup result, blocking: {domain}")
                        html_content = self.get_blocked_page_html(domain)
                        flow.response = http.Response.make(
                            403,
                            html_content.encode('utf-8'),
                            {"Content-Type": "text/html; charset=utf-8"}
                        )
                
                except Exception as popup_error:
                    self.log_error(f"[Popup Error] Failed to call popup for {domain}: {popup_error}\n{traceback.format_exc()}")
                    ctx.log.error(f"[PhishGuard] Popup error: {popup_error}")
                    # Default to block on error with custom page
                    html_content = self.get_blocked_page_html(domain)
                    flow.response = http.Response.make(
                        403,
                        html_content.encode('utf-8'),
                        {"Content-Type": "text/html; charset=utf-8"}
                    )
        
        except Exception as e:
            self.log_error(f"[Critical Error] request() handler failed: {e}\n{traceback.format_exc()}")
            ctx.log.error(f"[PhishGuard] CRITICAL: {e}")
    
    def show_popup_subprocess(self, domain: str) -> str:
        """
        Call popup_simple.py as subprocess.
        Returns: "ALLOW", "BLOCK", or "TIMEOUT"
        """
        try:
            # Build absolute path to popup script
            popup_path = os.path.join(self.script_dir, "popup_simple.py")
            
            self.log_error(f"[Popup] Calling: {popup_path} with domain: {domain}")
            ctx.log.info(f"[PhishGuard] Calling popup: {domain}")
            
            if not os.path.exists(popup_path):
                self.log_error(f"[Popup Error] popup_simple.py not found at: {popup_path}")
                ctx.log.error(f"[PhishGuard] popup_simple.py not found")
                return "TIMEOUT"
            
            # Call popup_simple.py with domain as argument
            # Wait for stdout result
            proc = subprocess.Popen(
                [sys.executable, popup_path, domain],
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

