import pandas as pd

dataset_path = "../dataset/phishing_dataset.csv"

df = pd.read_csv(dataset_path)

print("===================================")
print("       CYBERSHIELD AI DATASET")
print("===================================")

print("\nDataset Shape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nMissing Values:")
print(df.isnull().sum())

print("\nTarget Distribution:")
print(df["result"].value_counts())

print("\nFirst 5 Records:")
print(df.head())

print("\n===================================")
print("Dataset inspection completed")
print("===================================")