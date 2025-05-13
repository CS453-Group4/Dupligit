import os
import requests
import json

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
    For each detected similar issue, decide whether it is truly a duplicate of the main issue.

    Reply using this exact JSON format:
    [
    {
        "matched_issue_title": "...",
        "verdict": "Correct" or "False"
    }
    ]

    Only return this JSON. Do not add any explanations or extra text.
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
        gemini_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(gemini_text)
        return parsed

    except Exception as e:
        return []  #
