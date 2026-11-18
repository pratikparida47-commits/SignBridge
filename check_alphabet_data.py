import pandas as pd

file_path = "dataset/isl_alphabet.csv"

df = pd.read_csv(file_path)

print("\nTOTAL SUCCESSFUL ROWS:", len(df))
print("\nSAMPLES FOR EACH LETTER:")
print(df["label"].value_counts().sort_index())

print("\nTOTAL LETTERS FOUND:", df["label"].nunique())
print("\nCSV COLUMNS:", len(df.columns))