# CyberShield AI

Phishing link detection using machine learning. Engineering Capstone Project, A.Y. 2026-2027.

## How the parts connect

```
React website  ->  Spring Boot API (port 8080)  ->  Python ML service (port 5000)
                          |
                       PostgreSQL (port 5432, database "cybershield")
```

## Run it

Double-click `START-CYBERSHIELD.bat`. The site opens at http://127.0.0.1:8080.
Keep the two other windows open while using it. Close them to stop the project.

## Folders

| Folder | Contents |
|---|---|
| `frontend` | React website. `npm run build` puts it inside the backend |
| `backend` | Spring Boot API that saves scans to PostgreSQL |
| `ml-service` | Flask service, link feature extractor and training script |
| `models` | Trained models and test results |
| `dataset` | UCI phishing websites dataset |
| `website` | Static information page that can be hosted for free |
| `archive` | Earlier scripts and prototypes, not used by the running project |

## After changing code

Frontend, from `frontend`:

```
npm run build
```

Backend, from `backend` (build the frontend first):

```
mvn package
```

Retrain the live model, from `ml-service`:

```
.venv\Scripts\python.exe train_url_model.py
```

## How a score is made

1. `url_feature_extractor.py` reads 10 features from the link.
2. An XGBoost model gives a model score from 0 to 100.
3. Rules in `app.py` and `lookalike_check.py` give a separate rules score, including the known website check.
4. The higher score is used: below 40 is Legitimate, 40 to 74 is Suspicious, 75 or more is Phishing.

## Known limits

- The scanner reads the link only. It does not open the page.
- The model's 90.68% accuracy is measured on dataset records and does not include the rules.
- Sites outside `models/known_sites.txt` (top 100,000 Tranco sites) or a trusted ending such as `.gov.in` and `.ac.in` are never marked Legitimate.
- Full scanner on real links (2026-10-30): flagged 92.3% of 3,000 unseen links from Phishing.Database, 1.4% of the 3,000 most popular Tranco sites, and 98.3% of 3,000 real Tranco sites ranked just outside the list. Phishing hosted on a known website can pass.
- Run the scanner tests from `ml-service` with `.venv\Scripts\python.exe test_scan.py`, adding a phishing list and a safe list (one link per line) for bulk results.
- The UCI dataset is from 2015, and the rule weights were set by hand.
- The 30-feature `.pkl` models need scikit-learn, which Windows Smart App Control blocks on this PC. The live service does not use them.
- Local database passwords are in `backend/local.properties` and `backend/.db-superuser.local`. Do not share these files.
