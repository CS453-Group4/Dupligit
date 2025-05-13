import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import requests
from backend.app.gemini_validation import validate_similarity_with_gemini
from backend.app.text_similarity import create_faiss_index, calculate_similarity, calculate_percentage_similarity


# Load environment variables
issue_title = os.getenv("ISSUE_TITLE") or ""
issue_number = os.getenv("ISSUE_NUMBER")
repo = os.getenv("REPO")
token = os.getenv("GH_TOKEN")

# ✅ Validate required envs
required_envs = {
    "REPO": repo,
    "GH_TOKEN": token,
    "ISSUE_NUMBER": issue_number,
    "ISSUE_TITLE": issue_title
}

for key, val in required_envs.items():
    if not val:
        print(f"❌ Missing environment variable: {key}")
        exit(1)



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

try:
    issues = r.json()
except Exception as e:
    print("❌ Failed to parse JSON from GitHub issues response")
    print("🔁 Raw response:", r.text)
    raise e

if not isinstance(issues, list):
    print("❌ GitHub API did not return a list of issues")
    print("🔁 Response:", issues)
    exit(1)

print("🧪 All issues fetched:")
for i in issues:
    print(f"- #{i['number']}: {i['title']}")


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
print("Top FAISS results:")
for i, (text, score) in enumerate(results[:5]):
    print(f"{i+1}. Score: {score}")

scores = [score for _, score in results]
percentage_similarities = calculate_percentage_similarity(scores)

# Step 6: Top matches
top_n = 20
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
            "score": float(score)  
        })

print("🔬 Gemini INPUT DEBUG:")
print("issue_title:", issue_title)
print("issue_body:", issue_body)
print("similar_issues:", similar_issues)
gemini_response = validate_similarity_with_gemini(issue_title, issue_body, similar_issues)
print("🧠 Gemini Parsed Response:")
print(json.dumps(gemini_response, indent=2))


filtered_similar_issues = []
for issue in similar_issues:
    verdict = next((v for v in gemini_response if v["matched_issue_title"] == issue["title"]), None)
    if verdict and verdict["verdict"].lower() == "correct":
        filtered_similar_issues.append(issue)
filtered_similar_issues = filtered_similar_issues[:5]
print("✅ Gemini-approved duplicates:")
for i in filtered_similar_issues:
    print(f"- {i['title']} ({i['score']:.1f}%)")


# Step 7: Prepare comment
base_comment = (
    f"**Dupligit Bot Report**\n\n"
    f"Issue under review: *{issue_title}*\n\n"
)

if filtered_similar_issues:
    base_comment += (
        " **Potential Duplicate Issues Found**\n\n"
        "We've detected similar issues to this one:\n\n"
        "| Issue # | Title | Similarity |\n"
        "|---------|-------|------------|\n"
    )
    for issue in filtered_similar_issues:
        ...
        base_comment += f"| [#{issue_index}]({title_link}) | {safe_title} | {score:.0f}% |\n"

    base_comment += (
        "\n📌 Label `needs-duplicate-review` has been added.\n"
        "\n🔧 Maintainers can confirm by commenting:\n"
        "```bash\n/mark-duplicate #<issue_number>\n```"
    )

    # ✅ Add label
    label_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels"
    requests.post(label_url, headers=headers, json={"labels": ["needs-duplicate-review"]})
else:
    base_comment += "✅ No strong duplicate candidates were confirmed by Gemini.\n"
    base_comment += "You may proceed or wait for human triage.\n"

# ✅ Always post the comment
print("📝 Posting final comment:")
print(base_comment)

requests.post(comment_url, headers=headers, json={"body": base_comment})
