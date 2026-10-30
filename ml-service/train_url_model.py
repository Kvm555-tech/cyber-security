import csv
import json
import os

import numpy as np
import xgboost as xgb

from url_feature_extractor import URL_FEATURE_NAMES


# ============================================================
# TRAIN THE LIVE SCANNER MODEL
#
# Uses only the features that can be read from a link, so the
# model sees the same information in training and in live use.
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "..", "dataset", "phishing_dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "xgboost_url.json")
METRICS_PATH = os.path.join(BASE_DIR, "..", "models", "xgboost_url_metrics.json")

with open(DATASET_PATH, newline="") as f:
    rows = list(csv.DictReader(f))

X = np.array(
    [[float(row[name]) for name in URL_FEATURE_NAMES] for row in rows]
)

# Dataset: 1 = legitimate, -1 = phishing. Model: 0 = legitimate, 1 = phishing.
y = np.array([1 if row["result"] == "-1" else 0 for row in rows])

# Stratified 80 / 20 split
rng = np.random.default_rng(42)
test_mask = np.zeros(len(y), dtype=bool)

for label in (0, 1):
    indexes = np.flatnonzero(y == label)
    rng.shuffle(indexes)
    test_mask[indexes[: round(len(indexes) * 0.2)]] = True

dtrain = xgb.DMatrix(X[~test_mask], label=y[~test_mask], feature_names=URL_FEATURE_NAMES)
dtest = xgb.DMatrix(X[test_mask], label=y[test_mask], feature_names=URL_FEATURE_NAMES)

booster = xgb.train(
    {
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "max_depth": 5,
        "eta": 0.1,
        "seed": 42
    },
    dtrain,
    num_boost_round=200
)

predicted = (booster.predict(dtest) >= 0.5).astype(int)
actual = y[test_mask]

tp = int(((predicted == 1) & (actual == 1)).sum())
tn = int(((predicted == 0) & (actual == 0)).sum())
fp = int(((predicted == 1) & (actual == 0)).sum())
fn = int(((predicted == 0) & (actual == 1)).sum())

metrics = {
    "testRecords": len(actual),
    "accuracy": round((tp + tn) / len(actual) * 100, 2),
    "precision": round(tp / (tp + fp) * 100, 2),
    "recall": round(tp / (tp + fn) * 100, 2),
    "f1": round(2 * tp / (2 * tp + fp + fn) * 100, 2),
    "falseAlarms": round(fp / (fp + tn) * 100, 2)
}

booster.save_model(MODEL_PATH)

with open(METRICS_PATH, "w") as f:
    json.dump(metrics, f, indent=2)

print("Features:", len(URL_FEATURE_NAMES))
print("Training records:", int((~test_mask).sum()))
print("Results:", metrics)
