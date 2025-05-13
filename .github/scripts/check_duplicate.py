import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import requests
from backend.app.gemini_validation import validate_similarity_with_gemini
from backend.app.text_similarity import create_faiss_index, calculate_similarity, calculate_percentage_similarity

# 🔧 CONFIGURABLE WEIGHTS
TITLE_WEIGHT = 0.6
BODY_WEIGHT = 0.4

def weighted_text(title: str, body: str, title_weight: float = TITLE_WEIGHT, body_weight: float = BODY_WEIGHT):
    title = title or ""
    body = body or ""
    return f"{(title + ' ') * int(title_weight * 10)} {(body + ' ') * int(body_weight * 10)}"

# 🌍 Load environment variables
issue_title = os.getenv("ISSUE_TITLE") or ""
issue_number = os.getenv("ISSUE_NUMBER")
repo = os.getenv("REPO")
token = os.getenv("GH_TOKEN")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json"
}

comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"

# Step 1: Fetch all issues
r = requests.get(f"https://api.github.com/repos/{repo}/issues", headers=headers)
issues = r.json()

# Step 2: Filter issues
filtered_issues = [
    (i.get("title", ""), i["number"], i.get("body", ""))
    for i in issues
    if str(i["number"]) != issue_number
]

if not filtered_issues:
    requests.post(comment_url, headers=headers, json={"body": "ℹ️ No other issues found to compare."})
    exit(0)

# Step 3: Prepare FAISS input
combined_texts = [weighted_text(title, body) for title, _, body in filtered_issues]
faiss_index, model = create_faiss_index(combined_texts)

# Step 4: Prepare current issue query
current_issue = next((i for i in issues if str(i["number"]) == issue_number), {})
issue_body = current_issue.get("body", "")
if not issue_body.strip():
    issue_body = "(no description provided)"
query_text = weighted_text(issue_title, issue_body)

# Step 5: Similarity search
results = calculate_similarity(faiss_index, model, combined_texts, query_text)
scores = [score for _, score in results]
percentage_similarities = calculate_percentage_similarity(scores)

# Step 6: Top matches
top_n = 3
top_results = results[:top_n]
top_scores = percentage_similarities[:top_n]

similar_issues = []
for (text, _), score in zip(top_results, top_scores):
    match = next(((title, num, body) for (title, num, body), w_text in zip(filtered_issues, combined_texts) if weighted_text(title, body) == text), None)
    if match:
        title, number, body = match
        similar_issues.append({
            "title": title,
            "body": body,
            "score": score
        })

gemini_response = validate_similarity_with_gemini(issue_title, issue_body, similar_issues)

# Step 7: Prepare comment
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

    for i, (text, _) in enumerate(results[:5]):
        percentage = percentage_similarities[i]
        if percentage < 70.0:
            continue

        match = next(((title, num) for (title, num, body), w_text in zip(filtered_issues, combined_texts) if weighted_text(title, body) == text), None)
        if not match:
            continue
        title, issue_index = match
        title_link = f"https://github.com/{repo}/issues/{issue_index}"
        safe_title = title.replace("|", "｜")  # escape pipe
        base_comment += f"| [#{issue_index}]({title_link}) | {safe_title} | {percentage:.0f}% |\n"

    base_comment += (
        "\n📌 Label `needs-duplicate-review` has been added.\n"
        "\n🔧 Maintainers can confirm by commenting:\n"
        "```bash\n/mark-duplicate #<issue_number>\n```"
    )

    # Label it
    label_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels"
    requests.post(label_url, headers=headers, json={"labels": ["needs-duplicate-review"]})

else:
    base_comment += "✅ No strong duplicate candidates found. You may proceed."

base_comment += f"\n\n🧠 **Gemini Review**\n```\n{gemini_response}\n```"

# Step 8: Post final comment
requests.post(comment_url, headers=headers, json={"body": base_comment})
