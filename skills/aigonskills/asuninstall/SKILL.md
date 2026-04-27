---
name: asuninstall
description: Remove a locally installed aigonskills skill. Use when the user says "uninstall skill", "remove local skill", "asuninstall", or wants to delete an aigonskills-installed skill.
argument-hint: <skill name>
---

# Uninstall a local skill

Removes a skill that was installed via `asinstall`. Only targets skills with an `.aigonskills.json` marker file — skills installed by other means are left alone unless the user explicitly insists.

This only deletes local files — it does not affect references in CLAUDE.md (use `asremove` for that).

## Find the skill

Search for aigonskills-managed skills matching the argument:

```bash
find ~/.claude/skills .claude/skills -name ".aigonskills.json" 2>/dev/null
```

For each result, check the parent directory name against `$ARGUMENTS` (case-insensitive, partial match allowed).

- **No `.aigonskills.json` match but directory exists** — tell the user this skill was not installed via aigonskills. Only proceed if the user explicitly confirms they want it removed anyway.
- **Found in one location** — proceed to confirm.
- **Found in both** — list both and ask which to remove (or both).
- **Not found anywhere** — tell the user. List aigonskills-managed skills so they can see what's available.

## Confirm and delete

Show what will be deleted: full path, skill name and id from `.aigonskills.json`, and file listing.

After user confirms:
```bash
rm -rf <skill-directory>
```

Report that the skill was removed and the `/skillname` command is no longer available.
