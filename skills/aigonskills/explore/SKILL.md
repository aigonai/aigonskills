---
name: explore
description: Explore and search the aigonskills index (15,000+ skills). Use when the user asks to "find a skill", "search skills", "explore skills", "what skills are available", "skill for X", or wants to discover skills for a specific purpose.
---

# Explore aigonskills

Requires the aigonskills MCP server — see the `install` skill if not connected. To read and access files from a skill you've found, see the `use` skill.

## Search

All search goes through the `list` function with a `query` and `mode` parameter.

### Keyword modes

**`fts`** (default) — Full-text search. Supports quoted phrases, OR, negation with `-`, prefix with `*`.

```
call(namespace="aigonskills", function="list", kwargs={"query": "pull request review"})
call(namespace="aigonskills", function="list", kwargs={"query": "\"code review\" OR lint"})
```

**`trigram`** — Fuzzy matching. Use for partial words, typos, or substrings FTS misses.

```
call(namespace="aigonskills", function="list", kwargs={"query": "kubernetes", "mode": "trigram"})
```

**`fts+trigram`** — Both combined. Slower but broader. Use when single modes return too few results.

### Semantic modes

Natural language instead of keywords. Use when you can describe what you want but don't know the right terms.

- **`semantic-desc`** — Matches against skill descriptions. Good default for semantic search.
- **`semantic-body`** — Matches against full SKILL.md body. Finds skills where the description doesn't mention the concept.
- **`semantic-both`** — Both. Widest net.

```
call(namespace="aigonskills", function="list", kwargs={"query": "a skill that reviews code for security vulnerabilities", "mode": "semantic-desc"})
```

Use `threshold` (0–1) to filter weak matches. 0.3–0.5 is a good range.

### When to use which

| Situation | Mode |
|-----------|------|
| You know exact terms | `fts` |
| Partial words or typos | `trigram` |
| Few keyword results | `fts+trigram` |
| Can describe it but lack keywords | `semantic-desc` |
| Not in description, might be in body | `semantic-body` or `semantic-both` |

## Filters

Combine with any search:
- `shell` — only skills that use shell commands
- `invocable` — only user-invocable skills (slash-command style)
- `scripts` — only skills with a scripts directory
- `tools` — only skills that declare allowed-tools
- `language` — by language code (e.g. `en`, `zh-cn`)
- `source` — scope to a specific `owner/repo`

```
call(namespace="aigonskills", function="list", kwargs={"query": "deploy", "shell": true})
call(namespace="aigonskills", function="list", kwargs={"query": "review", "source": "anthropics/claude-code"})
```

## Browse sources

List indexed GitHub repos ordered by skill count:

```
call(namespace="aigonskills", function="sources")
call(namespace="aigonskills", function="sources", kwargs={"owner": "anthropics"})
```

Use a repo from sources as the `source` filter in search to scope results.

## Documentation

- https://skills.aigon.ai/docs/
- https://skills.aigon.ai/docs/mcp/tools/
- https://skills.aigon.ai/docs/mcp/functions/
