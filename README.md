PhishGuard v2 – Real-Time Browser-Level Phishing Protection

PhishGuard v2 is a lightweight, real-time phishing protection system designed to safeguard users from malicious and suspicious websites. It works at the browser level, intercepting outgoing web requests made by Google Chrome and alerting the user before they access potentially harmful domains.

🚀 Features
1. Browser-Level Real-Time Protection

Intercepts Chrome traffic using a local mitmproxy instance

Extracts the destination domain from every request

Cross-checks against a list of suspicious domains

Popup alert appears instantly on detection

2. Security Alert Popup

Professional antivirus-style popup window

Displays full warning message

Shows suspicious domain

Auto-blocks after timeout

User can choose:

ALLOW → continue to the website

BLOCK → redirect to a custom “Blocked by PhishGuard” page

3. Custom Block Page

Clean HTML warning page

Displays blocked domain

Notifies user of potential phishing risk

Mimics a real security firewall block screen

4. Chrome-Only Isolation

Only Chrome traffic is routed through the proxy

Other apps (ChatGPT, WhatsApp, VS Code, Windows services) remain unaffected

No system proxy settings are modified

5. ML-Ready Architecture

Suspicion list currently rule-based

Designed to integrate a machine learning scoring model:

Suspicion score

Threat category

NLP heuristics

URL entropy and structure patterns

📁 Project Structure
PhishGuard_v2/
│
├── launcher.py               # Starts mitmproxy and Chrome with isolated proxy
├── proxy_simple.py           # mitmproxy addon for URL interception & popup calls
├── popup_simple.py           # Security popup (Block/Allow)
├── blocked_page.html         # Custom webpage shown on BLOCK
├── suspicious_urls.txt       # List of suspicious domains
├── start_phishguard.bat      # One-click launcher
└── assets/
      └── security_icon.png   # Optional icon for popup

🛠 How It Works

User launches start_phishguard.bat

launcher.py starts mitmproxy on a local port

Chrome launches with:

--proxy-server=127.0.0.1:<port>


proxy_simple.py captures every request

If domain is suspicious → popup opens

User selects Allow or Block

Blocked domains show the HTML block page

🔧 Requirements

Python 3.10+

mitmproxy

Tkinter (bundled with Python on Windows)

Google Chrome installed

▶️ Running the Project

Simply double-click:

start_phishguard.bat
