import pandas as pd
import numpy as np
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

from xgboost import XGBClassifier


# ==========================================
# 1. LOAD DATASET
# ==========================================

print("===================================")
print("     CYBERSHIELD AI MODEL TRAINING")
print("===================================")

dataset_path = "../dataset/phishing_dataset.csv"

df = pd.read_csv(dataset_path)

print("\nDataset loaded successfully.")
print("Dataset shape:", df.shape)


# ==========================================
# 2. SEPARATE FEATURES AND TARGET
# ==========================================

X = df.drop(columns=["result"])

y = df["result"]


# ==========================================
# 3. CONVERT TARGET
# ==========================================
# Original UCI dataset:
#  1  = legitimate
# -1  = phishing
#
# Our application:
#  0  = legitimate
#  1  = phishing

y = y.map({
    1: 0,
    -1: 1
})


print("\nTarget distribution after conversion:")
print(y.value_counts())


# ==========================================
# 4. TRAIN / TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples :", len(X_test))


# ==========================================
# 5. CREATE MODELS
# ==========================================

models = {

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    ),

    "SVM": SVC(
        probability=True,
        kernel="rbf",
        random_state=42
    ),

    "XGBoost": XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss"
    )
}


# ==========================================
# 6. CREATE MODEL DIRECTORY
# ==========================================

os.makedirs("../models", exist_ok=True)


# ==========================================
# 7. TRAIN AND EVALUATE
# ==========================================

results = []


for model_name, model in models.items():

    print("\n")
    print("===================================")
    print("Training:", model_name)
    print("===================================")

    # Train
    model.fit(X_train, y_train)

    # Prediction
    y_pred = model.predict(X_test)

    # Probability prediction
    y_probability = model.predict_proba(X_test)[:, 1]

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)

    precision = precision_score(
        y_test,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        y_pred,
        zero_division=0
    )

    roc_auc = roc_auc_score(
        y_test,
        y_probability
    )

    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(
        y_test,
        y_pred
    ).ravel()

    # False Positive Rate
    false_positive_rate = fp / (fp + tn)

    # Display results
    print("\nAccuracy :", round(accuracy, 4))
    print("Precision:", round(precision, 4))
    print("Recall   :", round(recall, 4))
    print("F1 Score :", round(f1, 4))
    print("ROC-AUC  :", round(roc_auc, 4))
    print("FPR      :", round(false_positive_rate, 4))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=[
                "Legitimate",
                "Phishing"
            ],
            zero_division=0
        )
    )

    # Save model
    model_filename = (
        model_name.lower()
        .replace(" ", "_")
        + ".pkl"
    )

    model_path = os.path.join(
        "../models",
        model_filename
    )

    joblib.dump(model, model_path)

    print("Model saved to:", model_path)

    # Store metrics
    results.append({
        "Model": model_name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1_Score": f1,
        "ROC_AUC": roc_auc,
        "False_Positive_Rate": false_positive_rate
    })


# ==========================================
# 8. SAVE COMPARISON RESULTS
# ==========================================

results_df = pd.DataFrame(results)

results_path = "../models/model_comparison.csv"

results_df.to_csv(
    results_path,
    index=False
)


# ==========================================
# 9. DISPLAY FINAL COMPARISON
# ==========================================

print("\n")
print("===================================")
print("       MODEL COMPARISON")
print("===================================")

print(
    results_df.to_string(
        index=False
    )
)

print("\nResults saved to:")
print(results_path)

print("\n===================================")
print("       TRAINING COMPLETED")
print("===================================")