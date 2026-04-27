---
name: asadd
description: Add a skill reference from the aigonskills index to the project's CLAUDE.md or AGENT.md. Use when the user says "add skill", "register skill", "asadd", or wants to bookmark a remote skill for later use with asrun.
argument-hint: <skill id, name, or search query>
---

# Add a skill reference

Adds a skill to the `## aigonskills` section in the project's CLAUDE.md or AGENT.md. This creates a tracked reference with hashes — it does not download files. Use `asrun` to execute referenced skills, or `asinstall` to download them locally.

Requires the aigonskills MCP server — see the `install` skill if not connected.

## Resolve the skill

The argument can be a numeric ID, a normalized name, or a search query.

1. **Numeric** — use as skill ID directly.
2. **Underscored, no spaces** — try as normalized name: `skill(namespace="bynormalizedname", name="$ARGUMENTS")`. If it fails, fall back to search.
3. **Otherwise** — search: `call(namespace="aigonskills", function="list", kwargs={"query": "$ARGUMENTS"})`. If multiple results, show top 5 (id, name, description) and ask the user to pick. If no results, suggest different terms or a semantic mode.

## Fetch metadata

```
call(namespace="aigonskills", function="metadata", kwargs={"id": <id>})
```

Extract: `id`, `name`, `body_hash`, `description`, and the `files` list (each file has `path`, `url` containing the blob_sha prefix).

## Find the target file

Look for CLAUDE.md or AGENT.md in the project root. If both exist, use CLAUDE.md. If neither exists, ask the user which to create.

## Add the reference

Read the file. Look for an existing `## aigonskills` section.

**If the section exists:**
- Check the table for a row with the same id — if found, update its body_hash and description instead of adding a duplicate.
- Otherwise append a new row to the table.

**If the section does not exist**, append it to the end of the file:

```markdown
## aigonskills

| id | name | body_hash | description |
|----|------|-----------|-------------|
| <id> | <name> | <body_hash> | <description> |
```

**If the skill has associated files**, add a manifest block immediately after the table row (or after the table if adding the section fresh):

```markdown
<!-- asfiles:<id> -->
<!-- <path>|<blob_sha_prefix> -->
<!-- /asfiles -->
```

Extract `blob_sha_prefix` from each file's `url` field (the last path segment of `https://skills.aigon.ai/api/files/<blob_sha_prefix>`). New files have no safety status yet — `asrun` will evaluate them on first use.

Report what was added: skill name, id, file count, and which file was modified.
