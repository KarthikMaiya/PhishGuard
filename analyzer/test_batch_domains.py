import requests
import json

ANALYZER_URL = "http://127.0.0.1:8000/score"

TEST_DOMAINS = [
    # PayPal phishing patterns
    "http://paypal-login-secure.com",
    "http://paypal-update-alert.com",
    "http://verify-paypal-account.com",
    "http://paypal-security-center.net",
    "http://paypal-resolution-case.xyz",

    # Banking phishing
    "http://secure-chase-banking.com",
    "http://icici-verification-alert.in.net",
    "http://hdfc-update-security.xyz",
    "http://sbi-online-update-alert.com",
    "http://axisbank-login-verification.net",

    # Apple / Google phishing
    "http://login-appleid-update.com",
    "http://apple-security-notice.net",
    "http://accounts-google-verification.com",
    "http://google-support-center-alert.xyz",
    "http://reset-google-password-alert.com",

    # Microsoft / Office365 phishing
    "http://office365-password-reset.com",
    "http://microsoft-security-warning.net",
    "http://verify-office-login.xyz",
    "http://ms-support-center-alert.com",
    "http://onedrive-authenticate-login.net",

    # Shortener abuse
    "http://bit.ly/verify-update",
    "http://tinyurl.com/reset-login",
    "http://goo.gl/security-alert",
    "http://is.gd/paypal-case",

    # High-entropy / random domains
    "http://xvjqmzplkdn.com",
    "http://secure-qw9dkl2p-update.xyz",
    "http://login-asd98asdas9d.com",
    "http://verify-9q8w7e6r5t.net",
    "http://qw8e7r6t5y4u3i2o1p.biz",

    # Legitimate control group
    "https://google.com",
    "https://github.com",
    "https://microsoft.com",
    "https://openai.com",
    "https://stackoverflow.com"
]


def analyze_url(url):
    try:
        response = requests.post(
            ANALYZER_URL,
            headers={"Content-Type": "application/json"},
            json={"url": url},
            timeout=2
        )
        data = response.json()
        return {
            "url": url,
            "score": data.get("score", 0.0),
            "risk": data.get("risk", "unknown"),
            "reasons": data.get("reasons", [])
        }
    except Exception as e:
        return {
            "url": url,
            "score": -1,
            "risk": "error",
            "reasons": [f"Error: {e}"]
        }


def main():
    print("\n============================================")
    print("      PHISHGUARD BATCH DOMAIN TEST")
    print("============================================\n")

    results = []

    for domain in TEST_DOMAINS:
        print(f"Testing: {domain}")
        result = analyze_url(domain)
        results.append(result)

    # Sort by score (highest risk first)
    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)

    print("\n============================================")
    print("              FINAL REPORT (SORTED)")
    print("============================================\n")

    for r in results_sorted:
        print(f"URL: {r['url']}")
        print(f"Score: {round(r['score'], 4)}")
        print(f"Risk: {r['risk']}")
        print("Reasons:", ", ".join(r['reasons']) if r['reasons'] else "(none)")
        print("-" * 50)

    print("\nDone! Analyzer batch test completed.\n")


if __name__ == "__main__":
    main()
