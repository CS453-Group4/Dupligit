from fastapi import FastAPI
from pydantic import BaseModel
from backend.app.text_similarity import create_faiss_index, calculate_similarity

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

#for now mock data
PAST_ISSUES = [
    "App crashes on profile click",
    "Login fails with wrong password",
    "Image upload silently fails",
    "App freezes on login",
    "Unable to reset password on mobile",
    "Clicking save does nothing in profile settings"
]

class Query(BaseModel):
    text: str

@app.post("/predict")
def predict(query: Query):
    faiss_index, model = create_faiss_index(PAST_ISSUES)
    similar_issue, score = calculate_similarity(faiss_index, model, PAST_ISSUES, query.text)
    return {
        "query": query.text,
        "most_similar": similar_issue,
        "similarity_score": score
    }
