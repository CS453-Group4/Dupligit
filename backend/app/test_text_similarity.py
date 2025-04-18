import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.text_similarity import create_faiss_index, calculate_similarity

def test_similarity_logic():
    texts = [
        "App crashes on profile click",
        "Login fails with wrong password",
        "Image upload silently fails",
        "App freezes on login"
    ]
    query = "Login screen freezes when password is incorrect"

    faiss_index, model = create_faiss_index(texts)
    most_similar_text, similarity_score = calculate_similarity(faiss_index, model, texts, query)

    assert most_similar_text in texts
    assert similarity_score < 5.0  # Düşük L2 mesafesi = yüksek benzerlik
