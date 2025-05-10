import os
import pandas as pd
from tqdm import tqdm
import logging

from app.text_similarity import calculate_similarity, create_faiss_index
from app.text_similarity import calculate_percentage_similarity

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def main():
    logger.info("Starting the process...")

    # Load the dataset
    logger.info("Loading the dataset...")

    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Create the path to the CSV file relative to the script
    file_path = os.path.join(script_dir, 'bug_report_dataset', 'bug_reports_thunderbird.csv')

    # Load the dataset
    df = pd.read_csv(file_path)

    # Strip any leading/trailing spaces from column names
    df.columns = df.columns.str.strip()

    # Print columns to help identify issues
    logger.info(f"Columns in dataset: {df.columns.tolist()}")

    # Ensure the 'Issue_id' column exists
    if 'Issue_id' not in df.columns:
        logger.error("'Issue_id' column is missing in the dataset.")
        return

    df['text'] = df['Title'].fillna('') + ' ' + df['Description'].fillna('')
    logger.info(f"Dataset loaded with {len(df)} rows.")

    # Limit the number of rows used for the test (e.g., first 100 rows)
    num_rows = 10  # Adjust this value to limit the number of rows
    logger.info(f"Limiting to the first {num_rows} rows for testing.")
    df = df.head(num_rows)  # Use only the first `num_rows` rows

    issue_ids = df['Issue_id'].tolist()
    texts = df['text'].tolist()

    # Create FAISS index
    logger.info("Creating FAISS index...")
    faiss_index, model = create_faiss_index(texts)
    logger.info("FAISS index created.")

    # Initialize result collection
    result_rows = []
    logger.info("Starting similarity calculations...")

    # Iterate over each issue
    for idx, (issue_id, text) in tqdm(enumerate(zip(issue_ids, texts)), total=len(texts)):
        logger.debug(f"Processing issue {issue_id}...")

        results = calculate_similarity(faiss_index, model, texts, text)

        # Get the top 5 similar issues (excluding the current issue itself)
        similar_indices = [i for i, _ in results if i != idx][:5]
        distances = [d for _, d in results if _ != idx][:5]
        similarities = calculate_percentage_similarity(distances)

        # Collect results for the row
        row = {'Issue_id': issue_id}
        for i, (sim_id, sim_score) in enumerate(zip(similar_indices, similarities), start=1):
            # Check if the similar issue ID is valid
            if sim_id is not None:
                row[f'Similar_issue_id_{i}'] = issue_ids[sim_id]
                row[f'Similarity_{i}'] = round(sim_score, 2)
            else:
                row[f'Similar_issue_id_{i}'] = None
                row[f'Similarity_{i}'] = None

        result_rows.append(row)
        logger.debug(f"Processed issue {issue_id}. Added to results.")

    # Save the results to a CSV
    logger.info("Saving results to 'similarity_results.csv'...")
    result_df = pd.DataFrame(result_rows)
    result_df.to_csv('similarity_results.csv', index=False)
    logger.info("Results saved successfully.")

if __name__ == '__main__':
    main()
