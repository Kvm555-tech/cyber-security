import sys

from app import app


# ============================================================
# SCANNER TESTS
#
# Named links must get the expected result. Optional list files
# (one link per line) measure how the scanner does in bulk:
#   python test_scan.py <phishing-list.txt> <safe-list.txt>
# ============================================================

SAFE_LINKS = [
    "https://www.google.com", "https://mail.google.com/mail/u/0/", "https://google.co.in",
    "google.com", "https://docs.google.com/document/d/abc/edit", "https://github.com/explore",
    "https://www.microsoft.com/en-in", "https://login.microsoftonline.com", "https://www.sbi.co.in",
    "https://www.onlinesbi.sbi", "https://www.hdfcbank.com", "https://www.icicibank.com",
    "https://www.axisbank.com", "https://www.amazon.in/gp/cart", "https://www.flipkart.com",
    "https://www.paytm.com", "https://www.phonepe.com", "https://www.paypal.com/signin",
    "https://www.apple.com/in/", "https://www.netflix.com/browse", "https://www.instagram.com",
    "https://www.facebook.com", "https://web.whatsapp.com", "https://www.linkedin.com/feed/",
    "https://en.wikipedia.org/wiki/Phishing", "https://www.youtube.com/watch?v=abc123",
    "https://www.youtube-nocookie.com/embed/abc", "https://stackoverflow.com/questions",
    "https://www.irctc.co.in", "https://www.india.gov.in", "https://www.iitb.ac.in",
    "https://www.coca-cola.com", "https://www.gitlab.com", "https://www.reddit.com/r/india",
    "https://www.nytimes.com", "http://neverssl.com"
]

BAD_LINKS = [
    "https://www.g00gle.com", "https://paypa1.com/signin", "https://gooogle.com", "https://goggle.com",
    "https://rnicrosoft.com", "https://arnazon.com", "https://faceb00k.com/login", "https://netfl1x.com",
    "https://1nstagram.com", "https://app1e.com", "https://whatsap.com", "https://linkedln.com",
    "https://paypal-login.com", "https://google-security.net", "https://hdfcbank-kyc.com/update",
    "https://onlinesbi-verify.in", "https://www.paypal.com.login-check.net", "https://google.com.account.example",
    "http://192.168.4.20/login.php", "http://www.mybank.example@evil.example/signin",
    "https://https-mybank.example:8443/login", "http://paypal.com.login.verify-account.example/update",
    "http://mybank-help.example//redirect//login", "https://xn--ggle-55da.com"
]

SUSPICIOUS_OR_WORSE = [
    "http://bit.ly/3abcXYZ", "https://secure-login.mybank-verify.example/account",
    "https://tinyurl.com/abc123"
]

BLOCKED_INPUT = ["not a link", "", "http://", "https://exa mple.com"]

client = app.test_client()


def scan(link):
    return client.post("/scan", json={"url": link})


def run_named():

    failures = 0

    groups = [
        (SAFE_LINKS, {"LEGITIMATE"}, "safe"),
        (BAD_LINKS, {"PHISHING"}, "phishing"),
        (SUSPICIOUS_OR_WORSE, {"SUSPICIOUS", "PHISHING"}, "suspicious or worse")
    ]

    for links, expected, name in groups:

        passed = 0

        for link in links:

            body = scan(link).get_json()

            if body.get("prediction") in expected:
                passed += 1
            else:
                failures += 1
                print(f"FAIL expected {name}: {link} -> {body.get('prediction')} {body.get('threatScore')}")

        print(f"{name}: {passed}/{len(links)} passed")

    blocked = sum(scan(link).status_code == 400 for link in BLOCKED_INPUT)
    failures += len(BLOCKED_INPUT) - blocked

    print(f"bad input blocked: {blocked}/{len(BLOCKED_INPUT)}")

    return failures


def run_list(path, label, flagged_is_correct):

    with open(path, encoding="utf-8", errors="ignore") as f:
        links = [line.strip() for line in f if line.strip()]

    counts = {"LEGITIMATE": 0, "SUSPICIOUS": 0, "PHISHING": 0, "error": 0}
    wrong = []

    for link in links:

        body = scan(link).get_json()
        result = body.get("prediction", "error")
        counts[result] += 1

        if result == "PHISHING" if not flagged_is_correct else result == "LEGITIMATE":
            wrong.append(link)

    total = len(links)
    flagged = counts["SUSPICIOUS"] + counts["PHISHING"]

    print(f"\n{label}: {total} links {counts}")
    print(f"flagged as suspicious or phishing: {flagged} ({flagged / total * 100:.1f}%)")

    if not flagged_is_correct:
        for link in wrong[:15]:
            print("  wrongly marked phishing:", link)


failed = run_named()

if len(sys.argv) > 1:
    run_list(sys.argv[1], "Phishing list", True)

if len(sys.argv) > 2:
    run_list(sys.argv[2], "Safe list", False)

sys.exit(1 if failed else 0)
