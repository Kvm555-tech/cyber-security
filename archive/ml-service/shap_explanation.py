import pandas as pd
import joblib
import shap

from feature_schema import FEATURE_NAMES


print("===================================")
print(" CYBERSHIELD AI - SHAP EXPLANATION")
print("===================================")


# --------------------------------------------------
# 1. Load dataset
# --------------------------------------------------

dataset_path = "../dataset/phishing_dataset.csv"

df = pd.read_csv(dataset_path)

X = df[FEATURE_NAMES]

print("\nDataset loaded successfully.")


# --------------------------------------------------
# 2. Load Random Forest model
# --------------------------------------------------

model_path = "../models/random_forest.pkl"

model = joblib.load(model_path)

print("Random Forest model loaded successfully.")


# --------------------------------------------------
# 3. Select one sample
# --------------------------------------------------

sample = X.iloc[[0]]

print("\nSample selected for prediction.")


# --------------------------------------------------
# 4. Prediction
# --------------------------------------------------

prediction = model.predict(sample)[0]

probabilities = model.predict_proba(sample)[0]

legitimate_probability = probabilities[0]

phishing_probability = probabilities[1]


if prediction == 1:
    prediction_label = "PHISHING"
else:
    prediction_label = "LEGITIMATE"


print("\n===================================")
print("PREDICTION")
print("===================================")

print("Prediction            :", prediction_label)
print(
    "Legitimate Probability:",
    round(legitimate_probability * 100, 2),
    "%"
)
print(
    "Phishing Probability  :",
    round(phishing_probability * 100, 2),
    "%"
)


# --------------------------------------------------
# 5. Threat Score
# --------------------------------------------------

threat_score = phishing_probability * 100


if threat_score >= 75:
    threat_level = "HIGH"
elif threat_score >= 40:
    threat_level = "MEDIUM"
else:
    threat_level = "LOW"


print("\n===================================")
print("THREAT SCORE")
print("===================================")

print("Threat Score :", round(threat_score, 2), "/ 100")
print("Threat Level :", threat_level)


# --------------------------------------------------
# 6. Create SHAP explainer
# --------------------------------------------------

explainer = shap.TreeExplainer(model)

shap_values = explainer.shap_values(sample)


# --------------------------------------------------
# 7. Extract phishing-class SHAP values
# --------------------------------------------------

if len(shap_values.shape) == 3:

    # Shape:
    # samples × features × classes

    phishing_shap_values = shap_values[0, :, 1]

else:

    # Older SHAP output format
    phishing_shap_values = shap_values[1][0]


# --------------------------------------------------
# 8. Create feature explanation table
# --------------------------------------------------

explanation_df = pd.DataFrame({
    "Feature": FEATURE_NAMES,
    "Feature_Value": sample.iloc[0].values,
    "SHAP_Value": phishing_shap_values
})


# Sort by absolute SHAP contribution
explanation_df["Absolute_SHAP"] = (
    explanation_df["SHAP_Value"].abs()
)

explanation_df = explanation_df.sort_values(
    by="Absolute_SHAP",
    ascending=False
)


# --------------------------------------------------
# 9. Display top features
# --------------------------------------------------

print("\n===================================")
print("TOP SHAP FEATURES")
print("===================================")

top_features = explanation_df.head(10)

for index, row in top_features.iterrows():

    direction = "increases phishing risk"

    if row["SHAP_Value"] < 0:
        direction = "decreases phishing risk"

    print(
        f"{row['Feature']:<30} "
        f"SHAP: {row['SHAP_Value']:+.4f} "
        f"({direction})"
    )


# --------------------------------------------------
# 10. Save explanation
# --------------------------------------------------

output_path = "../models/shap_explanation.csv"

explanation_df.to_csv(
    output_path,
    index=False
)


print("\n===================================")
print("SHAP EXPLANATION COMPLETED")
print("===================================")

print("Explanation saved to:")
print(output_path)