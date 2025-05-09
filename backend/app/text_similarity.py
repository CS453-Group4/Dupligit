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

def main():
    texts = [
        "When I try to push my branch, I keep getting a 403 error. I’ve confirmed I have write access, so I’m not sure what’s wrong.",
        "The build pipeline fails after I merged my PR. It says something about missing secrets. This didn’t happen before.",
        "Unable to clone the repository using SSH. I’ve added my SSH key but still get a permission denied error.",
        "I'm experiencing issues with pushing to the repository. I get a permission error even though I’ve authenticated with a personal access token.",
        "I think the README could be clearer about how to install dependencies. A section on system requirements would help too."
    ]
    query_text = "I can’t push to the repo — I get a permission denied error, even though my credentials are correct."

    faiss_index, model = create_faiss_index(texts)

    results = calculate_similarity(faiss_index, model, texts, query_text)
    scores = [score for _, score in results]

    percentage_similarities = calculate_percentage_similarity(scores)

    print("\nSimilarity Results (lower = more similar):\n")
    for rank, (text, percentage_similarity) in enumerate(zip(results, percentage_similarities), 1):
        print(f"{rank}. Similarity: {percentage_similarity:.2f}%")
        print(f"   → {text[0]}\n")

if __name__ == "__main__":
    main()
