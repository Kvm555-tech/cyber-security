import os
from urllib.parse import urlparse

import numpy as np
import xgboost as xgb
from flask import Flask, jsonify, request

from lookalike_check import link_warnings
from url_feature_extractor import URL_FEATURE_NAMES, extract_url_features


# ============================================================
# CYBERSHIELD AI - ML SERVICE
# ============================================================

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "xgboost_url.json")

booster = xgb.Booster()
booster.load_model(MODEL_PATH)


# ============================================================
# PLAIN LANGUAGE REASONS
# ============================================================

RISK_REASONS = {
    "having_ip_address": "The link uses a number address instead of a website name.",
    "url_length": "The link is unusually long.",
    "shortining_service": "The link uses a shortening service, which hides the real address.",
    "having_at_symbol": "The link contains an @ symbol, which can hide the real address.",
    "double_slash_redirecting": "The link has an extra // that can redirect to another site.",
    "prefix_suffix": "The website name contains a hyphen, often used to copy real names.",
    "having_sub_domain": "The link has extra parts before the main website name.",
    "sslfinal_state": "The link does not use HTTPS.",
    "port": "The link uses an unusual port number.",
    "https_token": "The website name contains the word https to look secure."
}

SAFE_REASONS = {
    "having_ip_address": "The link uses a website name, not a number address.",
    "url_length": "The link is a normal length.",
    "shortining_service": "The link shows its real address.",
    "having_at_symbol": "The link has no @ symbol.",
    "double_slash_redirecting": "The link has no hidden redirect.",
    "prefix_suffix": "The website name has no hyphen.",
    "having_sub_domain": "The link has no extra parts before the main website name.",
    "sslfinal_state": "The link uses HTTPS.",
    "port": "The link uses a standard port.",
    "https_token": "The website name does not misuse the word https."
}


# ============================================================
# WARNING SIGN RULES
#
# The UCI dataset carries little signal for these signs, so the
# model alone can miss them. Points are added for each sign and
# the final score is the higher of the two checks.
# ============================================================

RULE_POINTS = {
    "having_ip_address": 60,
    "having_at_symbol": 60,
    "https_token": 60,
    "double_slash_redirecting": 50,
    "shortining_service": 45,
    "port": 40,
    "having_sub_domain": 40,
    "prefix_suffix": 25,
    "url_length": 20,
    "sslfinal_state": 15
}


BAIT_WORDS = (
    "login", "signin", "verify", "secure", "security", "account",
    "update", "password", "banking", "support"
)

BAIT_WORD_POINTS = 25

BAIT_WORD_REASON = "The website name uses a word common in phishing, such as login or verify."


def get_hostname(url):

    return (urlparse(url if "://" in url else "https://" + url).hostname or "").lower()


def has_bait_word(url):

    hostname = get_hostname(url)

    # A plain name like login.gov or update.microsoft.com is not enough:
    # the word has to be joined into a name with a hyphen.
    return any(
        word in part
        for part in hostname.lower().split(".")
        if "-" in part
        for word in BAIT_WORDS
    )


def get_rule_score(features, url):

    points = sum(
        weight for name, weight in RULE_POINTS.items()
        if features[name] == -1
    )

    if has_bait_word(url):
        points += BAIT_WORD_POINTS

    points += sum(warning["points"] for warning in link_warnings(get_hostname(url)))

    return min(points, 95)


def get_threat_level(threat_score):

    if threat_score >= 75:
        return "HIGH"

    if threat_score >= 40:
        return "MEDIUM"

    return "LOW"


def get_prediction(threat_score):

    if threat_score >= 75:
        return "PHISHING"

    if threat_score >= 40:
        return "SUSPICIOUS"

    return "LEGITIMATE"


def build_reasons(features, contributions, url):

    impacts = {
        name: float(value)
        for name, value in zip(URL_FEATURE_NAMES, contributions)
    }

    warnings = [
        {"feature": w["feature"], "effect": "increases risk", "text": w["text"]}
        for w in link_warnings(get_hostname(url))
    ]

    # Other warning signs found in the link, strongest rule first
    warnings += [
        {"feature": name, "effect": "increases risk", "text": RISK_REASONS[name]}
        for name in sorted(RULE_POINTS, key=RULE_POINTS.get, reverse=True)
        if features[name] == -1
    ]

    if has_bait_word(url):
        warnings.append({
            "feature": "bait_word",
            "effect": "increases risk",
            "text": BAIT_WORD_REASON
        })

    if warnings:
        return warnings

    # Clean link: show what the model relied on most
    clean = sorted(
        (name for name in URL_FEATURE_NAMES if impacts[name] < 0),
        key=lambda name: impacts[name]
    )

    return [{
        "feature": "known_site",
        "effect": "lowers risk",
        "text": "This website is a known, trusted site."
    }] + [
        {"feature": name, "effect": "lowers risk", "text": SAFE_REASONS[name]}
        for name in clean[:2]
    ]


@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "UP",
        "service": "CyberShield AI ML Service",
        "model": "XGBoost",
        "features": len(URL_FEATURE_NAMES)
    })


@app.route("/scan", methods=["POST"])
def scan_url():

    data = request.get_json(silent=True) or {}

    url = str(data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "Enter a website link to scan."}), 400

    if len(url) > 2048:
        return jsonify({"error": "This link is too long to scan."}), 400

    try:
        features = extract_url_features(url)

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    matrix = xgb.DMatrix(
        np.array([[features[name] for name in URL_FEATURE_NAMES]], dtype=float),
        feature_names=URL_FEATURE_NAMES
    )

    phishing_probability = float(booster.predict(matrix)[0])

    # Built-in TreeSHAP values. The last column is the base value.
    contributions = booster.predict(matrix, pred_contribs=True)[0][:-1]

    model_score = round(phishing_probability * 100, 2)

    rule_score = get_rule_score(features, url)

    threat_score = max(model_score, rule_score)

    return jsonify({
        "url": url,
        "prediction": get_prediction(threat_score),
        "threatScore": threat_score,
        "threatLevel": get_threat_level(threat_score),
        "modelScore": model_score,
        "ruleScore": rule_score,
        "reasons": build_reasons(features, contributions, url)
    })


if __name__ == "__main__":

    app.run(host="127.0.0.1", port=5000, debug=False)
