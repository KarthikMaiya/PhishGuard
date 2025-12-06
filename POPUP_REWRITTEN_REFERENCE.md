# popup_simple.py - REWRITTEN (410 lines)

```python
"""
PhishGuard Popup - Enterprise-grade security alert UI
Features:
  1. Scrollable detection reasons with Canvas + Scrollbar
  2. 8-second auto-block countdown timer
  3. Pulsating red border (500ms cycle: bright #ff0000 ↔ dark #990000)
  4. Hidden window close button (forces user decision)
Runs as a standalone subprocess called from proxy_simple.py.
Returns result via stdout: "BLOCK" or "ALLOW"
"""
import tkinter as tk
import sys
import os
import json

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class PhishGuardPopup:
    """Enterprise-grade phishing alert popup with all features"""
    
    def __init__(self, domain: str, timeout_sec: int = 8, reasons: list = None):
        self.domain = domain
        self.timeout_sec = timeout_sec
        self.countdown = timeout_sec
        self.result = None
        self.details_expanded = False
        self.border_pulse_state = 0  # Toggle: 0=bright, 1=dark
        self.animation_id = None
        self.countdown_id = None
        self.reasons = reasons if reasons else []
        self.root = None
        self.root_border = None
        self.countdown_label = None
        self.details_button = None
        self.details_container = None
        self.details_frame = None
        self.details_canvas = None
        
        # Color scheme - aggressive red/black/grey
        self.colors = {
            'bg': '#ffffff',
            'fg': '#222222',
            'header_bg': '#8b0000',
            'header_text': '#ffffff',
            'border_bright': '#ff0000',
            'border_dark': '#990000',
            'button_block_bg': '#cc0000',
            'button_block_hover': '#990000',
            'button_allow_bg': '#666666',
            'button_allow_hover': '#444444',
            'button_text': '#ffffff',
            'warning_bg': '#fff0f0',
            'warning_border': '#cc0000',
            'domain_bg': '#f0f0f0',
            'domain_fg': '#cc0000',
            'separator': '#cc0000',
            'countdown_fg': '#cc0000',
            'details_bg': '#f5f5f5',
            'details_fg': '#333333'
        }
    
    def load_icon(self):
        """Load security icon if available"""
        if not PIL_AVAILABLE:
            return None
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "security_icon.png")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except Exception:
            pass
        return None
    
    def animate_border(self):
        """FEATURE 3: Pulse red border every 500ms (bright ↔ dark)"""
        if self.root and self.root.winfo_exists():
            # Toggle color state
            if self.border_pulse_state == 0:
                color = self.colors['border_bright']  # Bright red #ff0000
                self.border_pulse_state = 1
            else:
                color = self.colors['border_dark']    # Dark red #990000
                self.border_pulse_state = 0
            
            self.root_border.config(bg=color)
            
            # Schedule next pulse in 500ms (non-blocking)
            self.animation_id = self.root.after(500, self.animate_border)
    
    def update_countdown(self):
        """FEATURE 2: 8-second countdown, auto-block at 0"""
        if self.countdown > 0:
            self.countdown_label.config(text=f"Auto-block in: {self.countdown} seconds")
            self.countdown -= 1
            self.countdown_id = self.root.after(1000, self.update_countdown)
        else:
            # Auto-block on timeout
            self.result = "BLOCK"
            self.stop_all_animations()
            self.root.destroy()
    
    def stop_all_animations(self):
        """Stop both border pulse and countdown animations"""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
        if self.countdown_id:
            self.root.after_cancel(self.countdown_id)
            self.countdown_id = None
    
    def on_block(self):
        """BLOCK button clicked - close immediately"""
        self.result = "BLOCK"
        self.stop_all_animations()
        self.root.destroy()
    
    def on_allow(self):
        """ALLOW button clicked - close immediately"""
        self.result = "ALLOW"
        self.stop_all_animations()
        self.root.destroy()
    
    def toggle_details(self):
        """Toggle details section"""
        if self.details_expanded:
            self.hide_details()
        else:
            self.show_details()
    
    def show_details(self):
        """Show details with scrollbar"""
        if self.details_expanded:
            return
        self.details_expanded = True
        self.details_button.config(text="Hide Details <<")
        self.details_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15), 
                                   after=self.details_button)
    
    def hide_details(self):
        """Hide details section"""
        if not self.details_expanded:
            return
        self.details_expanded = False
        self.details_button.config(text="Show Details >>")
        self.details_container.pack_forget()
    
    def populate_details(self):
        """FEATURE 1: Populate details with scrollable reasons"""
        # Build threat assessment from actual reasons
        threat_text = "Threat Assessment:\n"
        if self.reasons and len(self.reasons) > 0:
            for reason in self.reasons:
                threat_text += f"  • {reason}\n"
        else:
            threat_text += """  • Classified as high-risk phishing/malware domain
  • Malicious domain pattern detected
  • Potential credential theft attempt
  • Suspicious redirects or exploits identified
"""
        
        full_text = f"""Domain: {self.domain}

{threat_text}
Recommended Action:
  • Block and report this domain
  • Do not enter any sensitive information
  • Contact network administrator if false positive

PhishGuard Risk Level: HIGH
Last Updated: Ongoing Monitoring"""
        
        # Create scrollable label in details_frame
        detail_label = tk.Label(
            self.details_frame,
            text=full_text,
            font=("Arial", 9),
            bg=self.colors['details_bg'],
            fg=self.colors['details_fg'],
            justify=tk.LEFT,
            wraplength=600,
            padx=10,
            pady=10
        )
        detail_label.pack(anchor=tk.W, fill=tk.X)
    
    def create_ui(self):
        """Create entire popup UI"""
        # Main window
        self.root = tk.Tk()
        self.root.title("SECURITY WARNING - PhishGuard")
        self.root.geometry("680x650")
        self.root.attributes('-topmost', True)
        
        # Prevent user from closing via window close button
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Center on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        c = self.colors
        
        # FEATURE 3: Red pulsating border frame
        self.root_border = tk.Frame(self.root, bg=c['border_bright'], padx=3, pady=3)
        self.root_border.pack(fill=tk.BOTH, expand=True)
        
        # Main content
        main_frame = tk.Frame(self.root_border, bg=c['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=c['header_bg'], padx=20, pady=20)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="SECURITY WARNING", font=("Arial", 16, "bold"),
                bg=c['header_bg'], fg=c['header_text']).pack(anchor=tk.W)
        tk.Label(header_frame, text="SUSPICIOUS DOMAIN DETECTED", font=("Arial", 13, "bold"),
                bg=c['header_bg'], fg=c['header_text']).pack(anchor=tk.W, pady=(5, 0))
        
        # Separator
        tk.Frame(main_frame, bg=c['separator'], height=2).pack(fill=tk.X)
        
        # Content area
        content_frame = tk.Frame(main_frame, bg=c['bg'], padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Threat message
        icon_section = tk.Frame(content_frame, bg=c['bg'])
        icon_section.pack(fill=tk.X, pady=(0, 15))
        
        icon = self.load_icon()
        if icon:
            icon_label = tk.Label(icon_section, image=icon, bg=c['bg'])
            icon_label.image = icon
            icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Label(icon_section, text="This website has been identified as a security threat. "
                "Visiting may result in theft of personal information, passwords, or malware.",
                font=("Arial", 10), bg=c['bg'], fg=c['fg'], justify=tk.LEFT,
                wraplength=450).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Domain warning box
        domain_warning = tk.Frame(content_frame, bg=c['warning_bg'], relief=tk.SOLID,
                                 bd=2, highlightthickness=1, highlightbackground=c['warning_border'])
        domain_warning.pack(fill=tk.X, pady=15)
        
        domain_warning_inner = tk.Frame(domain_warning, bg=c['warning_bg'], padx=12, pady=10)
        domain_warning_inner.pack(fill=tk.X)
        
        tk.Label(domain_warning_inner, text="DETECTED DOMAIN:",
                font=("Arial", 9, "bold"), bg=c['warning_bg'],
                fg=c['domain_fg']).pack(anchor=tk.W)
        tk.Label(domain_warning_inner, text=self.domain,
                font=("Arial", 12, "bold"), bg=c['warning_bg'],
                fg=c['domain_fg'], wraplength=500, justify=tk.LEFT).pack(anchor=tk.W, pady=(5, 0))
        
        # FEATURE 1: Details button with scrollable content
        self.details_button = tk.Button(content_frame, text="Show Details >>",
                                       font=("Arial", 9), bg=c['details_bg'],
                                       fg=c['details_fg'], border=0, padx=5, pady=3,
                                       command=self.toggle_details, relief=tk.FLAT)
        self.details_button.pack(anchor=tk.W, pady=(0, 10))
        
        # Details container with scrollbar
        self.details_container = tk.Frame(content_frame, bg=c['details_bg'],
                                         relief=tk.SUNKEN, bd=1)
        
        self.details_canvas = tk.Canvas(self.details_container, bg=c['details_bg'],
                                       highlightthickness=0, height=120)
        scrollbar = tk.Scrollbar(self.details_container, orient=tk.VERTICAL,
                               command=self.details_canvas.yview)
        
        self.details_frame = tk.Frame(self.details_canvas, bg=c['details_bg'])
        self.details_frame.bind("<Configure>",
                              lambda e: self.details_canvas.configure(
                                  scrollregion=self.details_canvas.bbox("all")))
        
        self.details_canvas.create_window((0, 0), window=self.details_frame, anchor="nw")
        self.details_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.details_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # FEATURE 2: Countdown timer
        self.countdown_label = tk.Label(content_frame,
                                       text=f"Auto-block in: {self.countdown} seconds",
                                       font=("Arial", 12, "bold"), bg=c['bg'],
                                       fg=c['countdown_fg'])
        self.countdown_label.pack(pady=(20, 15))
        
        tk.Label(content_frame, text="DO NOT PROCEED unless you trust this website completely",
                font=("Arial", 9, "italic"), bg=c['bg'],
                fg=c['domain_fg']).pack(pady=(0, 15))
        
        # Separator before buttons
        tk.Frame(main_frame, bg=c['separator'], height=2).pack(fill=tk.X)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg=c['bg'], padx=20, pady=15)
        button_frame.pack(fill=tk.X)
        
        # BLOCK button (prominent)
        block_btn = tk.Button(button_frame, text="BLOCK THIS WEBSITE",
                             font=("Arial", 12, "bold"), bg=c['button_block_bg'],
                             fg=c['button_text'], padx=50, pady=16,
                             command=self.on_block, cursor='hand2', relief=tk.RAISED, bd=3,
                             activebackground=c['button_block_hover'],
                             activeforeground=c['button_text'])
        block_btn.pack(fill=tk.X, pady=(0, 10))
        block_btn.focus()
        
        # ALLOW button (less prominent)
        tk.Button(button_frame, text="Allow Anyway",
                 font=("Arial", 10), bg=c['button_allow_bg'],
                 fg=c['button_text'], padx=30, pady=10,
                 command=self.on_allow, cursor='hand2', relief=tk.RAISED, bd=2,
                 activebackground=c['button_allow_hover'],
                 activeforeground=c['button_text']).pack(fill=tk.X)
        
        # Populate details content
        self.populate_details()
        
        # Start animations
        self.animate_border()      # Feature 3: Border pulse
        self.update_countdown()    # Feature 2: Countdown timer
    
    def run(self) -> str:
        """Show popup and return result"""
        try:
            self.create_ui()
            self.root.mainloop()
            result = self.result if self.result else "BLOCK"
            return result
        except Exception as e:
            print(f"[Error] Popup error: {e}", file=sys.stderr)
            return "BLOCK"


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


def main():
    """
    Main entry point - called from proxy_simple.py subprocess.
    Arguments: domain_name [reasons_json]
    Returns: BLOCK or ALLOW via stdout
    """
    if len(sys.argv) < 2:
        print("BLOCK", file=sys.stdout)
        sys.stdout.flush()
        sys.exit(0)
    
    domain = sys.argv[1]
    reasons = []
    
    # Parse optional reasons as JSON
    if len(sys.argv) > 2:
        try:
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
            sys.stdout.flush()
            sys.exit(0)
        else:
            print("BLOCK", file=sys.stdout)
            sys.stdout.flush()
            sys.exit(0)
    except Exception as e:
        print("BLOCK", file=sys.stderr)
        sys.stdout.flush()
        sys.exit(0)


if __name__ == "__main__":
    main()
```
