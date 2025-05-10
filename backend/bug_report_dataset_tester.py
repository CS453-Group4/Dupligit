import os 
import pandas as pd
from tqdm import tqdm
import logging

from app.text_similarity import calculate_similarity, create_faiss_index
from app.text_similarity import calculate_percentage_similarity

# Set up logging with DEBUG level
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def main():
    logger.info("Starting the process...")

    # Load the dataset
    logger.info("Loading the dataset...")

    script_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(script_dir, 'bug_report_dataset', 'bug_reports_thunderbird.csv')
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    df['Issue_id'] = df['Issue_id'].apply(lambda x: int(x) if isinstance(x, float) else x)

    if 'Issue_id' not in df.columns:
        logger.error("'Issue_id' column is missing in the dataset.")
        return

    logger.info(f"Columns in dataset: {df.columns.tolist()}")

    df['text'] = df['Title'].fillna('') + ' ' + df['Description'].fillna('')
    logger.info(f"Dataset loaded with {len(df)} rows.")

    num_rows = 100
    logger.info(f"Limiting to the first {num_rows} rows for testing.")
    df = df.head(num_rows)

    issue_ids = df['Issue_id'].tolist()
    texts = df['text'].tolist()

    logger.info("Creating FAISS index...")
    faiss_index, model, embeddings = create_faiss_index(texts)
    logger.info("FAISS index created.")

    result_rows = []
    logger.info("Starting similarity calculations...")

    for idx, (curr_issue_id, query_embedding) in tqdm(enumerate(zip(issue_ids, embeddings)), total=len(embeddings)):
        logger.debug(f"Processing issue {curr_issue_id}...")

        I, D = calculate_similarity(faiss_index, query_embedding, k=len(embeddings))
        similar_indices = [i for i in I if i != idx][:5]
        distances = [d for i, d in zip(I, D) if i != idx][:5]
        similarities = calculate_percentage_similarity(distances)

        row = {'Issue_id': curr_issue_id}
        for i, (sim_idx, sim_score) in enumerate(zip(similar_indices, similarities), start=1):
            try:
                similar_issue_id = issue_ids[sim_idx]
                logger.debug(f"Resolved similar_issue_id: {similar_issue_id}")
                
                row[f'Similar_issue_id_{i}'] = similar_issue_id
                row[f'Similarity_{i}'] = round(sim_score, 2)
            except (ValueError, IndexError, TypeError) as e:
                logger.warning(f"Failed to index sim_idx={sim_idx} for issue_id={curr_issue_id}: {e}")
                row[f'Similar_issue_id_{i}'] = None
                row[f'Similarity_{i}'] = None

        result_rows.append(row)
        logger.debug(f"Processed issue {curr_issue_id}. Added to results.")

    logger.info("Saving results to 'similarity_results.csv'...")
    result_df = pd.DataFrame(result_rows)
    result_df.to_csv('similarity_results.csv', index=False)
    logger.info("Results saved successfully.")

if __name__ == '__main__':
    main()
