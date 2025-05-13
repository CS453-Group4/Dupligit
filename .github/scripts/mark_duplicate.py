import os
import re
import requests

# 🌍 Environment variables from GitHub Actions
token = os.getenv("GH_TOKEN")
repo = os.getenv("REPO")
comment_body = os.getenv("ISSUE_BODY")  # e.g. /mark-duplicate #46
comment_author = os.getenv("COMMENT_AUTHOR")
commented_issue_number = os.getenv("ISSUE_NUMBER")  # Issue where the comment was posted

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
    url = f"https://api.github.com/repos/{repo}/issues/{issue_num}/comments"
    requests.post(url, headers=headers, json={"body": body})

# --- Step 1: Parse command ---
match = re.match(r"/mark-duplicate\s+#(\d+)", (comment_body or "").strip())
if not match:
    comment_on_issue(commented_issue_number, "❌ Invalid format. Use `/mark-duplicate #<issue_number>`.")
    exit(1)

target_issue_number = match.group(1)  # This is the one that should be closed

# --- Step 2: Auth Check ---
if not is_authorized_user(comment_author):
    comment_on_issue(commented_issue_number, f"🚫 Sorry @{comment_author}, you are not authorized to mark duplicates.")
    exit(1)

# 💬 Say you're starting
comment_on_issue(commented_issue_number, f"🔁 Attempting to close issue #{target_issue_number} as a duplicate...")

try:
    # --- Step 3: Add 'duplicate' label to target issue ---
    label_url = f"https://api.github.com/repos/{repo}/issues/{target_issue_number}/labels"
    label_response = requests.post(label_url, headers=headers, json={"labels": ["duplicate"]})

    if label_response.status_code != 200:
        comment_on_issue(commented_issue_number, f"⚠️ Could not add `duplicate` label to #{target_issue_number}. Status: {label_response.status_code}")

    # --- Step 4: Close the target issue ---
    close_url = f"https://api.github.com/repos/{repo}/issues/{target_issue_number}"
    close_response = requests.patch(close_url, headers=headers, json={"state": "closed"})

    if close_response.status_code == 200:
        comment_on_issue(commented_issue_number, (
            f"✅ Successfully marked issue [#{target_issue_number}](https://github.com/{repo}/issues/{target_issue_number}) as duplicate and closed it.\n\n"
            f"Thanks @{comment_author}!"
        ))
    else:
        comment_on_issue(commented_issue_number, (
            f"⚠️ Tried to close issue [#{target_issue_number}](https://github.com/{repo}/issues/{target_issue_number}) "
            f"but got status code {close_response.status_code}."
        ))

except Exception as e:
    comment_on_issue(commented_issue_number, f"🚨 Error occurred while marking duplicate: `{str(e)}`")
    exit(1)
