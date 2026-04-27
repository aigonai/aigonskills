---
name: asrun
description: Run a skill that has been added to the project's CLAUDE.md or AGENT.md. Use when the user says "run skill", "asrun", "execute skill", or wants to use a referenced skill in the current session.
argument-hint: <skill id or name from references>
---

# Run a referenced skill

Fetches and executes a skill that has been registered in the project's CLAUDE.md or AGENT.md via `asadd`. Only runs referenced skills — use `asadd` to add one first, or `asexplore` to search the index.

Requires the aigonskills MCP server — see the `install` skill if not connected.

## 1. Resolve the skill

Read CLAUDE.md or AGENT.md in the project root. Find the `## aigonskills` section. If the section does not exist or is empty, tell the user there are no referenced skills and suggest `asadd` to add one.

Match `$ARGUMENTS` against the `id` or `name` columns in the table (case-insensitive for name, partial match allowed). If no match, list the available referenced skills so the user can pick. If multiple partial matches, show them and ask.

Note the file manifest from `<!-- asfiles:<id> -->` for safety checks.

## 2. Fetch and execute

Fetch the skill body:
```
skill(namespace="byid", name="<id>")
```

Read the returned content. It contains instructions to follow in the current session.

## 3. Handle associated files

If the skill's instructions reference files that need to be on disk, fetch metadata first:
```
call(namespace="aigonskills", function="metadata", kwargs={"id": <id>})
```

Compare each file's blob_sha (from the `url` field in metadata) against the `<!-- asfiles -->` manifest.

- **blob_sha matches, marked `executed`** — previously run executable, safe. Download silently:
  ```bash
  curl -sS -o "<path>" "<url>"
  ```
- **blob_sha matches, marked `examined`** — previously reviewed, safe. Download silently.
- **blob_sha changed or new entry, file is executable** (`.sh`, `.py`, `.bash`, or has executable intent in skill instructions) — show the file content to the user. Do not run until the user confirms it's safe. After approval, update the manifest line to `<path>|<new_blob_sha>|executed`.
- **blob_sha changed or new entry, non-executable** — note the change to the user, download, update manifest to `<path>|<new_blob_sha>|examined`.
- **File not in manifest at all** — treat as new. Executable: show and require approval. Non-executable: download with notice.

## 4. Follow the instructions

Apply the skill's instructions to the current session and working directory as if they were given directly by the user.
