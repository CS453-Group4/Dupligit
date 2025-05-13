import os
import re
import requests

# 🌍 Environment variables from GitHub Actions
token = os.getenv("GH_TOKEN")
repo = os.getenv("REPO")
comment_body = os.getenv("ISSUE_BODY")
comment_issue_number = os.getenv("ISSUE_NUMBER")  # the issue where the comment was posted
comment_author = os.getenv("COMMENT_AUTHOR")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json"
}

def is_authorized_user(username):
    url = f"https://api.github.com/repos/{repo}/collaborators/{username}/permission"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"⚠️ Could not fetch permission info for user {username}. Status code: {resp.status_code}")
        return False
    permission = resp.json().get("permission", "")
    print(f"🔍 User '{username}' has GitHub permission: '{permission}'")
    return permission in ["admin", "maintain", "write"]

def comment_on_issue(issue_num, body):
    comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_num}/comments"
    requests.post(comment_url, headers=headers, json={"body": body})

# --- Step 1: Parse the command ---
match = re.match(r"/mark-duplicate\s+#(\d+)", comment_body.strip())

if not match:
    print("❌ Command format not recognized. Expected '/mark-duplicate #<issue_number>'")
    exit(0)

duplicate_issue_number = match.group(1)  # The issue that will be CLOSED (e.g. #65)

# --- Step 2: Check authorization ---
if not is_authorized_user(comment_author):
    comment_on_issue(comment_issue_number, f"🚫 Sorry @{comment_author}, you are not authorized to mark issues as duplicates.")
    exit(1)

# --- Step 3: Add 'duplicate' label to the issue being closed ---
label_url = f"https://api.github.com/repos/{repo}/issues/{duplicate_issue_number}/labels"
requests.post(label_url, headers=headers, json={"labels": ["duplicate"]})

# --- Step 4: Post confirmation on the issue being closed ---
confirmation_comment = (
    f"✅ Marked as duplicate of [#{comment_issue_number}](https://github.com/{repo}/issues/{comment_issue_number}) by @{comment_author}.\n\n"
    f"🔒 Closing this issue to avoid duplication. Please refer to the main issue for future updates."
)
comment_on_issue(duplicate_issue_number, confirmation_comment)

# --- Step 5: Close the duplicate issue ---
close_url = f"https://api.github.com/repos/{repo}/issues/{duplicate_issue_number}"
requests.patch(close_url, headers=headers, json={"state": "closed"})

print(f"✅ Issue #{duplicate_issue_number} closed as duplicate of #{comment_issue_number}")
