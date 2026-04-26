---
name: structural-lint
description: Create a project-specific structural linter that enforces architectural rules ruff/eslint can't catch. Use when the user asks to "add a structural linter", "enforce architecture rules", "lint for project conventions", or "catch architectural violations".
---

# Structural Linter

Create a custom Python linter that enforces project-specific architectural rules — the kind that generic linters (ruff, eslint, pylint) can't catch. These are rules derived from your project's CLAUDE.md, architecture docs, and hard-won conventions.

## What structural linting catches

Things generic linters miss:
- **Forbidden API usage** — e.g. raw SQL `text()` when the project requires SQLAlchemy Core expressions
- **Cross-module import violations** — e.g. service A must not import from service B directly
- **Naming conventions** — e.g. LLM agent files must follow a dated naming scheme
- **Decorator requirements** — e.g. database methods must use `@with_session`
- **Silent failure patterns** — e.g. except blocks that swallow errors into fake results
- **Magic numbers** — numeric literals that should be named constants
- **Lazy imports** — imports inside function bodies that hide dependency issues
- **Version sync** — version strings that must match across files

## Steps

1. **Identify the rules.** Read the project's CLAUDE.md, architecture docs, and any conventions docs. Look for statements like "never do X", "always use Y", "files in Z must have...". Each becomes a rule.

2. **Create the linter script.** Put it in `_scripts/structural_lint.py` (or the project's scripts directory). Key design decisions:
   - **stdlib only** — no dependencies, runs anywhere
   - **Two kinds of rules**: line-based (regex on source lines) and AST-based (parsing the syntax tree for structural patterns)
   - **Global rules** for cross-file checks (e.g. "every registry dir must have base.py")
   - **noqa comments** — each rule supports `# noqa: RULE_ID` for intentional exceptions
   - **Ruff-style output** — `file:line:col: RULE_ID message` for editor integration

3. **Structure each rule as a function** that takes `(filepath, lines, rel_path)` and returns a list of `Violation` dataclasses:

   ```python
   @dataclass
   class Violation:
       file: str
       line: int
       col: int
       rule_id: str
       message: str
       remediation: str = ""
   ```

4. **Register rules in a dict** so they can be run individually with `--rule RULE_ID`:

   ```python
   LINE_RULES = {"NO_TEXT": check_no_text, "NO_CROSS_IMPORT": check_no_cross_import}
   AST_RULES = {"WITH_SESSION": check_with_session, "NO_MAGIC_NUMBER": check_no_magic_number}
   GLOBAL_RULES = {"VERSION_SYNC": check_version_sync}
   ```

5. **Add exception mechanisms** for each rule:
   - Per-line: `# noqa: RULE_ID`
   - Per-file: exception sets in the config section
   - Contextual: auto-skip patterns (e.g. `server_default=text(...)` is legitimate DDL)

6. **Wire into CI** as a pre-commit hook or CI step:
   ```bash
   python _scripts/structural_lint.py           # all rules
   python _scripts/structural_lint.py --rule NO_TEXT  # single rule
   ```

## Reference implementation

See `resources/structural_lint.py` for a complete working example from a production Python project. It enforces 12 rules across three categories (line-based, AST-based, global) and demonstrates:
- Two-pass detection (import tracking + usage flagging)
- AST parent annotation for context-aware checks
- Benign-context heuristics (HTTP status codes, slice components, keyword args)
- Warning vs error severity levels
- Summary table reporting
