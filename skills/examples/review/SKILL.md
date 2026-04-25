---
name: review
description: This skill should be used when the user asks to "review", "code review", or "review the PR". Reviews staged or branch changes for bugs, correctness, and style issues.
---

# Review

Review the current branch or staged changes and report issues.

## Steps

1. Get the diff: `git diff main...HEAD` (or `git diff --staged` if reviewing staged changes)
2. For each changed file, evaluate:
   - Correctness: logic errors, edge cases, off-by-one, null handling
   - Security: injection, auth bypasses, exposed secrets
   - Clarity: confusing names, missing context, dead code
   - Tests: are new behaviors covered?
3. Output findings grouped by severity: **Critical**, **Warning**, **Suggestion**
4. Keep feedback specific — include file and line number for each issue
