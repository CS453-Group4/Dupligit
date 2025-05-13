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

jobs:
  check-duplicate:
    if: github.event_name == 'issues'
    runs-on: ubuntu-latest
    steps:
      - uses: yourusername/dupligit-action@v1
        with:
          mode: check
          issue-title: ${{ github.event.issue.title }}
          issue-number: ${{ github.event.issue.number }}
          repo: ${{ github.repository }}

  mark-duplicate:
    if: |
      github.event_name == 'issue_comment' &&
      contains(github.event.comment.body, '/mark-duplicate')
    runs-on: ubuntu-latest
    steps:
      - uses: yourusername/dupligit-action@v1
        with:
          mode: mark
          issue-body: ${{ github.event.comment.body }}
          issue-number: ${{ github.event.issue.number }}
          comment-author: ${{ github.event.comment.user.login }}
          repo: ${{ github.repository }}
          
```