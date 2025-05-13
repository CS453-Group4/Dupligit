import os
import re
import requests

# 🌍 Environment variables from GitHub Actions
token = os.getenv("GH_TOKEN")
repo = os.getenv("REPO")
comment_body = os.getenv("ISSUE_BODY")
comment_author = os.getenv("COMMENT_AUTHOR")
duplicate_number = os.getenv("ISSUE_NUMBER")  # Issue where the comment was made

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

# --- Step 1: Parse the command ---
match = re.match(r"/mark-duplicate\s+#(\d+)", (comment_body or "").strip())
if not match:
    comment_on_issue(duplicate_number, "❌ Invalid command format. Use `/mark-duplicate #<issue_number>`.")
    exit(1)

target_issue = match.group(1)

# --- Step 2: Authorization Check ---
if not is_authorized_user(comment_author):
    comment_on_issue(duplicate_number, f"🚫 Sorry @{comment_author}, you are not authorized to mark issues as duplicates.")
    exit(1)

try:
    # 💬 Inform user we're beginning the process
    comment_on_issue(duplicate_number, f"🔁 Attempting to mark this issue as duplicate of #{target_issue}...")

    # --- Step 3: Add label ---
    label_url = f"https://api.github.com/repos/{repo}/issues/{duplicate_number}/labels"
    label_response = requests.post(label_url, headers=headers, json={"labels": ["duplicate"]})

    if label_response.status_code != 200:
        comment_on_issue(duplicate_number, f"⚠️ Could not add `duplicate` label. Status: {label_response.status_code}")

    # --- Step 4: Close the duplicate issue ---
    close_url = f"https://api.github.com/repos/{repo}/issues/{duplicate_number}"
    close_response = requests.patch(close_url, headers=headers, json={"state": "closed"})

    if close_response.status_code == 200:
        comment_on_issue(duplicate_number, (
            f"✅ Successfully marked this issue as a duplicate of [#{target_issue}](https://github.com/{repo}/issues/{target_issue}) "
            f"and closed it.\n\n"
            f"Thanks @{comment_author}!"
        ))
    else:
        comment_on_issue(duplicate_number, (
            f"⚠️ Tried to close this issue as a duplicate of [#{target_issue}](https://github.com/{repo}/issues/{target_issue}) "
            f"but got status code {close_response.status_code}."
        ))

except Exception as e:
    comment_on_issue(duplicate_number, f"🚨 Unexpected error occurred while marking duplicate: `{str(e)}`")
    exit(1)
