"""
PhishGuard Popup - Enterprise antivirus-style security alert UI
Runs as a standalone subprocess called from proxy_simple.py.
Takes domain as command-line argument.
Returns result via stdout: "BLOCK" or "ALLOW"
Features: professional UI, countdown timer, expandable details, custom block page.
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
    """Enterprise-grade antivirus-style popup for suspicious domain detection"""
    
    def __init__(self, domain: str, timeout_sec: int = 8):
        self.domain = domain
        self.timeout_sec = timeout_sec
        self.countdown = timeout_sec
        self.result = None
        self.details_expanded = False
        self.risk_level = "HIGH"
        
        # Single light theme color scheme
        self.colors = {
            'bg': '#ffffff',
            'fg': '#222222',
            'header_bg': '#d32f2f',
            'header_text': '#ffffff',
            'title_fg': '#ffffff',
            'button_block_bg': '#d32f2f',
            'button_block_hover': '#b71c1c',
            'button_allow_bg': '#666666',
            'button_allow_hover': '#444444',
            'button_text': '#ffffff',
            'border': '#e0e0e0',
            'countdown_fg': '#d32f2f',
            'countdown_bg': '#ffffff',
            'details_bg': '#f5f5f5',
            'details_fg': '#333333',
            'warning_bg': '#fff3cd',
            'warning_fg': '#856404',
            'warning_border': '#ffc107',
            'risk_high': '#d32f2f',
            'risk_medium': '#ff9800',
            'risk_low': '#ffc107',
            'desc_fg': '#555555'
        }
    
    def load_icon(self):
        """Load security icon from assets/security_icon.png if available"""
        if not PIL_AVAILABLE:
            return None
        
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "security_icon.png")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img = img.resize((80, 80), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except Exception as e:
            pass
        return None
    
    def create_ui(self):
        """Create the enterprise-grade professional UI"""
        self.root = tk.Tk()
        self.root.title("PhishGuard Security Alert - SUSPICIOUS DOMAIN DETECTED")
        self.root.geometry("620x500")
        self.root.attributes('-topmost', True)
        
        # Disable close button
        def disable_close():
            pass
        self.root.protocol("WM_DELETE_WINDOW", disable_close)
        
        # Center on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        c = self.colors
        self.root.config(bg=c['bg'])
        
        # High-visibility header with bold styling
        self.header_frame = tk.Frame(self.root, bg=c['header_bg'], height=80)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)
        self.header_frame.pack_propagate(False)
        
        # Header content frame
        header_content = tk.Frame(self.header_frame, bg=c['header_bg'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        self.title_label = tk.Label(
            header_content,
            text="SUSPICIOUS DOMAIN DETECTED",
            font=("Arial", 14, "bold"),
            bg=c['header_bg'],
            fg=c['title_fg']
        )
        self.title_label.pack(side=tk.LEFT, expand=True)
        
        # Subtitle
        self.subtitle_label = tk.Label(
            header_content,
            text="Your connection has been blocked for security reasons",
            font=("Arial", 9),
            bg=c['header_bg'],
            fg=c['header_text']
        )
        self.subtitle_label.pack(fill=tk.X, pady=(5, 0))
        
        # Risk level color bar
        self.risk_bar = tk.Frame(
            self.root,
            bg=c[f'risk_{self.risk_level.lower()}'],
            height=6
        )
        self.risk_bar.pack(fill=tk.X)
        self.risk_bar.pack_propagate(False)
        
        # Risk level label with color coding
        risk_frame = tk.Frame(self.root, bg=c['details_bg'], padx=15, pady=6)
        risk_frame.pack(fill=tk.X)
        
        self.risk_label = tk.Label(
            risk_frame,
            text=f"Risk Level: {self.risk_level} - This website is potentially dangerous",
            font=("Arial", 9, "bold"),
            bg=c['details_bg'],
            fg=c['details_fg']
        )
        self.risk_label.pack(anchor=tk.W)
        
        # Main content frame
        self.content_frame = tk.Frame(self.root, bg=c['bg'], padx=20, pady=20)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Warning box
        self.warning_box = tk.Frame(
            self.content_frame,
            bg=c['warning_bg'],
            padx=12,
            pady=12,
            relief=tk.FLAT,
            bd=0
        )
        self.warning_box.pack(fill=tk.X, pady=(0, 15))
        
        warning_text = tk.Label(
            self.warning_box,
            text="WARNING: This website may be used to steal your information or install malware. Do not proceed unless you are certain this is a legitimate website.",
            font=("Arial", 9),
            bg=c['warning_bg'],
            fg=c['warning_fg'],
            justify=tk.LEFT,
            wraplength=550
        )
        warning_text.pack(fill=tk.X)
        
        # Icon and description section
        icon_section = tk.Frame(self.content_frame, bg=c['bg'])
        icon_section.pack(fill=tk.X, pady=(0, 15))
        
        # Load and display icon
        icon = self.load_icon()
        if icon:
            icon_label = tk.Label(icon_section, image=icon, bg=c['bg'])
            icon_label.image = icon
            icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Description text
        self.desc_label = tk.Label(
            icon_section,
            text="PhishGuard has identified this domain as potentially harmful. It may be attempting to steal your login credentials, personal information, or install malicious software.",
            font=("Arial", 10),
            bg=c['bg'],
            fg=c['desc_fg'],
            justify=tk.LEFT,
            wraplength=400
        )
        self.desc_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Domain display section with border
        domain_border = tk.Frame(self.content_frame, bg=c['border'], padx=1, pady=1)
        domain_border.pack(fill=tk.X, pady=15)
        
        self.domain_section = tk.Frame(domain_border, bg=c['details_bg'], padx=12, pady=12)
        self.domain_section.pack(fill=tk.X)
        
        self.domain_label = tk.Label(
            self.domain_section,
            text=f"Detected Domain: {self.domain}",
            font=("Arial", 11, "bold"),
            bg=c['details_bg'],
            fg=c['details_fg'],
            wraplength=500,
            justify=tk.LEFT
        )
        self.domain_label.pack(anchor=tk.W, fill=tk.X)
        
        # Expandable details button
        self.details_button = tk.Button(
            self.content_frame,
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
        self.details_button.pack(anchor=tk.W, pady=(0, 10))
        
        # Details frame (hidden by default)
        self.details_frame = tk.Frame(self.content_frame, bg=c['details_bg'], padx=10, pady=10)
        
        # Countdown timer with high visibility
        self.countdown_label = tk.Label(
            self.content_frame,
            text=f"Auto-block in: {self.countdown} seconds",
            font=("Arial", 13, "bold"),
            bg=c['countdown_bg'],
            fg=c['countdown_fg']
        )
        self.countdown_label.pack(pady=(15, 20))
        
        # "Are you sure?" warning at bottom
        sure_label = tk.Label(
            self.content_frame,
            text="Are you sure you want to proceed?",
            font=("Arial", 9, "italic"),
            bg=c['bg'],
            fg=c['desc_fg']
        )
        sure_label.pack(pady=(0, 10))
        
        # Button frame with large buttons
        self.button_frame = tk.Frame(self.content_frame, bg=c['bg'])
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # BLOCK button (red, left) - default focus
        self.block_btn = tk.Button(
            self.button_frame,
            text="BLOCK",
            font=("Arial", 13, "bold"),
            bg=c['button_block_bg'],
            fg=c['button_text'],
            padx=40,
            pady=14,
            command=self.on_block,
            cursor='hand2',
            relief=tk.RAISED,
            bd=2,
            activebackground=c['button_block_hover'],
            activeforeground=c['button_text']
        )
        self.block_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.BOTH)
        
        # ALLOW button (grey, right)
        self.allow_btn = tk.Button(
            self.button_frame,
            text="ALLOW",
            font=("Arial", 13, "bold"),
            bg=c['button_allow_bg'],
            fg=c['button_text'],
            padx=40,
            pady=14,
            command=self.on_allow,
            cursor='hand2',
            relief=tk.RAISED,
            bd=2,
            activebackground=c['button_allow_hover'],
            activeforeground=c['button_text']
        )
        self.allow_btn.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.BOTH)
        
        # Focus on block button (safer default)
        self.block_btn.focus()
        
        # Start countdown timer
        self.update_countdown()
    
    def toggle_details(self):
        """Toggle details section visibility"""
        if self.details_expanded:
            self.hide_details()
        else:
            self.show_details()
    
    def show_details(self):
        """Show expandable details section with proper theming"""
        if self.details_expanded:
            return
        
        self.details_expanded = True
        self.details_button.config(text="Hide Details <<")
        
        c = self.colors
        
        # Clear details frame
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        details_text = f"""Domain: {self.domain}
Reason: Suspicious domain detected by PhishGuard
Suspicion Score: High risk - Pattern matching
Category: Phishing / Malware detection"""
        
        detail_label = tk.Label(
            self.details_frame,
            text=details_text,
            font=("Arial", 9),
            bg=c['details_bg'],
            fg=c['details_fg'],
            justify=tk.LEFT,
            wraplength=500
        )
        detail_label.pack(anchor=tk.W, fill=tk.X)
        
        self.details_frame.pack(fill=tk.X, pady=10, before=self.countdown_label)
    
    def hide_details(self):
        """Hide expandable details section"""
        if not self.details_expanded:
            return
        
        self.details_expanded = False
        self.details_button.config(text="Show Details >>")
        self.details_frame.pack_forget()
    
    def update_countdown(self):
        """Update countdown timer every second"""
        if self.countdown > 0:
            self.countdown_label.config(text=f"Auto-block in: {self.countdown} seconds")
            self.countdown -= 1
            self.root.after(1000, self.update_countdown)
        else:
            # Auto-block when countdown reaches zero
            self.result = "BLOCK"
            self.root.destroy()
    
    def on_block(self):
        """Block button clicked"""
        self.result = "BLOCK"
        self.root.destroy()
    
    def on_allow(self):
        """Allow button clicked"""
        self.result = "ALLOW"
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
    Show professional antivirus-style popup for suspicious domain detection.
    
    Args:
        domain: The suspicious domain detected
        timeout_sec: Auto-block countdown in seconds (default 8)
    
    Returns:
        "BLOCK" or "ALLOW" string
    """
    popup = PhishGuardPopup(domain, timeout_sec)
    return popup.run()


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

