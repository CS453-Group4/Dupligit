# Dupligit Action 🤖

Detect and mark duplicate GitHub issues using semantic embeddings and LLM validation.

## ✅ Features

- Detects similar issues on `issues.opened`
- Lets maintainers confirm duplicates via `/mark-duplicate`
- Powered by Gemini/OpenAI + FAISS + Python

## 🛠️ Setup

1. Add this to your repo's `.github/workflows/dupligit.yml`:

```yaml
name: Dupligit Bot

on:
  issues:
    types: [opened]
  issue_comment:
    types: [created]

permissions:
  contents: read
  issues: write

jobs:
  check-duplicate:
    if: github.event_name == 'issues'
    runs-on: ubuntu-latest
    steps:
      - name: Run Dupligit Check
        uses: CS453-Group4/Dupligit@v1.0.7
        with:
          mode: check
          issue-title: ${{ github.event.issue.title }}
          issue-number: ${{ github.event.issue.number }}
          repo: ${{ github.repository }}
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  mark-duplicate:
    if: |
      github.event_name == 'issue_comment' &&
      contains(github.event.comment.body, '/mark-duplicate')
    runs-on: ubuntu-latest
    steps:
      - name: Run Dupligit Mark
        uses: CS453-Group4/Dupligit@v1.0.7
        with:
          mode: mark
          issue-body: ${{ github.event.comment.body }}
          issue-number: ${{ github.event.issue.number }}
          comment-author: ${{ github.event.comment.user.login }}
          repo: ${{ github.repository }}
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}


```

# User Manual (Usage Instructions)
Project Repository: https://github.com/CS453-Group4/Dupligit

How to Use
  nstall Dupligit Action:
  In your repo (e.g., your-org/your-repo), create a workflow file:  .github/workflows/dupligit.yml
  Copy and paste the ready workflow YAML from the README.md of the Dupligit repository.


  To use the latest stable version: uses:CS453-Group4/Dupligit@1.0.11

  Add Secrets:
  Go to your GitHub repo → Settings → Secrets → Actions:
  GEMINI_API_KEY → your Gemini API key
  GH_TOKEN is automatically available as a GitHub-provided token.

# How It Works
    A. When a user opens an issue:
        Dupligit Bot scans all existing open issues.
        Embeds and compares using FAISS + LLM validation.
        If similar issues are found, it:
        Posts a markdown table of candidates with % similarity.
        Adds a needs-duplicate-review label.
        Instructs maintainers to confirm.

      B. When a maintainer comments:
        /mark-duplicate #<issue_number>
        Dupligit checks their permission (admin, maintain, write).
        If authorized:
        Posts a confirmation comment.
        Adds duplicate label.
        Closes the duplicate issue.
        Users with read-only access cannot mark issues as duplicates.


