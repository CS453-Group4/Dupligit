import os
import requests

def validate_similarity_with_gemini(issue_title, issue_body, similar_issues):
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    prompt = f"""You are an expert in software QA and duplicate issue detection.

The newly created GitHub issue is:
Title: {issue_title}
Description: {issue_body}

Here are potentially similar issues detected automatically:
"""

    for idx, issue in enumerate(similar_issues, 1):
        prompt += f"\n{idx}. Title: {issue['title']}\n   Description: {issue['body']}\n   Similarity Score: {issue['score']:.2f}%"

    prompt += """
Evaluate whether each similarity score is justified. For each, say whether the score is 'Correct', 'Too High', or 'Too Low', and briefly explain why.

Reply using this format:
[
  {
    "original_issue_title": "...",
    "matched_issue_title": "...",
    "score": ...,
    "verdict": "...",
    "reason": "..."
  },
  ...
]
"""

    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(url, json=body)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Gemini validation failed: {str(e)}"
