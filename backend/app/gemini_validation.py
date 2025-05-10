
import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-pro")

def validate_similarity_with_gemini(issue_title, issue_body, similar_issues):
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

    try:
        response = model.generate_content(prompt)
        return response.text  # Raw JSON-like string from Gemini
    except Exception as e:
        return f"Gemini validation failed: {str(e)}"
