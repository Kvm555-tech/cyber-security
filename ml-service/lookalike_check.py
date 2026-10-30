import os
import re


# ============================================================
# WEBSITE NAME CHECKS
#
# Signs in the website name that the UCI dataset does not cover:
# imitated brands, free hosting, risky endings and random names.
# ============================================================

BRANDS = {
    "adobe": "Adobe",
    "amazon": "Amazon",
    "apple": "Apple",
    "axisbank": "Axis Bank",
    "binance": "Binance",
    "coinbase": "Coinbase",
    "dhl": "DHL",
    "discord": "Discord",
    "dropbox": "Dropbox",
    "facebook": "Facebook",
    "fedex": "FedEx",
    "flipkart": "Flipkart",
    "github": "GitHub",
    "google": "Google",
    "hdfcbank": "HDFC Bank",
    "icicibank": "ICICI Bank",
    "instagram": "Instagram",
    "kotak": "Kotak",
    "linkedin": "LinkedIn",
    "metamask": "MetaMask",
    "microsoft": "Microsoft",
    "netflix": "Netflix",
    "onlinesbi": "SBI",
    "outlook": "Outlook",
    "paypal": "PayPal",
    "paytm": "Paytm",
    "phonepe": "PhonePe",
    "roblox": "Roblox",
    "spotify": "Spotify",
    "steamcommunity": "Steam",
    "telegram": "Telegram",
    "twitter": "Twitter",
    "usps": "USPS",
    "whatsapp": "WhatsApp",
    "wikipedia": "Wikipedia",
    "yahoo": "Yahoo",
    "youtube": "YouTube"
}

# Real sites whose names would otherwise look like a brand
KNOWN_REAL_NAMES = {"youtube-nocookie", "amazonaws", "googleapis", "gstatic", "wikimedia", "telegra"}

LOOKALIKE_LETTERS = str.maketrans({
    "0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "$": "s"
})

# A brand joined to one of these words is a common phishing pattern
BRAND_BAIT_WORDS = {
    "login", "signin", "secure", "security", "verify", "verification", "account",
    "update", "support", "help", "service", "kyc", "alert", "billing", "pay",
    "wallet", "reward", "gift", "free", "claim", "check", "auth", "online", "bank"
}

FREE_HOSTS = (
    "pages.dev", "vercel.app", "netlify.app", "github.io", "replit.app", "replit.dev",
    "framer.app", "framer.website", "webflow.io", "weebly.com", "web.app",
    "firebaseapp.com", "workers.dev", "onrender.com", "glitch.me", "wixsite.com",
    "herokuapp.com", "surge.sh", "blogspot.com", "sites.google.com", "000webhostapp.com",
    "godaddysites.com", "square.site", "wordpress.com", "ngrok.io", "ngrok-free.app"
)

RISKY_ENDINGS = {
    "help", "top", "xyz", "icu", "cc", "ss", "site", "online", "click", "tk", "ml",
    "ga", "cf", "gq", "sbs", "cfd", "rest", "buzz", "quest", "live", "lat", "bond"
}

TRUSTED_ENDINGS = (
    ".gov", ".edu", ".mil", ".gov.in", ".nic.in", ".ac.in", ".edu.in", ".gov.uk", ".ac.uk"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Top 100,000 sites from the Tranco popularity list
with open(os.path.join(BASE_DIR, "..", "models", "known_sites.txt")) as known_sites_file:
    KNOWN_SITES = {line.strip() for line in known_sites_file}

POINTS_UNKNOWN_SITE = 50
POINTS_IMITATES_BRAND = 80
POINTS_USES_BRAND_NAME = 40
POINTS_MIXED_LETTERS = 80
POINTS_FREE_HOST = 40
POINTS_RANDOM_NAME = 35
POINTS_RISKY_ENDING = 30


def get_ending_length(parts):

    # Endings like co.in, com.hk and ac.uk count as one ending
    has_two_part_ending = (
        len(parts) > 2 and len(parts[-1]) == 2
        and parts[-2] in ("co", "com", "org", "net", "ac", "gov", "edu", "nic")
    )

    return 2 if has_two_part_ending else 1


def split_hostname(hostname):

    parts = hostname.removeprefix("www.").split(".")

    suffix_length = get_ending_length(parts)

    registered = parts[-(suffix_length + 1)] if len(parts) > suffix_length else ""

    return registered, parts[:-(suffix_length + 1)]


def is_known_site(hostname):

    parts = hostname.removeprefix("www.").split(".")

    # Only approved organisations can register these endings
    if hostname.endswith(TRUSTED_ENDINGS):
        return True

    return ".".join(parts[-(get_ending_length(parts) + 1):]) in KNOWN_SITES


def edit_distance(first, second):

    previous = list(range(len(second) + 1))

    for i, a in enumerate(first, 1):

        current = [i]

        for j, b in enumerate(second, 1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (a != b)
            ))

        previous = current

    return previous[-1]


