"""
PhishGuard Popup - Aggressive enterprise-grade security alert UI
Pulsating red perimeter border animation with professional threat styling.
Runs as a standalone subprocess called from proxy_simple.py.
Takes domain as command-line argument.
Returns result via stdout: "BLOCK" or "ALLOW"
"""
import tkinter as tk
from tkinter import messagebox
import sys
import os

# Try to import PIL for icon support, but make it optional
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class PhishGuardPopup:
    """Aggressive enterprise-grade security popup for suspicious domain detection"""
    
    def __init__(self, domain: str, timeout_sec: int = 8):
        self.domain = domain
        self.timeout_sec = timeout_sec
        self.countdown = timeout_sec
        self.result = None
        self.details_expanded = False
        self.border_pulse_state = 0  # 0 = bright red, 1 = dark red
        self.animation_id = None
        
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
        """Load security icon from assets/security_icon.png if available"""
        if not PIL_AVAILABLE:
            return None
        
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "security_icon.png")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except Exception as e:
            pass
        return None
    
    def animate_border(self):
        """Animate the pulsating red border - non-blocking"""
        if self.root.winfo_exists():
            c = self.colors
            # Pulse between bright red and dark red
            if self.border_pulse_state == 0:
                border_color = c['border_bright']
                self.border_pulse_state = 1
            else:
                border_color = c['border_dark']
                self.border_pulse_state = 0
            
            self.root_border.config(bg=border_color)
            
            # Schedule next animation in 500ms
            self.animation_id = self.root.after(500, self.animate_border)
    
    def create_ui(self):
        """Create the aggressive enterprise-grade security UI"""
        self.root = tk.Tk()
        self.root.title("SECURITY WARNING - PhishGuard")
        self.root.geometry("680x650")
        self.root.attributes('-topmost', True)
        
        # Disable close button (force decision)
        def disable_close():
            pass
        self.root.protocol("WM_DELETE_WINDOW", disable_close)
        
        # Center on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        c = self.colors
        
        # Pulsating red border (outer perimeter frame)
        self.root_border = tk.Frame(self.root, bg=c['border_bright'], padx=3, pady=3)
        self.root_border.pack(fill=tk.BOTH, expand=True)
        
        # Main content area inside border
        main_frame = tk.Frame(self.root_border, bg=c['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # High-visibility aggressive header
        header_frame = tk.Frame(main_frame, bg=c['header_bg'], padx=20, pady=20)
        header_frame.pack(fill=tk.X)
        
        # Title (all caps, bold, aggressive)
        title_label = tk.Label(
            header_frame,
            text="SECURITY WARNING",
            font=("Arial", 16, "bold"),
            bg=c['header_bg'],
            fg=c['header_text']
        )
        title_label.pack(anchor=tk.W)
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="SUSPICIOUS DOMAIN DETECTED",
            font=("Arial", 13, "bold"),
            bg=c['header_bg'],
            fg=c['header_text']
        )
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Red separator line
        sep1 = tk.Frame(main_frame, bg=c['separator'], height=2)
        sep1.pack(fill=tk.X)
        
        # Content area
        content_frame = tk.Frame(main_frame, bg=c['bg'], padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Warning icon and threat message
        icon_section = tk.Frame(content_frame, bg=c['bg'])
        icon_section.pack(fill=tk.X, pady=(0, 15))
        
        # Load and display icon
        icon = self.load_icon()
        if icon:
            icon_label = tk.Label(icon_section, image=icon, bg=c['bg'])
            icon_label.image = icon
            icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Threat message
        threat_text = tk.Label(
            icon_section,
            text="This website has been identified as a potential security threat. Visiting this site may result in theft of personal information, passwords, or malware infection.",
            font=("Arial", 10),
            bg=c['bg'],
            fg=c['fg'],
            justify=tk.LEFT,
            wraplength=450
        )
        threat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Domain warning box (highlighted)
        domain_warning = tk.Frame(content_frame, bg=c['warning_bg'], relief=tk.SOLID, bd=2, highlightthickness=1, highlightbackground=c['warning_border'])
        domain_warning.pack(fill=tk.X, pady=15)
        
        domain_warning_inner = tk.Frame(domain_warning, bg=c['warning_bg'], padx=12, pady=10)
        domain_warning_inner.pack(fill=tk.X)
        
        warning_label = tk.Label(
            domain_warning_inner,
            text="DETECTED DOMAIN:",
            font=("Arial", 9, "bold"),
            bg=c['warning_bg'],
            fg=c['domain_fg']
        )
        warning_label.pack(anchor=tk.W)
        
        domain_label = tk.Label(
            domain_warning_inner,
            text=self.domain,
            font=("Arial", 12, "bold"),
            bg=c['warning_bg'],
            fg=c['domain_fg'],
            wraplength=500,
            justify=tk.LEFT
        )
        domain_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Expandable details section with scrollbar
        details_btn = tk.Button(
            content_frame,
            text="Show Details >>",
            font=("Arial", 9),
            bg=c['details_bg'],
            fg=c['details_fg'],
            border=0,
            padx=5,
            pady=3,
            command=self.toggle_details,
            relief=tk.FLAT
        )
        details_btn.pack(anchor=tk.W, pady=(0, 10))
        self.details_button = details_btn
        
        # Details frame with canvas and scrollbar (initially hidden)
        self.details_container = tk.Frame(content_frame, bg=c['details_bg'], relief=tk.SUNKEN, bd=1)
        
        # Canvas for scrollable content
        self.details_canvas = tk.Canvas(
            self.details_container,
            bg=c['details_bg'],
            highlightthickness=0,
            height=120
        )
        scrollbar = tk.Scrollbar(self.details_container, orient=tk.VERTICAL, command=self.details_canvas.yview)
        
        self.details_frame = tk.Frame(self.details_canvas, bg=c['details_bg'])
        self.details_frame.bind(
            "<Configure>",
            lambda e: self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))
        )
        
        self.details_canvas.create_window((0, 0), window=self.details_frame, anchor="nw")
        self.details_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.details_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Countdown timer (prominent)
        countdown_label = tk.Label(
            content_frame,
            text=f"Auto-block in: {self.countdown} seconds",
            font=("Arial", 12, "bold"),
            bg=c['bg'],
            fg=c['countdown_fg']
        )
        countdown_label.pack(pady=(20, 15))
        self.countdown_label = countdown_label
        
        # Urgent message
        urgent_label = tk.Label(
            content_frame,
            text="DO NOT PROCEED unless you trust this website completely",
            font=("Arial", 9, "italic"),
            bg=c['bg'],
            fg=c['domain_fg']
        )
        urgent_label.pack(pady=(0, 15))
        
        # Red separator line before buttons
        sep2 = tk.Frame(main_frame, bg=c['separator'], height=2)
        sep2.pack(fill=tk.X)
        
        # Button area
        button_frame = tk.Frame(main_frame, bg=c['bg'], padx=20, pady=15)
        button_frame.pack(fill=tk.X)
        
        # BLOCK button (dominant, large, bright red)
        self.block_btn = tk.Button(
            button_frame,
            text="BLOCK THIS WEBSITE",
            font=("Arial", 12, "bold"),
            bg=c['button_block_bg'],
            fg=c['button_text'],
            padx=50,
            pady=16,
            command=self.on_block,
            cursor='hand2',
            relief=tk.RAISED,
            bd=3,
            activebackground=c['button_block_hover'],
            activeforeground=c['button_text']
        )
        self.block_btn.pack(fill=tk.X, pady=(0, 10))
        self.block_btn.focus()
        
        # ALLOW button (smaller, grey, less prominent)
        self.allow_btn = tk.Button(
            button_frame,
            text="Allow Anyway",
            font=("Arial", 10),
            bg=c['button_allow_bg'],
            fg=c['button_text'],
            padx=30,
            pady=10,
            command=self.on_allow,
            cursor='hand2',
            relief=tk.RAISED,
            bd=2,
            activebackground=c['button_allow_hover'],
            activeforeground=c['button_text']
        )
        self.allow_btn.pack(fill=tk.X)
        
        # Start animations
        self.animate_border()
        self.update_countdown()
        
        # Populate initial details
        self.populate_details()
    
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
        
        detail_label = tk.Label(
            self.details_frame,
            text=details_text,
            font=("Arial", 9),
            bg=c['details_bg'],
            fg=c['details_fg'],
            justify=tk.LEFT,
            wraplength=600,
            padx=10,
            pady=10
        )
        detail_label.pack(anchor=tk.W, fill=tk.X)
    
    def toggle_details(self):
        """Toggle details section visibility"""
        if self.details_expanded:
            self.hide_details()
        else:
            self.show_details()
    
    def show_details(self):
        """Show expandable details section"""
        if self.details_expanded:
            return
        
        self.details_expanded = True
        self.details_button.config(text="Hide Details <<")
        self.details_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15), after=self.details_button)
    
    def hide_details(self):
        """Hide expandable details section"""
        if not self.details_expanded:
            return
        
        self.details_expanded = False
        self.details_button.config(text="Show Details >>")
        self.details_container.pack_forget()
    
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
    
    def stop_animation(self):
        """Stop the border pulsation animation"""
        if self.animation_id is not None:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
    
    def on_block(self):
        """Block button clicked"""
        self.result = "BLOCK"
        self.stop_animation()
        self.root.destroy()
    
    def on_allow(self):
        """Allow button clicked"""
        self.result = "ALLOW"
        self.stop_animation()
        self.root.destroy()
    
    def run(self) -> str:
        """Show popup and return result"""
        try:
            self.create_ui()
            self.root.mainloop()
            return self.result if self.result else "BLOCK"
        except Exception as e:
            print(f"[Error] Popup error: {e}", file=sys.stderr)
            return "BLOCK"


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


