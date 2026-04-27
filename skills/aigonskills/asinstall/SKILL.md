---
name: asinstall
description: Install a skill from the aigonskills index as a local Claude Code slash command. Use when the user says "install skill", "download skill", "asinstall", or wants a skill available offline as /skillname.
argument-hint: <skill id, name, or search query> [--project]
---

# Install a skill locally

Downloads a skill and its files from the aigonskills index into the local Claude Code skills directory, making it available as a `/skillname` slash command. Writes an `.aigonskills.json` marker file for tracking.

Requires the aigonskills MCP server — see the `install` skill if not connected. To search first, see the `asexplore` skill.

## Resolve the skill

1. **Numeric** — use as skill ID directly.
2. **Underscored, no spaces** — try as normalized name: `skill(namespace="bynormalizedname", name="$ARGUMENTS")`. Fall back to search on failure.
3. **Otherwise** — search: `call(namespace="aigonskills", function="list", kwargs={"query": "$ARGUMENTS"})`. Show top 5 if ambiguous, ask user to pick.

## Choose install location

- `--project` in arguments → `.claude/skills/<name>/`
- Otherwise → ask the user: global (`~/.claude/skills/<name>/`) or project-level (`.claude/skills/<name>/`)

## Fetch and install

1. Get metadata:
   ```
   call(namespace="aigonskills", function="metadata", kwargs={"id": <id>})
   ```

2. Determine directory name: use the skill's `name` field, lowercased, spaces → hyphens. If that directory already exists, warn and ask before overwriting.

3. Create the skill directory:
   ```bash
   mkdir -p <install_root>/<skill-name>
   ```

4. Download all files. The metadata `files` list includes SKILL.md and all associated files, each with a `url` field. Download every file via the API — do not write from memory:
   ```bash
   mkdir -p "$(dirname "<install_root>/<skill-name>/<path>")"
   curl -sS -o "<install_root>/<skill-name>/<path>" "<url>"
   ```
   This ensures the installed files are byte-identical to the index.

6. Write `.aigonskills.json` in the skill directory:
   ```json
   {
     "id": <id>,
     "name": "<name>",
     "body_hash": "<body_hash>",
     "normalized_name": "<normalized_name>",
     "installed": "<ISO 8601 timestamp>",
     "files": {
       "<path>": "<blob_sha_prefix>",
       "<path>": "<blob_sha_prefix>"
     }
   }
   ```
   This marker identifies the skill as aigonskills-managed and records the blob hashes at install time.

7. Report: installed location, `/skillname` command, number of files downloaded.

## Find all aigonskills-installed skills

To list every skill installed via asinstall, search for the marker file:

```bash
find ~/.claude/skills .claude/skills -name ".aigonskills.json" 2>/dev/null
```
