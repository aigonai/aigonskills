---
name: init
description: This skill should be used when the user asks to "initialize CLAUDE.md", "set up CLAUDE.md", or "document this project for Claude". Creates a CLAUDE.md file with codebase documentation.
---

# Init

Create a `CLAUDE.md` file that gives Claude useful context about this project.

## Steps

1. Explore the repo:
   - `ls`, `cat package.json` / `pyproject.toml` / `Cargo.toml` — identify language and toolchain
   - Skim `README.md` if it exists
   - `find . -name "*.md" | head -10` — check for existing docs
2. Identify the key things Claude needs to know:
   - Build, test, and run commands
   - Directory structure (brief)
   - Non-obvious conventions or gotchas
3. Write `CLAUDE.md` to the project root — keep it under 200 lines, no padding
