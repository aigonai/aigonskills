---
name: ascreate
description: Create a new Claude Code skill. Use when the user says "create a skill", "new skill", "ascreate", "make a skill", or wants to author a custom slash command.
argument-hint: <skill name>
---

# Create a skill

Guide for authoring a Claude Code skill that can be used as a `/skillname` slash command.

## Choose a location

- **Global** — `~/.claude/skills/<skill-name>/` — available in all projects
- **Project** — `.claude/skills/<skill-name>/` — only available in this project

Ask the user which they want. Default to project-level.

## Directory structure

Every skill is a directory with a `SKILL.md` file. Supporting files go in subdirectories:

```
<skill-name>/
├── SKILL.md           # Required — frontmatter + instructions
├── scripts/           # Executable scripts (.sh, .py, .bash)
├── resources/         # Reference implementations, config templates
└── examples/          # Example data, sample outputs
```

Subdirectory names are always **plural**. Only create subdirectories that are needed.

## SKILL.md format

```markdown
---
name: <skill-name>
description: <what it does and when to use it>
argument-hint: <what arguments it expects>
---

# Title

Instructions for Claude to follow when this skill is invoked.
```

### Frontmatter fields

Only `name` and `description` are needed for most skills. Other available fields:

| Field | Purpose |
|-------|---------|
| `name` | Display name (directory name used if omitted) |
| `description` | What the skill does — Claude uses this to decide when to load it |
| `argument-hint` | Shown in autocomplete, e.g. `<filename>` or `<query> [--flag]` |
| `allowed-tools` | Tools Claude can use without permission, e.g. `Bash(git add *)` |
| `model` | Override model when skill is active |
| `effort` | Override effort level: `low`, `medium`, `high`, `xhigh`, `max` |
| `context` | Set to `fork` to run in an isolated subagent |
| `disable-model-invocation` | `true` to prevent Claude from auto-triggering |
| `user-invocable` | `false` to hide from `/` menu (only Claude can invoke) |

### Dynamic content

Use these placeholders in the markdown body — they're replaced at invocation time:

- `$ARGUMENTS` — everything the user typed after `/skillname`
- `$0`, `$1`, ... — individual arguments by position
- `${CLAUDE_SKILL_DIR}` — path to the skill's directory (use this to reference scripts/resources)

### Shell commands in skills

Skills can run shell commands before the content is sent to Claude:

```markdown
Current git branch: !`git branch --show-current`
```

The output replaces the placeholder inline.

## Referencing files

Use `${CLAUDE_SKILL_DIR}` to reference files within the skill:

```markdown
Run the linter:
\`\`\`bash
python "${CLAUDE_SKILL_DIR}/scripts/lint.py" $ARGUMENTS
\`\`\`

See the reference implementation at `${CLAUDE_SKILL_DIR}/resources/example.py`.
```

## Writing good skills

- The description determines when Claude auto-loads the skill — include trigger phrases
- Instructions should be concrete steps, not general advice
- If the skill has side effects (deploys, sends messages), set `disable-model-invocation: true`
- Keep SKILL.md focused — put large reference files in `resources/`
- Scripts in `scripts/` should be self-contained with clear usage

## After creating

The skill is available immediately as `/skill-name`. No restart needed. Test it by typing `/` and looking for it in the autocomplete menu.
