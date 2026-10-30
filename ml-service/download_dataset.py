from ucimlrepo import fetch_ucirepo
import pandas as pd
import os

print("Downloading phishing dataset...")

# Fetch UCI Phishing Websites dataset
dataset = fetch_ucirepo(id=327)

features = dataset.data.features
target = dataset.data.targets

# Combine features and target
df = pd.concat([features, target], axis=1)

# Create dataset directory if it does not exist
os.makedirs("../dataset", exist_ok=True)

# Save dataset
output_path = "../dataset/phishing_dataset.csv"

df.to_csv(output_path, index=False)

print("===================================")
print("Dataset downloaded successfully!")
print("===================================")

print("Rows    :", df.shape[0])
print("Columns :", df.shape[1])

print("Saved to:")
print(output_path)