def looks_like(name, brand):

    if name == brand:
        return False

    swapped = name.translate(LOOKALIKE_LETTERS).replace("rn", "m").replace("vv", "w")

    if swapped == brand or swapped.replace("l", "i") == brand.replace("l", "i"):
        return True

    # Short names differ by one letter too easily to compare this way
    return len(brand) >= 6 and edit_distance(name, brand) == 1


def check_brand(hostname):

    registered, subdomains = split_hostname(hostname)

    if not registered or registered in KNOWN_REAL_NAMES:
        return None

    if registered in BRANDS:

        # roblox.ss: a real brand name on a risky ending
        if hostname.rsplit(".", 1)[-1] in RISKY_ENDINGS:
            return BRANDS[registered], POINTS_IMITATES_BRAND

        return None

    pieces = registered.split("-")

    for brand, label in BRANDS.items():

        # paypa1.com or paypal.com.login-check.net
        if looks_like(registered, brand) or brand in subdomains:
            return label, POINTS_IMITATES_BRAND

        if len(pieces) > 1:

            # g00gle-login.com
            if any(looks_like(piece, brand) for piece in pieces):
                return label, POINTS_IMITATES_BRAND

            if brand in pieces:

                # paypal-login.com is worse than amazon-images.com
                if BRAND_BAIT_WORDS.intersection(pieces):
                    return label, POINTS_IMITATES_BRAND

                return label, POINTS_USES_BRAND_NAME

    return None


def has_mixed_letters(hostname):

    # Latin letters mixed with look-alike letters from another alphabet.
    # A name written fully in another language is normal.
    for label in hostname.split("."):

        try:
            decoded = label.encode("ascii").decode("idna") if label.startswith("xn--") else label
        except (UnicodeError, ValueError):
            return True

        if not decoded.isascii() and re.search(r"[a-z]", decoded):
            return True

    return False


def free_host_of(hostname):

    for host in FREE_HOSTS:
        if hostname.endswith("." + host):
            return host

    return None


def looks_random(hostname):

    host = free_host_of(hostname)

    name = hostname[: -len(host) - 1] if host else split_hostname(hostname)[0]

    for token in re.split(r"[-.]", name):

        # 2m1p9z: letters and numbers shuffled together
        switches = len(re.findall(r"[a-z][0-9]|[0-9][a-z]", token))
        digits = sum(c.isdigit() for c in token)

        if switches >= 3 and digits >= 3:
            return True

        # dhltrcjhfga: a long run with no vowels
        if re.search(r"[bcdfghjklmnpqrstvwxz]{6,}", token):
            return True

    return False


def link_warnings(hostname):

    warnings = []

    if not is_known_site(hostname):
        warnings.append({
            "feature": "unknown_site",
            "points": POINTS_UNKNOWN_SITE,
            "text": "This website could not be confirmed as a known, trusted site."
        })

    brand = check_brand(hostname)

    if brand:
        warnings.append({
            "feature": "lookalike",
            "points": brand[1],
            "text": f"The website name imitates {brand[0]}, but this is not the real {brand[0]} site."
        })

    if has_mixed_letters(hostname):
        warnings.append({
            "feature": "mixed_letters",
            "points": POINTS_MIXED_LETTERS,
            "text": "The website name mixes letters from different alphabets to imitate a real name."
        })

    if free_host_of(hostname):
        warnings.append({
            "feature": "free_host",
            "points": POINTS_FREE_HOST,
            "text": "The site is on a free hosting service, where anyone can publish a page in minutes."
        })

    if looks_random(hostname):
        warnings.append({
            "feature": "random_name",
            "points": POINTS_RANDOM_NAME,
            "text": "The website name looks randomly generated."
        })

    if hostname.rsplit(".", 1)[-1] in RISKY_ENDINGS:
        warnings.append({
            "feature": "risky_ending",
            "points": POINTS_RISKY_ENDING,
            "text": "The website name uses a cheap ending that is often used for short-lived sites."
        })

    return warnings
