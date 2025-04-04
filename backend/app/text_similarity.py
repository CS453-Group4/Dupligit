import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

def create_faiss_index(texts):
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Convert texts to embeddings
    embeddings = model.encode(texts)

    # Create FAISS index
    dimension = len(embeddings[0])
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(np.array(embeddings))
    
    return faiss_index, model

def calculate_similarity(faiss_index, model, texts, query_text):
    # Convert query text (multi-sentence) to an embedding
    query_embedding = model.encode(query_text)

    # Perform search in FAISS index
    D, I = faiss_index.search(np.array([query_embedding]), k=1)

    # Return the most similar text and its similarity score
    return texts[I[0][0]], D[0][0]

def main():
    # Create and initialize the FAISS index
    faiss_index, model, texts = create_faiss_index()

    # Example multi-sentence query
    query_text = "The login page freezes when I enter incorrect details. The only fix is to refresh."

    # Find the most similar issue
    most_similar_text, similarity_score = calculate_similarity(faiss_index, model, texts, query_text)

    print(f"Most Similar Issue: {most_similar_text}")
    print(f"Similarity Score (lower is more similar): {similarity_score}")

if __name__ == "__main__":
    main()
