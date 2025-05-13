import os
import re
import requests

# Environment variables
token = os.getenv("GH_TOKEN")
repo = os.getenv("REPO")
comment_body = os.getenv("ISSUE_BODY")  # the comment content, e.g. "/mark-duplicate #39"
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
    url = f"https://api.github.com/repos/{repo}/issues/{issue_num}/comments"
    requests.post(url, headers=headers, json={"body": body})

# Step 1: Parse the target issue number from the comment
match = re.match(r"/mark-duplicate\s+#(\d+)", comment_body.strip())
if not match:
    print("❌ Invalid command format.")
    exit(1)

target_issue = match.group(1)  # This is the issue that should be closed as duplicate

# Step 2: Auth check
if not is_authorized_user(comment_author):
    comment_on_issue(target_issue, f"🚫 @{comment_author}, you are not authorized to mark duplicates.")
    exit(1)

try:
    # Step 3: Add 'duplicate' label to the target
    label_url = f"https://api.github.com/repos/{repo}/issues/{target_issue}/labels"
    requests.post(label_url, headers=headers, json={"labels": ["duplicate"]})

    # Step 4: Notify and close
    comment_on_issue(target_issue, f"✅ Marked as duplicate by @{comment_author}. Closing issue.")
    close_url = f"https://api.github.com/repos/{repo}/issues/{target_issue}"
    r = requests.patch(close_url, headers=headers, json={"state": "closed"})

    if r.status_code == 200:
        comment_on_issue(target_issue, f"🔒 Issue #{target_issue} closed successfully.")
    else:
        comment_on_issue(target_issue, f"⚠️ Failed to close issue. Status code: {r.status_code}")

except Exception as e:
    comment_on_issue(target_issue, f"❌ Error while closing issue #{target_issue}: `{str(e)}`")
    exit(1)
