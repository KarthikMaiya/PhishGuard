#!/usr/bin/env python3
from urllib.parse import urlparse
import ipaddress
from publicsuffix2 import get_tld

def subdomain_count_debug(domain_or_netloc: str) -> int:
    domain = domain_or_netloc.split(':')[0]
    
    print(f'  subdomain_count called with: {repr(domain)}')
    
    try:
        ipaddress.ip_address(domain)
        print(f'    -> Detected as IP, returning 0')
        return 0
    except Exception:
        pass
    
    try:
        tld = get_tld(domain, strict=False)
        total_dots = domain.count('.')
        tld_dots = tld.count('.')
        result = max(0, total_dots - tld_dots - 1)
        print(f'    -> TLD={tld}, total_dots={total_dots}, tld_dots={tld_dots}, result={result}')
        return result
    except Exception as e:
        print(f'    -> Exception: {e}')
        dot_count = domain.count('.')
        return max(dot_count - 1, 0)

# Test with mail.google.com
urls = ['mail.google.com', 'https://mail.google.com', 'accounts.google.com', 'google.com']

for url in urls:
    print(f'\nTesting: {url}')
    netloc = urlparse(url).netloc
    print(f'  urlparse(url).netloc = {repr(netloc)}')

    if not netloc:
        netloc = url
        print(f'  Using fallback: {repr(netloc)}')

    result = subdomain_count_debug(netloc)
    print(f'  Final result: {result}')
