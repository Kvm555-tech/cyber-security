import pandas as pd
import joblib
import shap

from feature_schema import FEATURE_NAMES


print("===================================")
print("   CYBERSHIELD AI - SHAP TEST")
print("===================================")


# Load dataset
dataset_path = "../dataset/phishing_dataset.csv"

df = pd.read_csv(dataset_path)

print("\nDataset loaded.")
print("Shape:", df.shape)


# Separate features and target
X = df[FEATURE_NAMES]

y = df["result"].map({
    1: 0,     # Legitimate
    -1: 1     # Phishing
})


# Load Random Forest model
model_path = "../models/random_forest.pkl"

model = joblib.load(model_path)

print("\nRandom Forest model loaded successfully.")


# Create SHAP explainer
explainer = shap.TreeExplainer(model)

print("SHAP explainer created successfully.")


# Select one sample
sample = X.iloc[[0]]

print("\nSample used for explanation:")
print(sample.to_string(index=False))


# Generate SHAP values
shap_values = explainer.shap_values(sample)


print("\n===================================")
print("SHAP VALUES")
print("===================================")

print(shap_values)


print("\n===================================")
print("SHAP TEST COMPLETED")
print("===================================")