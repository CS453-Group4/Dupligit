import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

def create_faiss_index(sentences, model):
    # Convert sentences to embeddings
    embeddings = model.encode(sentences)
    
    # Create FAISS index
    dimension = len(embeddings[0])
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(np.array(embeddings))
    
    return faiss_index, embeddings

def calculate_similarity(embedding1, embedding2):
    # Compute L2 distance (lower is more similar)
    return np.linalg.norm(embedding1 - embedding2)

def process_csv(input_csv, output_csv):
    # Load the dataset
    df = pd.read_csv(input_csv)
    
    # Initialize the SentenceTransformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Compute embeddings for all text pairs
    df['embedding1'] = df['text1'].apply(lambda x: model.encode(x))
    df['embedding2'] = df['text2'].apply(lambda x: model.encode(x))
    
    # Compute similarity scores
    df['similarity_score'] = df.apply(lambda row: calculate_similarity(row['embedding1'], row['embedding2']), axis=1)
    
    # Sort by similarity score (ascending: most similar at the top)
    df = df.sort_values(by='similarity_score')
    
    # Drop embeddings before saving
    df = df[['text1', 'text2', 'similarity_score']]
    
    # Save to new CSV
    df.to_csv(output_csv, index=False)
    print(f"Sorted results saved to {output_csv}")

if __name__ == "__main__":
    input_csv = "Text_Similarity_Dataset.csv"  # Replace with your actual file name
    output_csv = "sorted_similarity.csv"
    process_csv(input_csv, output_csv)
