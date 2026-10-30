from urllib.parse import urlparse
import ipaddress
import re


# ============================================================
# URL FEATURE EXTRACTOR
#
# Uses the same values as the UCI dataset:
#   1 = looks legitimate, 0 = suspicious, -1 = looks like phishing
# ============================================================

URL_FEATURE_NAMES = [
    "having_ip_address",
    "url_length",
    "shortining_service",
    "having_at_symbol",
    "double_slash_redirecting",
    "prefix_suffix",
    "having_sub_domain",
    "sslfinal_state",
    "port",
    "https_token"
]

SHORTENING_DOMAINS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd",
    "buff.ly", "cutt.ly", "shorturl.at", "rebrand.ly", "rb.gy", "t.ly",
    "tiny.cc", "v.gd", "shorturl.pt", "shortme.id", "s.id"
}

SECOND_LEVEL_SUFFIXES = {
    "co.in", "ac.in", "org.in", "net.in", "gov.in", "edu.in", "nic.in",
    "co.uk", "ac.uk", "org.uk", "gov.uk", "com.au", "co.jp", "com.br"
}


def is_ip_address(hostname):

    try:
        ipaddress.ip_address(hostname)
        return True

    except ValueError:
        return False


def count_subdomain_dots(hostname):

    name = hostname[4:] if hostname.startswith("www.") else hostname

    for suffix in SECOND_LEVEL_SUFFIXES:
        if name.endswith("." + suffix):
            name = name[: -len(suffix)] + "tld"
            break

    return name.count(".")


def extract_url_features(url):

    original_url = url.strip()

    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", original_url):
        full_url = original_url
    else:
        # No scheme typed, so there is no sign of missing HTTPS to count
        full_url = "https://" + original_url

    parsed = urlparse(full_url)

    hostname = (parsed.hostname or "").lower()

    if not hostname or (" " in hostname) or (
        "." not in hostname and hostname != "localhost"
    ):
        raise ValueError("This does not look like a website link.")

    is_ip = is_ip_address(hostname)

    length = len(original_url)

    if length < 54:
        url_length = 1
    elif length <= 75:
        url_length = 0
    else:
        url_length = -1

    is_shortener = any(
        hostname == domain or hostname.endswith("." + domain)
        for domain in SHORTENING_DOMAINS
    )

    after_protocol = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", original_url)

    dots = count_subdomain_dots(hostname)

    if is_ip or dots <= 1:
        sub_domain = 1
    elif dots == 2:
        sub_domain = 0
    else:
        sub_domain = -1

    try:
        port = parsed.port
    except ValueError:
        raise ValueError("This link has an invalid port number.")

    return {
        "having_ip_address": -1 if is_ip else 1,
        "url_length": url_length,
        "shortining_service": -1 if is_shortener else 1,
        "having_at_symbol": -1 if "@" in original_url else 1,
        "double_slash_redirecting": -1 if "//" in after_protocol else 1,
        "prefix_suffix": -1 if "-" in hostname else 1,
        "having_sub_domain": sub_domain,
        "sslfinal_state": 1 if parsed.scheme.lower() == "https" else -1,
        "port": -1 if port not in (None, 80, 443) else 1,
        "https_token": -1 if "https" in hostname else 1
    }
