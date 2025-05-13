import os
import re
import requests

# 🌍 Environment variables from GitHub Actions
token = os.getenv("GH_TOKEN")
repo = os.getenv("REPO")
comment_body = os.getenv("ISSUE_BODY")
duplicate_number = os.getenv("ISSUE_NUMBER")  # The issue where the comment was posted
comment_author = os.getenv("COMMENT_AUTHOR")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json"
}

def is_authorized_user(username):
    url = f"https://api.github.com/repos/{repo}/collaborators/{username}/permission"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return False
    permission = resp.json().get("permission", "")
    return permission in ["admin", "maintain", "write"]

def comment_on_issue(issue_num, body):
    comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_num}/comments"
    requests.post(comment_url, headers=headers, json={"body": body})

# --- Step 1: Parse the command ---
match = re.match(r"/mark-duplicate\s+#(\d+)", comment_body.strip())
if not match:
    comment_on_issue(duplicate_number, "❌ Invalid command format. Use `/mark-duplicate #<issue_number>`.")
    exit(1)

duplicate_of = match.group(1)

# --- Step 2: Authorization Check ---
if not is_authorized_user(comment_author):
    comment_on_issue(duplicate_number, f"🚫 Sorry @{comment_author}, you are not authorized to mark issues as duplicates.")
    exit(1)

try:
    # --- Step 3: Add Label ---
    label_url = f"https://api.github.com/repos/{repo}/issues/{duplicate_number}/labels"
    requests.post(label_url, headers=headers, json={"labels": ["duplicate"]})

    # --- Step 4: Comment before closing ---
    comment_on_issue(duplicate_number, f"🛑 Issue is being closed as a duplicate of [#{duplicate_of}](https://github.com/{repo}/issues/{duplicate_of}) by @{comment_author}.")

    # --- Step 5: Close Issue ---
    close_url = f"https://api.github.com/repos/{repo}/issues/{duplicate_number}"
    response = requests.patch(close_url, headers=headers, json={"state": "closed"})

    if response.status_code == 200:
        comment_on_issue(duplicate_number, f"✅ Issue #{duplicate_number} successfully closed as a duplicate of #{duplicate_of}.")
    else:
        comment_on_issue(duplicate_number, f"⚠️ Attempted to close issue but failed with status code: {response.status_code}")

except Exception as e:
    comment_on_issue(duplicate_number, f"🚨 An error occurred while marking the duplicate: `{str(e)}`")
    exit(1)
