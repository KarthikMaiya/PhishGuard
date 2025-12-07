# 🛡️ PhishGuard – Chrome-Triggered Background Phishing Protection

PhishGuard is a **real-time, machine-learning-based phishing detection system for Windows** that runs silently in the background and **automatically activates whenever Google Chrome is launched**. It analyzes every website in real time and предупрежs users before they fall victim to phishing attacks.

---
## 🎥 Live Demo (Click to Play)

> This video demonstrates real-time phishing detection, warning popup, and blocking in action.

<p align="center">
  <video width="720" controls>
    <source src="demo/phishguard_demo.mp4" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</p>


## 🚀 What Makes PhishGuard Unique?

- ✅ Works **automatically with Chrome** (no manual startup)
- ✅ Uses **Machine Learning (XGBoost)** for real-time detection
- ✅ **Intercepts live web traffic** using a secure local proxy
- ✅ Gives users **instant Allow / Block control**
- ✅ **Auto-shuts down** when Chrome is closed (zero idle resource usage)

---

## 🧠 High-Level Working (1-Minute Overview)

1. **User opens Google Chrome**
2. PhishGuard’s **background controller (`launcher.py`) starts silently**
3. **ML Analyzer** starts on `127.0.0.1:8000`
4. **Local Proxy** starts on `127.0.0.1:8080`
5. Chrome is **forced to route all traffic through PhishGuard**
6. Every website is:
   - Analyzed using ML
   - Either **allowed instantly** or **blocked with a warning**
7. When Chrome closes → **All services stop automatically**

---

## 🔄 System Process Flow

Google Chrome
↓
python launcher.py (Master Controller)
↓
serve_ml.py (ML API – Port 8000)
↓
proxy_simple.py (Traffic Interceptor – Port 8080)
↓
popup_simple.py (User Warning Interface)

yaml
Copy code

---

## ⚠️ What Happens on a Phishing Attempt?

- A warning popup is shown with:
  - Threat level
  - Suspicious domain
  - Countdown timer  
- User can:
  - ✅ **Allow** → Continue browsing
  - ❌ **Block** → Redirected to a safe blocked page
- Blocking happens at the **network level**, not just visually.

---

## ✅ Key Features Summary

- Silent background protection  
- Real-time ML-based phishing detection  
- Chrome-only enforcement  
- User-controlled decisions  
- No performance overhead when Chrome is closed  
- Fully automated startup & shutdown  

---

## 🧪 How to Run (Development Mode)

```bash
cd PhishGuard_v2
python launcher.py
