import os
import requests
import json

os.environ["GEMINI_API_KEY"] = "AIzaSyB2GRhfzc2Mb1O4kizah9FwU-lvSIQ7AIg"

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
        body = (issue.get('body') or '').strip().replace("\n", " ")[:300]

        prompt += f"\n{idx}. Title: {issue['title']}\n   Description: {body}\n   Similarity Score: {issue['score']:.2f}%"

    prompt += """
    Reply ONLY with this exact JSON format:
    [
    {
        "matched_issue_title": "...",
        "verdict": "Correct" or "False"
    },
    ...
    ]

    ⚠️ Do NOT explain. Do NOT summarize. Just return the raw JSON list. If none are valid, return [].
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
        print("🧠 Gemini Raw Output Text:")
        print(gemini_text)

        # ✅ Strip ```json ... ``` block if it exists
        if gemini_text.strip().startswith("```json"):
            gemini_text = gemini_text.strip()[7:-3].strip()  # remove ```json and ```

        try:
            parsed = json.loads(gemini_text)
            return parsed
        except json.JSONDecodeError as e:
            print("⚠️ Gemini response could not be parsed as JSON.")
            print("⚠️ Error:", e)
            return []


    except Exception as e:
        return []  #

def validate_similarity_with_gemini_test_dataset(issue_body, similar_issues):
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    prompt = f"""You are an expert in software QA and duplicate issue detection.

    The newly created GitHub issue is:
    Description: {issue_body}

    Here are potentially similar issues detected automatically:
    """

    for idx, issue in enumerate(similar_issues, 1):
        body = (issue.get('body') or '').strip().replace("\n", " ")[:300]
        prompt += f"\n{idx}. Description: {body}"

    prompt += """
    Reply ONLY with this exact JSON format:
    [
    {
        "matched_issue_index": <index from list above>,
        "verdict": "Correct" or "False"
    },
    ...
    ]

    ⚠️ Do NOT explain. Do NOT summarize. Just return the raw JSON list. If none are valid, return []."""

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
        print("🧠 Gemini Raw Output Text:")
        print(gemini_text)

        if gemini_text.strip().startswith("```json"):
            gemini_text = gemini_text.strip()[7:-3].strip()

        try:
            parsed = json.loads(gemini_text)
            return parsed
        except json.JSONDecodeError as e:
            print("⚠️ Gemini response could not be parsed as JSON.")
            print("⚠️ Error:", e)
            return []

    except Exception as e:
        print("⚠️ Request failed:", e)
        return []
