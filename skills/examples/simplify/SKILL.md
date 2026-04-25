---
name: simplify
description: This skill should be used when the user asks to "simplify", "clean up", "refactor for clarity", or "reduce complexity" in recently changed code. Reviews changed code for reuse, quality, and efficiency, then fixes any issues found.
---

# Simplify

Review recently changed code for unnecessary complexity, then fix it.

## Steps

1. Identify changed files: `git diff --name-only HEAD`
2. Read each changed file
3. Look for:
   - Duplicated logic that could be extracted
   - Abstractions that add complexity without value
   - Variables, parameters, or branches that aren't needed
   - Simpler stdlib or language idioms that replace custom code
4. Apply fixes directly — don't describe them, just make them
5. Re-read the result and confirm it's simpler than before
