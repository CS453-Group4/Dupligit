import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

def create_faiss_index(texts):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts)
    dimension = len(embeddings[0])

    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(np.array(embeddings))
    
    return faiss_index, model

def calculate_similarity(faiss_index, model, texts, query_text):
    query_embedding = model.encode(query_text)
    D, I = faiss_index.search(np.array([query_embedding]), k=len(texts))

    results = []
    for i, d in zip(I[0], D[0]):
        results.append((texts[i], d))
    
    return results

def calculate_percentage_similarity(scores):
    return [1 / (1 + score/1.7) * 100 for score in scores]
