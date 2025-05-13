import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def create_faiss_index(texts):
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    embeddings = model.encode(texts)
    dimension = len(embeddings[0])

    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(np.array(embeddings))
    
    return faiss_index, embeddings

def calculate_similarity(faiss_index, query_embedding, k):
    D, I = faiss_index.search(np.array([query_embedding]), k=k)
    return I[0], D[0]

def calculate_percentage_similarity(scores):
    return [1 / (1 + score / 1.7) * 100 for score in scores]