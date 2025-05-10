import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import requests
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.text_sim_csv import calculate_similarity, create_faiss_index
from backend.app.text_similarity import calculate_percentage_similarity

issue_title = os.getenv("ISSUE_TITLE")
issue_number = os.getenv("ISSUE_NUMBER")
repo = os.getenv("REPO")
token = os.getenv("GH_TOKEN")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json"
}
# Notify the user that the bot is running
comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
"""comment_payload = {"body": "🔍 Dupligit Bot is checking for similar issues. Please wait..."}
resp = requests.post(comment_url, headers=headers, json=comment_payload)

# DEBUG OUTPUT
print("🧪 DEBUG: Comment POST status:", resp.status_code)
print("🧪 DEBUG: Comment POST response:", resp.text)"""

# Step 1: Fetch all other issue titles
r = requests.get(f"https://api.github.com/repos/{repo}/issues", headers=headers)
issues = r.json()
titles = [i["title"] for i in issues if str(i["number"]) != issue_number]

if not titles:
    requests.post(comment_url, headers=headers, json={"body": "ℹ️ No other issues found to compare."})
    exit(0)

# Step 2: Create FAISS index and calculate similarity
faiss_index, model = create_faiss_index(titles)
results = calculate_similarity(faiss_index, model, titles, issue_title)
scores = [score for _, score in results]

percentage_similarities = calculate_percentage_similarity(scores)

base_comment = (
    f"🔍 **Dupligit Bot Report**\n\n"
    f"📝 Incoming Issue: _{issue_title}_\n\n"
)

if percentage_similarities[0] > 70.0:  # Changed to percentage similarity threshold
    most_similar_title = results[0][0]
    score = percentage_similarities[0]
    
    # Find the index of the most similar issue from the results list
    most_similar_index = titles.index(most_similar_title)

    base_comment += (
        f"🤖 This might be a duplicate of:\n> _{most_similar_title}_\n"
        f"🧠 Similarity Score: `{score:.2f}%`\n"
        f"\n📌 Label `needs-duplicate-review` has been added.\n"
        f"\n🔧 Maintainers can confirm by commenting:\n"
        f"```bash\n/mark-duplicate #{most_similar_index + 1}\n```"
    )

    # Step 4: Add label
    label_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels"
    requests.post(label_url, headers=headers, json={"labels": ["needs-duplicate-review"]})
else:
    base_comment += "✅ No strong duplicate candidates found. You may proceed."

# Step 5: Post final comment
requests.post(comment_url, headers=headers, json={"body": base_comment})