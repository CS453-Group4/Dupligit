import pandas as pd

# Read the CSV file into a pandas DataFrame
df = pd.read_csv('sorted_similarity.csv')

# Sort the data by similarity score
df_sorted = df.sort_values(by='similarity_score', ascending=True)

# Save the sorted DataFrame to a new CSV for easier analysis
df_sorted.to_csv('formatted_results.csv', index=False)

# Function to print results in chunks
def print_in_chunks(df, chunk_size=1):
    total_rows = len(df)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        print(f"\nShowing rows {start + 1} to {end}:")
        chunk = df.iloc[start:end]
        for index, row in chunk.iterrows():
            print(f"Text1:\n {row['text1']}\n\nText2:\n {row['text2']}\nSimilarity Score: {row['similarity_score']}\n{'-'*50}")
        input("Press Enter to continue to the next chunk...")

# Print the sorted results in chunks of 10
print_in_chunks(df_sorted, chunk_size=1)
