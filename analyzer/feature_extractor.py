# feature_extractor.py
# Domain-only feature extractor for PhishGuard_v2 with public suffix list support
from urllib.parse import urlparse
import ipaddress
import math
import re
from collections import Counter
from publicsuffix2 import get_tld
import Levenshtein


KNOWN_BRANDS = [
    "google", "microsoft", "paypal", "apple",
    "amazon", "facebook", "instagram",
    "netflix", "github", "openai"
]

def normalize_homoglyphs(s: str) -> str:
    return (
        s.replace("0", "o")
         .replace("1", "l")
         .replace("3", "e")
         .replace("5", "s")
         .replace("7", "t")
         .replace("rn", "m")
         .lower()
    )

def brand_impersonation_score(domain: str):
    base = domain.split('.')[0].lower()
    base = normalize_homoglyphs(base)

    best_score = 0.0
    best_brand = None

    for brand in KNOWN_BRANDS:
        score = Levenshtein.ratio(base, brand)

        if score > best_score:
            best_score = score
            best_brand = brand

    return best_score, best_brand



SUSPICIOUS_TLDS = {
    "ru","tk","ml","ga","cf","biz","info","top","work","pw","xyz","win","click","gq"
}

shortening_domains = re.compile(
    r"(bit\.ly|goo\.gl|tinyurl|t\.co|ow\.ly|is\.gd|buff\.ly|bitly|cutt\.ly|shorte|lnkd\.in)",
    re.IGNORECASE
)

def _normalize_netloc(netloc: str) -> str:
    # remove port if present
    return netloc.split(':')[0].lower().strip()

def has_ip(domain_or_netloc: str) -> int:
    netloc = _normalize_netloc(domain_or_netloc)
    try:
        # handle cases where a URL like 'http://1.2.3.4' gives '1.2.3.4'
        ipaddress.ip_address(netloc)
        return 1
    except Exception:
        return 0

def contains_hyphen(domain_or_netloc: str) -> int:
    netloc = _normalize_netloc(domain_or_netloc)
    return 1 if '-' in netloc else 0

def contains_numbers(domain_or_netloc: str) -> int:
    netloc = _normalize_netloc(domain_or_netloc)
    return 1 if re.search(r'\d', netloc) else 0

def is_long_domain(domain_or_netloc: str, threshold: int = 25) -> int:
    netloc = _normalize_netloc(domain_or_netloc)
    return 1 if len(netloc) > threshold else 0

def subdomain_count(domain_or_netloc: str) -> int:
    """
    Count actual subdomains using public suffix list.
    
    Examples:
    - google.com → 0 (no subdomains)
    - mail.google.com → 1 (1 subdomain: mail)
    - accounts.google.com → 1 (1 subdomain: accounts)
    - example.co.uk → 0 (co.uk is the TLD, no subdomains)
    - sub.example.co.uk → 1 (1 subdomain: sub)
    - IP addresses → 0
    """
    domain = domain_or_netloc.split(':')[0]  # Remove port if present
    
    # IP address → always 0 subdomains
    try:
        ipaddress.ip_address(domain)
        return 0
    except Exception:
        pass
    
    try:
        # Extract TLD using public suffix list (supports multi-part TLDs like co.uk)
        tld = get_tld(domain, strict=False)
        
        # Count total dots in full domain
        total_dots = domain.count('.')
        
        # Count dots in TLD (e.g., co.uk has 1 dot)
        tld_dots = tld.count('.')
        
        # Subdomains = total dots - (tld dots + 1)
        # The +1 accounts for the dot between domain and TLD
        return max(0, total_dots - tld_dots - 1)
    except Exception:
        # Fallback: if public suffix parsing fails, use simple logic
        dot_count = domain.count('.')
        return max(dot_count - 1, 0)

def tld_suspicious(domain_or_netloc: str) -> int:
    netloc = _normalize_netloc(domain_or_netloc)
    parts = netloc.rsplit('.', 2)
    if len(parts) < 2:
        return 0
    tld = parts[-1]
    return 1 if tld in SUSPICIOUS_TLDS else 0

def domain_entropy(domain_or_netloc: str) -> float:
    netloc = _normalize_netloc(domain_or_netloc)
    # use only the hostname part (no dots)
    s = netloc.replace('.', '')
    if not s:
        return 0.0
    counts = Counter(s)
    probs = [count/len(s) for count in counts.values()]
    ent = -sum(p * math.log2(p) for p in probs if p > 0)
    return round(ent, 3)

def uses_shortener(domain_or_netloc: str) -> int:
    netloc = _normalize_netloc(domain_or_netloc)
    return 1 if shortening_domains.search(netloc) else 0

def extract_domain_features_from_url(url: str):
    
    # Ensure URL has scheme
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Remove port if present
    domain = domain.split(":")[0]
    
    """
    Input: full URL string (the proxy will send full URL).
    Internal: extract domain/netloc and compute domain-level features.
    Returns: list of numeric features in a fixed order.
    """
    try:
        netloc = urlparse(url).netloc
        if not netloc:
            # If no netloc, it might be a bare domain - try parsing with scheme
            netloc = urlparse('http://' + url).netloc
    except Exception:
        netloc = url  # fallback if already a bare domain

    netloc = _normalize_netloc(netloc)

    features = [
        has_ip(netloc),
        contains_hyphen(netloc),
        contains_numbers(netloc),
        is_long_domain(netloc),
        subdomain_count(netloc),
        tld_suspicious(netloc),
        domain_entropy(netloc),
        uses_shortener(netloc)
    ]
    
    similarity, spoofed_brand = brand_impersonation_score(domain)


    
    # return list (ints/floats)
    return features