def show_popup(url: str, score, reasons) -> str:
    """
    Synchronous popup API for ML integration.

    Args:
        url: full URL to display
        score: float or None (risk probability 0-1)
        reasons: list of strings (detection reasons)

    Returns:
        'allow' or 'block' (lowercase)
    """
    try:
        root = tk.Tk()
        root.title("PhishGuard - Security Alert")
        root.geometry("750x400")
        root.attributes('-topmost', True)

        # Main container
        frm = tk.Frame(root, bg='#ffffff', padx=20, pady=20)
        frm.pack(fill=tk.BOTH, expand=True)

        # Header with risk level
        header_frm = tk.Frame(frm, bg='#8b0000', padx=15, pady=15)
        header_frm.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(header_frm, text="SECURITY WARNING", font=("Arial", 14, "bold"), 
                bg='#8b0000', fg='white').pack(anchor=tk.W)
        tk.Label(header_frm, text="Suspicious domain detected by PhishGuard", 
                font=("Arial", 10), bg='#8b0000', fg='white').pack(anchor=tk.W, pady=(5,0))

        # URL display
        tk.Label(frm, text="URL:", font=("Arial", 9, "bold"), fg='#333').pack(anchor=tk.W)
        url_label = tk.Label(frm, text=str(url), font=("Courier", 9), 
                           wraplength=700, justify=tk.LEFT, fg='#cc0000')
        url_label.pack(anchor=tk.W, pady=(0, 12), padx=(10, 0))

        # Risk score and level
        if score is not None:
            risk_pct = float(score) * 100.0
            risk_level = "HIGH" if risk_pct >= 75 else ("MEDIUM" if risk_pct >= 40 else "LOW")
            risk_color = '#cc0000' if risk_pct >= 75 else ('#ff9900' if risk_pct >= 40 else '#00aa00')
            
            score_frm = tk.Frame(frm, bg='#f0f0f0', relief=tk.SOLID, bd=1)
            score_frm.pack(fill=tk.X, pady=(0, 12))
            
            score_inner = tk.Frame(score_frm, bg='#f0f0f0', padx=12, pady=8)
            score_inner.pack(fill=tk.X)
            
            tk.Label(score_inner, text=f"Risk Level: {risk_level}", 
                    font=("Arial", 11, "bold"), fg=risk_color, bg='#f0f0f0').pack(anchor=tk.W)
            tk.Label(score_inner, text=f"Probability Score: {risk_pct:.1f}%", 
                    font=("Arial", 10), fg='#333', bg='#f0f0f0').pack(anchor=tk.W, pady=(3,0))

        # Reasons section
        if reasons and len(reasons) > 0:
            tk.Label(frm, text="Detection Reasons:", font=("Arial", 9, "bold"), 
                   fg='#333').pack(anchor=tk.W, pady=(0, 5))
            
            reasons_frm = tk.Frame(frm, bg='#fff9e6', relief=tk.SOLID, bd=1)
            reasons_frm.pack(fill=tk.X, pady=(0, 12))
            
            reasons_inner = tk.Frame(reasons_frm, bg='#fff9e6', padx=12, pady=8)
            reasons_inner.pack(fill=tk.X)
            
            for reason in reasons[:5]:  # Limit to 5 reasons
                tk.Label(reasons_inner, text=f"• {reason}", font=("Arial", 9), 
                       fg='#333', bg='#fff9e6', justify=tk.LEFT, wraplength=650).pack(anchor=tk.W, pady=2)

        # Action label
        tk.Label(frm, text="What would you like to do?", 
                font=("Arial", 9, "bold"), fg='#333').pack(anchor=tk.W, pady=(8, 10))

        # Buttons
        choice = {'value': 'block'}

        def allow():
            choice['value'] = 'allow'
            root.destroy()

        def block():
            choice['value'] = 'block'
            root.destroy()

        btn_frm = tk.Frame(frm, bg='#ffffff')
        btn_frm.pack(fill=tk.X, pady=(10, 0))

        allow_btn = tk.Button(btn_frm, text="ALLOW", width=15, font=("Arial", 10),
                            bg='#666666', fg='white', command=allow, padx=10, pady=8)
        allow_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        block_btn = tk.Button(btn_frm, text="BLOCK", width=15, font=("Arial", 10),
                            bg='#cc0000', fg='white', command=block, padx=10, pady=8)
        block_btn.pack(side=tk.LEFT)

        # Center window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")

        root.mainloop()
        return choice['value']
    except Exception:
        return 'block'


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


if __name__ == "__main__":
    main()


