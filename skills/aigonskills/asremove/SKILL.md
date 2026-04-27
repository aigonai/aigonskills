---
name: asremove
description: Remove a skill reference from the project's CLAUDE.md or AGENT.md. Use when the user says "remove skill", "unregister skill", "asremove", or wants to stop tracking a remote skill.
argument-hint: <skill id or name>
---

# Remove a skill reference

Removes a skill from the `## aigonskills` section in CLAUDE.md or AGENT.md. This only removes the reference — it does not affect locally installed skills (use `asuninstall` for that).

## Find the target file

Look for CLAUDE.md or AGENT.md in the project root. If both exist, check both for an `## aigonskills` section. If neither has one, tell the user there are no skill references to remove.

## Match and remove

Read the `## aigonskills` section. Match `$ARGUMENTS` against the `id` or `name` columns in the table (case-insensitive for name).

If no match is found, list the currently referenced skills so the user can see what's available.

If matched:
1. Remove the table row for that skill.
2. Remove the associated `<!-- asfiles:<id> -->...<!-- /asfiles -->` block if present.
3. If the table is now empty (only header rows remain), remove the entire `## aigonskills` section.

Report what was removed.
