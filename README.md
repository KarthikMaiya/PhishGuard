# **PhishGuard – Real-Time Browser-Level Phishing Protection**

PhishGuard is a lightweight, real-time phishing protection system that intercepts Google Chrome traffic, analyzes domains, and warns users before they access potentially harmful websites. It functions like a miniature firewall + antivirus popup system, detecting suspicious URLs and blocking them with a custom warning page.

---

## **🚀 Features**

### **1. Real-Time Browser-Level Interception**
- Monitors Chrome's outgoing HTTP/HTTPS requests via a local mitmproxy instance  
- Extracts destination domains from each request  
- Matches domains against a suspicious list  
- Popup appears instantly when a threat is detected  

### **2. Professional Security Popup**
- Antivirus-style warning UI  
- Displays suspicious domain  
- ALLOW button → continues normally  
- BLOCK button → displays custom block page  
- Auto-block timer for safety

### **3. Custom "Blocked by PhishGuard" Page**
- Clean HTML warning page  
- Shows blocked domain  
- Prevents accidental access to phishing sites  
- Mimics enterprise firewall behavior  

### **4. Chrome-Only Isolation**
- Only Chrome uses the proxy  
- No change to system proxy settings  
- Other apps (ChatGPT, WhatsApp, VS Code, Windows services) remain unaffected  

### **5. ML-Ready Implementation**
- Suspicious list is rule-based for now  
- Popup supports placeholders for:
  - Suspicion Score  
  - Threat Category  
  - Explanation Text  
- Architecture ready to integrate machine learning scoring  

---

## **📁 Project Structure**
PhishGuard_v2/
│
├── launcher.py # Starts mitmproxy + Chrome with isolated proxy

├── proxy_simple.py # mitmproxy addon for request interception + decisions

├── popup_simple.py # Security popup (Block/Allow)

├── blocked_page.html # Custom block page shown on BLOCK

├── suspicious_urls.txt # List of suspicious domains

├── start_phishguard.bat # One-click launcher

└── assets/

└── security_icon.png # Optional icon for popup



---

## **🛠 How It Works**

1. User runs `start_phishguard.bat`
2. `launcher.py` launches mitmproxy on localhost  
3. Chrome starts with:  --proxy-server=127.0.0.1:<port>
4. `proxy_simple.py` captures every outgoing URL  
5. If domain is in suspicious list → trigger popup  
6. User chooses:
- **ALLOW** → continue to site  
- **BLOCK** → show `blocked_page.html`  
7. Auto-block activates if user does not respond  

---

## **🔧 Requirements**

- Python 3.10+  
- mitmproxy  
- Tkinter (included in Windows Python)  
- Google Chrome  

---

## **▶️ Running the Project**

Double-click: start_phishguard.bat


Chrome will open automatically with protection enabled.

---

## **📌 Future Enhancements**

- Machine learning phishing classifier  
- URL similarity scoring  
- Dashboard + log viewer  
- Auto-learning whitelist system  
- Browser extension integration  

---

## **📄 License**
MIT License (or add your preferred license)





