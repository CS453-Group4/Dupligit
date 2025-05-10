import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def create_faiss_index(texts):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts)
    dimension = len(embeddings[0])

    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(np.array(embeddings))
    
    return faiss_index, model, embeddings

def calculate_similarity(faiss_index, query_embedding, k):
    D, I = faiss_index.search(np.array([query_embedding]), k=k)
    return I[0], D[0]

def calculate_percentage_similarity(scores):
    return [1 / (1 + score / 1.7) * 100 for score in scores]

def main():
    df = pd.read_csv('bug_reports.csv')
    df['text'] = df['Title'].fillna('') + ' ' + df['Description'].fillna('')

    issue_ids = df['Issue_id'].tolist()
    texts = df['text'].tolist()

    faiss_index, model, embeddings = create_faiss_index(texts)

    result_rows = []

    for idx, (issue_id, text) in tqdm(enumerate(zip(issue_ids, texts)), total=len(texts)):
        query_embedding = embeddings[idx]
        I, D = calculate_similarity(faiss_index, query_embedding, k=len(texts))

        # Skip the first result if it's the query itself
        similar_indices = [i for i in I if i != idx][:5]
        distances = [d for i, d in zip(I, D) if i != idx][:5]
        similarities = calculate_percentage_similarity(distances)

        row = {'Issue_id': issue_id}
        for i, (sim_id, sim_score) in enumerate(zip(similar_indices, similarities), start=1):
            row[f'Similar_issue_id_{i}'] = issue_ids[sim_id]
            row[f'Similarity_{i}'] = round(sim_score, 2)
        
        result_rows.append(row)

    result_df = pd.DataFrame(result_rows)
    result_df.to_csv('similarity_results.csv', index=False)

if __name__ == '__main__':
    main()
