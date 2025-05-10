import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import requests
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.app.gemini_validation import validate_similarity_with_gemini

from backend.app.text_sim_csv import create_faiss_index
from backend.app.text_similarity import calculate_similarity

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
model = SentenceTransformer("all-MiniLM-L6-v2")
faiss_index, _ = create_faiss_index(titles, model)
results = calculate_similarity(faiss_index, model, titles, issue_title)
scores = [score for _, score in results]

percentage_similarities = calculate_percentage_similarity(scores)
# 🔍 Prepare Gemini input
current_issue = next((i for i in issues if str(i["number"]) == issue_number), {})
issue_body = current_issue.get("body", "")

top_n = 3
top_results = results[:top_n]
top_scores = percentage_similarities[:top_n]

similar_issues = []
for (title, _), score in zip(top_results, top_scores):
    matched = next((i for i in issues if i["title"] == title), {})
    similar_issues.append({
        "title": matched.get("title", ""),
        "body": matched.get("body", ""),
        "score": score
    })

gemini_response = validate_similarity_with_gemini(issue_title, issue_body, similar_issues)


base_comment = (
    f"🔍 **Dupligit Bot Report**\n\n"
    f"📝 Incoming Issue: _{issue_title}_\n\n"
)

if percentage_similarities[0] > 70.0:
    base_comment += (
        "🔍 **Potential Duplicate Issues Found**\n\n"
        "We've detected similar issues to this one:\n\n"
        "| Issue # | Title | Similarity |\n"
        "|---------|-------|------------|\n"
    )

    for i, (title, _) in enumerate(results[:5]):
        percentage = percentage_similarities[i]
        if percentage < 70.0:
            continue

        issue_index = titles.index(title) + 1  # Approximation (may need adjustment if order differs)
        title_link = f"https://github.com/{repo}/issues/{issue_index}"
        safe_title = title.replace("|", "｜")  # escape markdown pipe
        base_comment += f"| [#{issue_index}]({title_link}) | {safe_title} | {percentage:.0f}% |\n"

    base_comment += (
        "\n📌 Label `needs-duplicate-review` has been added.\n"
        "\n🔧 Maintainers can confirm by commenting:\n"
        "```bash\n/mark-duplicate #<issue_number>\n```"
    )

    # Step 4: Add label
    label_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels"
    requests.post(label_url, headers=headers, json={"labels": ["needs-duplicate-review"]})

else:
    base_comment += "✅ No strong duplicate candidates found. You may proceed."

base_comment += f"\n\n🧠 **Gemini Review**\n```\n{gemini_response}\n```"

# Step 5: Post final comment
requests.post(comment_url, headers=headers, json={"body": base_comment})