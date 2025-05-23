import os
import sys
import pandas as pd
from tqdm import tqdm
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.test.text_similarity_test import calculate_percentage_similarity, calculate_similarity, create_faiss_index

# Configuration
USE_ALL_ROWS = True
NUM_ROWS = 20
SIM_NUM = 20

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def main():
    logger.info("Starting the process...")

    script_dir = os.path.dirname(os.path.realpath(__file__))

    eval_file_path = os.path.join(script_dir, 'bug_report_dataset/test_thunderbird.csv')
    eval_df = pd.read_csv(eval_file_path)
    eval_issue_ids = eval_df['Issue_id'].astype(int).tolist()
    logger.info(f"Loaded {len(eval_issue_ids)} issue IDs to evaluate.")

    file_path = os.path.join(script_dir, 'bug_report_dataset', 'bug_reports_thunderbird.csv')
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df['Issue_id'] = df['Issue_id'].astype(int)
    df['text'] = df['Title'].fillna('') + ' ' + df['Description'].fillna('')
    logger.info(f"Dataset loaded with {len(df)} rows.")

    df_eval = df[df['Issue_id'].isin(eval_issue_ids)].reset_index(drop=True)
    logger.info(f"Filtered dataset contains {len(df_eval)} evaluation rows.")

    issue_ids_all = df['Issue_id'].tolist()
    texts_all = df['text'].tolist()
    faiss_index, embeddings_all = create_faiss_index(texts_all)
    logger.info("FAISS index created on all data.")

    id_to_index = {issue_id: idx for idx, issue_id in enumerate(issue_ids_all)}

    result_rows = []
    logger.info("Starting similarity calculations for evaluation issues...")

    for _, row in tqdm(df_eval.iterrows(), total=len(df_eval)):
        curr_issue_id = row['Issue_id']
        curr_index = id_to_index[curr_issue_id]
        query_embedding = embeddings_all[curr_index]

        I, D = calculate_similarity(faiss_index, query_embedding, k=len(embeddings_all))
        similar_indices = [i for i in I if i != curr_index][:SIM_NUM]
        distances = [d for i, d in zip(I, D) if i != curr_index][:SIM_NUM]
        similarities = calculate_percentage_similarity(distances)

        result = {'Issue_id': curr_issue_id}
        for i, (sim_idx, sim_score) in enumerate(zip(similar_indices, similarities), start=1):
            try:
                similar_issue_id = issue_ids_all[sim_idx]
                result[f'Similar_issue_id_{i}'] = similar_issue_id
                result[f'Similarity_{i}'] = round(sim_score, 2)
            except Exception as e:
                logger.warning(f"Indexing error for issue_id={curr_issue_id}: {e}")
                result[f'Similar_issue_id_{i}'] = None
                result[f'Similarity_{i}'] = None

        result_rows.append(result)

    logger.info("Saving results to 'similarity_results.csv'...")
    result_df = pd.DataFrame(result_rows)

    result_file_path = os.path.join(script_dir, 'similarity_results.csv')
    result_df.to_csv(result_file_path, index=False)
    logger.info("Results saved successfully.")

if __name__ == '__main__':
    main()
