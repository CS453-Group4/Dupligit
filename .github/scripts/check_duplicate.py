import os
import requests
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# ENV from GitHub Actions
issue_title = os.getenv("ISSUE_TITLE")
issue_number = os.getenv("ISSUE_NUMBER")
repo = os.getenv("REPO")
token = os.getenv("GH_TOKEN")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json"
}

# Step 1: Fetch existing issues
r = requests.get(f"https://api.github.com/repos/{repo}/issues", headers=headers)
issues = r.json()
titles = [i["title"] for i in issues if str(i["number"]) != issue_number]

if not titles:
    print("No other issues to compare.")
    exit(0)

# Step 2: FAISS comparison
embeddings = model.encode(titles)
query = model.encode([issue_title])

index = faiss.IndexFlatL2(len(query[0]))
index.add(np.array(embeddings))

D, I = index.search(np.array(query), k=1)

most_similar_title = titles[I[0][0]]
score = D[0][0]

# Step 3: Comment if similar
if score < 10.0:
    comment_body = (
        f"🤖 **Possible duplicate found!**\n\n"
        f"> _{most_similar_title}_\n"
        f"🔍 Similarity Score: `{score:.2f}`\n"
        f"_This issue is now under duplicate review._"
    )

    comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    r = requests.post(comment_url, headers=headers, json={"body": comment_body})
    print("Commented:", r.status_code)
else:
    print("No strong duplicate found.")
