import os
import re
import requests

# Environment variables passed from the workflow
token = os.getenv("GH_TOKEN")
repo = os.getenv("REPO")
comment_body = os.getenv("ISSUE_BODY")
issue_number = os.getenv("ISSUE_NUMBER")
comment_author = os.getenv("COMMENT_AUTHOR")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json"
}

def is_authorized_user(username):
    """
    Check GitHub permission for the user.
    Only 'admin', 'maintain', or 'write' roles are authorized.
    """
    url = f"https://api.github.com/repos/{repo}/collaborators/{username}/permission"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        print(f"⚠️ Could not fetch permission info for user {username}. Status code: {resp.status_code}")
        return False

    permission = resp.json().get("permission", "")
    print(f"🔍 User '{username}' has GitHub permission: '{permission}'")
    return permission in ["admin", "maintain", "write"]

def comment_on_issue(body):
    """
    Post a comment to the issue.
    """
    comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    requests.post(comment_url, headers=headers, json={"body": body})

# --- Step 1: Parse the command ---
match = re.match(r"/mark-duplicate\s+#(\d+)", comment_body.strip())

if not match:
    print("❌ Command format not recognized. Expected '/mark-duplicate #<issue_number>'")
    exit(0)

duplicate_of = match.group(1)

# --- Step 2: Check authorization ---
if not is_authorized_user(comment_author):
    comment_on_issue(f"🚫 Sorry @{comment_author}, you are not authorized to mark issues as duplicates. Only team leads or maintainers can perform this action.")
    exit(1)

# --- Step 3: Add 'duplicate' label ---
label_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels"
requests.post(label_url, headers=headers, json={"labels": ["duplicate"]})

# --- Step 4: Post confirmation comment ---
comment_on_issue(
    f"✅ Marked as duplicate of #{duplicate_of} by @{comment_author}.\n\n"
    f"🔒 Closing this issue to avoid duplication. Please refer to the main issue for future updates."
)

# --- Step 5: Close the issue ---
close_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
requests.patch(close_url, headers=headers, json={"state": "closed"})

print(f"✅ Issue #{issue_number} closed as duplicate of #{duplicate_of}")
