#!/usr/bin/env python3
"""Structural linter — enforces project-specific architectural rules that
generic linters (ruff, eslint, pylint) cannot catch.

Reads your codebase and flags violations of conventions documented in your
CLAUDE.md or architecture docs. Runs with stdlib only — no dependencies.

Usage:
    python _scripts/structural_lint.py              # all rules
    python _scripts/structural_lint.py --rule NO_TEXT  # single rule
    python _scripts/structural_lint.py --help

This is a reference implementation. Adapt SCAN_DIRS, SKIP_DIRS, and the
individual rule functions to match your project's conventions.
"""

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────
# Adapt these to your project layout.

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCAN_DIRS = [
    PROJECT_ROOT / "src",
    # Add additional top-level packages here, e.g.:
    # PROJECT_ROOT / "services",
]

SKIP_DIRS = {"__pycache__", ".git", "tmp", ".venv", "node_modules"}

# Per-rule file-level exception sets. Use per-line `# noqa: RULE_ID` for
# one-off exceptions instead of adding files here.
NO_TEXT_EXCEPTIONS: set[str] = set()
NO_RUN_SYNC_EXCEPTIONS: set[str] = set()

# Patterns to auto-skip for NO_TEXT (legitimate DDL/infrastructure usage)
SERVER_DEFAULT_RE = re.compile(r"server_default\s*=\s*text\(")
PARTIAL_INDEX_RE = re.compile(r"postgresql_where\s*=\s*text\(")
HEALTH_CHECK_RE = re.compile(r"""text\(\s*["']SELECT 1["']\s*\)""")
SCHEMA_CHECK_RE = re.compile(r"""text\(\s*["']SELECT 1 FROM\s""")
DDL_RE = re.compile(r"""text\(\s*(?:f?["'](?:DROP|CREATE|ALTER)\s)""")


# ─── Violation ───────────────────────────────────────────────────────────────

@dataclass
class Violation:
    file: str
    line: int
    col: int
    rule_id: str
    message: str
    remediation: str = ""


# ─── Rule checkers ───────────────────────────────────────────────────────────
#
# Each rule checker follows the same signature:
#   Line-based:  (filepath, lines, rel) -> list[Violation]
#   AST-based:   (filepath, rel) -> list[Violation]
#   Global:      () -> list[Violation]
#
# Every rule supports `# noqa: RULE_ID` inline comments to suppress.


def check_no_text(filepath: Path, lines: list[str], rel: str) -> list[Violation]:
    """NO_TEXT: Detect `from sqlalchemy import text` and raw text() calls.

    Two-pass approach:
    1. First pass: detect if file imports text from sqlalchemy (and any alias)
    2. Second pass: flag the import lines + any text()/alias() calls
    This avoids false positives on non-sqlalchemy text() calls.
    """
    if rel in NO_TEXT_EXCEPTIONS:
        return []

    import_re = re.compile(r"from\s+sqlalchemy\s+import\s+(.+)")
    text_aliases: set[str] = set()
    import_lines: set[int] = set()

    in_comment_block = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        triples = stripped.count('"""') + stripped.count("'''")
        if triples % 2 == 1:
            in_comment_block = not in_comment_block
        if in_comment_block:
            continue

        m = import_re.search(line)
        if m:
            import_part = m.group(1)
            for token in import_part.split(","):
                token = token.strip().rstrip("\\").strip()
                if not token:
                    continue
                parts = token.split()
                if parts[0] == "text":
                    alias = parts[2] if len(parts) >= 3 and parts[1] == "as" else "text"
                    text_aliases.add(alias)
                    import_lines.add(i)

    if not text_aliases:
        return []

    violations = []
    in_comment_block = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "# noqa: NO_TEXT" in line or "# noqa:NO_TEXT" in line:
            continue

        triples = stripped.count('"""') + stripped.count("'''")
        if triples % 2 == 1:
            in_comment_block = not in_comment_block
        if in_comment_block:
            continue

        if SERVER_DEFAULT_RE.search(line):
            continue
        if PARTIAL_INDEX_RE.search(line):
            continue
        if HEALTH_CHECK_RE.search(line):
            continue
        if SCHEMA_CHECK_RE.search(line):
            continue
        if DDL_RE.search(line):
            continue
        if i in import_lines:
            continue

        for alias in text_aliases:
            pattern = rf"(?<![.\w]){re.escape(alias)}\s*\("
            if re.search(pattern, line):
                try:
                    col = line.index(alias) + 1
                except ValueError:
                    col = 1
                violations.append(Violation(
                    file=rel, line=i, col=col,
                    rule_id="NO_TEXT",
                    message=f"Call to `{alias}()` — use SQLAlchemy Core expressions",
                    remediation="Replace text('...') with select()/insert()/update()/delete()",
                ))

    return violations


def check_no_query(filepath: Path, lines: list[str], rel: str) -> list[Violation]:
    """NO_QUERY: Detect session.query() usage (legacy SQLAlchemy 1.x style)."""
    violations = []
    in_comment_block = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "# noqa: NO_QUERY" in line or "# noqa:NO_QUERY" in line:
            continue

        triples = stripped.count('"""') + stripped.count("'''")
        if triples % 2 == 1:
            in_comment_block = not in_comment_block
        if in_comment_block:
            continue

        if re.search(r"\.\s*query\s*\(", line):
            col = line.index("query") + 1
            violations.append(Violation(
                file=rel, line=i, col=col,
                rule_id="NO_QUERY",
                message="Use of `.query()` — use `select()` instead",
                remediation="Replace sess.query(Model) with select(Model)",
            ))

    return violations


def check_no_run_sync(filepath: Path, lines: list[str], rel: str) -> list[Violation]:
    """NO_RUN_SYNC: Detect run_sync() in async codebases."""
    if rel in NO_RUN_SYNC_EXCEPTIONS:
        return []

    violations = []
    in_comment_block = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "# noqa: NO_RUN_SYNC" in line or "# noqa:NO_RUN_SYNC" in line:
            continue

        triples = stripped.count('"""') + stripped.count("'''")
        if triples % 2 == 1:
            in_comment_block = not in_comment_block
        if in_comment_block:
            continue

        if re.search(r"\.run_sync\s*\(", line):
            col = line.index("run_sync") + 1
            violations.append(Violation(
                file=rel, line=i, col=col,
                rule_id="NO_RUN_SYNC",
                message="Use of `run_sync()` — use async `await session.execute()` instead",
                remediation="Rewrite using async SQLAlchemy Core",
            ))

    return violations


# ─── Example: Cross-package import boundary ─────────────────────────────────
# Adapt the package names to your project. This enforces that two packages
# (e.g. "frontend" and "backend") don't import from each other directly.
#
# PACKAGE_A = "frontend"
# PACKAGE_B = "backend"
#
# def check_no_cross_import(filepath: Path, lines: list[str], rel: str) -> list[Violation]:
#     """NO_CROSS_IMPORT: Detect imports between isolated packages."""
#     in_a = rel.startswith(f"{PACKAGE_A}/")
#     in_b = rel.startswith(f"{PACKAGE_B}/")
#     if not in_a and not in_b:
#         return []
#     violations = []
#     for i, line in enumerate(lines, 1):
#         stripped = line.strip()
#         if "# noqa: NO_CROSS_IMPORT" in line:
#             continue
#         if in_a and re.search(rf"(?:from|import)\s+{PACKAGE_B}", stripped):
#             violations.append(Violation(
#                 file=rel, line=i, col=1,
#                 rule_id="NO_CROSS_IMPORT",
#                 message=f"{PACKAGE_A} must not import from {PACKAGE_B}",
#                 remediation="Use API calls instead of direct imports",
#             ))
#         if in_b and re.search(rf"(?:from|import)\s+{PACKAGE_A}", stripped):
#             violations.append(Violation(
#                 file=rel, line=i, col=1,
#                 rule_id="NO_CROSS_IMPORT",
#                 message=f"{PACKAGE_B} must not import from {PACKAGE_A}",
#                 remediation="Use API calls instead of direct imports",
#             ))
#     return violations


# ─── Example: Require decorator on methods with a specific parameter ────────
# Useful for enforcing patterns like @with_session, @with_transaction, etc.
#
# REQUIRED_DECORATOR = "with_session"
# REQUIRED_PARAM = "session"
# SCAN_PATH_CONTAINS = "/database/"
#
# def check_required_decorator(filepath: Path, rel: str) -> list[Violation]:
#     """REQUIRED_DECORATOR: Methods with a specific param must have a decorator."""
#     if SCAN_PATH_CONTAINS not in rel:
#         return []
#     try:
#         source = filepath.read_text(encoding="utf-8")
#         tree = ast.parse(source, filename=str(filepath))
#     except (SyntaxError, UnicodeDecodeError):
#         return []
#     violations = []
#     for node in ast.walk(tree):
#         if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
#             continue
#         if node.name.startswith("_"):
#             continue
#         arg_names = [a.arg for a in node.args.args]
#         if REQUIRED_PARAM not in arg_names:
#             continue
#         has_dec = any(
#             (isinstance(d, ast.Name) and d.id == REQUIRED_DECORATOR) or
#             (isinstance(d, ast.Attribute) and d.attr == REQUIRED_DECORATOR)
#             for d in node.decorator_list
#         )
#         if not has_dec:
#             violations.append(Violation(
#                 file=rel, line=node.lineno, col=node.col_offset + 1,
#                 rule_id="REQUIRED_DECORATOR",
#                 message=f"`{node.name}()` has `{REQUIRED_PARAM}` param but no @{REQUIRED_DECORATOR}",
#                 remediation=f"Add @{REQUIRED_DECORATOR} decorator",
#             ))
#     return violations


def check_no_silent_failure(filepath: Path, lines: list[str], rel: str) -> list[Violation]:
    """NO_SILENT_FAILURE: Detect except blocks that swallow errors into fake results.

    Catches except blocks that assign hardcoded fallback values to result variables
    (response, result, etc.) without re-raising. These produce output
    indistinguishable from legitimate results, hiding real errors.
    """
    violations = []
    in_except = False
    except_line = 0
    except_indent = 0
    except_has_raise = False
    except_fallback_assignments: list[tuple[int, str]] = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if "# noqa: NO_SILENT_FAILURE" in line or "# noqa:NO_SILENT_FAILURE" in line:
            continue

        if stripped.startswith("except ") or stripped == "except:":
            if in_except and not except_has_raise:
                for fa_line, fa_var in except_fallback_assignments:
                    violations.append(Violation(
                        file=rel, line=fa_line, col=1,
                        rule_id="NO_SILENT_FAILURE",
                        message=f"Fallback assignment to `{fa_var}` in except block (line {except_line}) without re-raise — silent failure",
                        remediation="Re-raise the exception instead of assigning a fake result",
                    ))

            in_except = True
            except_line = i
            except_indent = len(line) - len(line.lstrip())
            except_has_raise = False
            except_fallback_assignments = []

        elif in_except:
            if stripped and not stripped.startswith("#"):
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= except_indent:
                    if not except_has_raise:
                        for fa_line, fa_var in except_fallback_assignments:
                            violations.append(Violation(
                                file=rel, line=fa_line, col=1,
                                rule_id="NO_SILENT_FAILURE",
                                message=f"Fallback assignment to `{fa_var}` in except block (line {except_line}) without re-raise — silent failure",
                                remediation="Re-raise the exception instead of assigning a fake result",
                            ))
                    in_except = False
                    except_fallback_assignments = []

            if in_except:
                if stripped.startswith("raise"):
                    except_has_raise = True

                if not except_has_raise:
                    m = re.match(r"(\w*(?:response|result)\w*)\s+=\s+(.*)", stripped)
                    if m:
                        var_name = m.group(1)
                        rhs = m.group(2).strip()
                        is_fallback = rhs.startswith(("f\"", "f'", '"', "'", "None", "[]", "{}", "0", "False", "True"))
                        if is_fallback:
                            except_fallback_assignments.append((i, var_name))

    if in_except and not except_has_raise:
        for fa_line, fa_var in except_fallback_assignments:
            violations.append(Violation(
                file=rel, line=fa_line, col=1,
                rule_id="NO_SILENT_FAILURE",
                message=f"Fallback assignment to `{fa_var}` in except block (line {except_line}) without re-raise — silent failure",
                remediation="Re-raise the exception instead of assigning a fake result",
            ))

    return violations


def check_no_magic_number(filepath: Path, rel: str) -> list[Violation]:
    """NO_MAGIC_NUMBER: Detect numeric literals outside constants.py files.

    All magic numbers should be named constants in the module's constants.py.
    Only 0 and 1 (int and float) are allowed inline everywhere.

    Auto-skipped contexts:
    - HTTP status codes (unambiguous always, ambiguous with context)
    - Slice components: [0:2], [:3], [-1:]
    - Keyword args: indent=2, ndigits=3, base=16, ...
    - .group(N) / .groups()[N] regex calls
    - range() / enumerate() arguments
    - round() precision (second arg)
    """
    if filepath.name == "constants.py":
        return []
    if filepath.name.startswith("test_") or "/tests/" in str(filepath):
        return []

    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
        source_lines = source.splitlines()
    except (SyntaxError, UnicodeDecodeError):
        return []

    _annotate_parents(tree)

    TRIVIAL = {0, 1}
    violations = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        if not isinstance(node.value, (int, float)):
            continue
        if node.value in TRIVIAL:
            continue

        line_num = node.lineno
        if line_num <= len(source_lines):
            line_text = source_lines[line_num - 1]
            if "# noqa: NO_MAGIC_NUMBER" in line_text or "# noqa:NO_MAGIC_NUMBER" in line_text:
                continue

        if isinstance(node.value, int) and _is_http_status_or_port(node.value, source_lines, line_num):
            continue

        if _is_benign_context(node):
            continue

        violations.append(Violation(
            file=rel, line=line_num, col=node.col_offset + 1,
            rule_id="NO_MAGIC_NUMBER",
            message=f"Magic number `{node.value}` — extract to constants.py",
            remediation="Move to module's constants.py with a descriptive UPPER_SNAKE_CASE name",
        ))

    return violations


def _annotate_parents(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child._parent = node  # type: ignore[attr-defined]


def _get_parent(node: ast.AST) -> ast.AST | None:
    return getattr(node, "_parent", None)


_BENIGN_KWARGS = {
    "indent", "ndigits", "base", "maxsplit", "start", "fillvalue",
    "stacklevel", "limit", "timeout", "encoding",
    "year", "month", "day", "hour", "minute", "second", "microsecond",
    "hours", "minutes", "seconds", "days", "weeks", "milliseconds", "microseconds",
    "max_age",
    "level", "depth", "width", "height",
}

_BENIGN_FUNCS = {"range", "enumerate", "round", "divmod", "pow"}
_BENIGN_METHODS = {"group", "groups", "start", "end", "span", "replace"}


def _is_benign_context(node: ast.AST) -> bool:
    parent = _get_parent(node)
    if parent is None:
        return False

    if isinstance(parent, ast.Slice):
        return True
    if isinstance(parent, ast.UnaryOp) and isinstance(_get_parent(parent), ast.Slice):
        return True

    if isinstance(parent, ast.keyword) and parent.arg in _BENIGN_KWARGS:
        return True

    if isinstance(parent, ast.Call):
        func = parent.func
        if isinstance(func, ast.Name) and func.id in _BENIGN_FUNCS:
            return True
        if isinstance(func, ast.Attribute) and func.attr in _BENIGN_METHODS:
            return True

    if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Mult):
        other = parent.left if parent.right is node else parent.right
        if isinstance(other, ast.Constant) and isinstance(other.value, str):
            return True

    if isinstance(parent, ast.Dict) and node in parent.keys:
        return True

    if isinstance(parent, ast.Compare):
        for comparator in parent.comparators:
            if comparator is node:
                left = parent.left
                if isinstance(left, ast.Call) and isinstance(left.func, ast.Name) and left.func.id == "len":
                    return True
        if parent.left is node:
            for comparator in parent.comparators:
                if isinstance(comparator, ast.Call) and isinstance(comparator.func, ast.Name) and comparator.func.id == "len":
                    return True

    if _is_inside_logger_call(node):
        return True

    return False


def _is_inside_logger_call(node: ast.AST) -> bool:
    current = _get_parent(node)
    while current is not None:
        if isinstance(current, ast.Call):
            func = current.func
            if isinstance(func, ast.Attribute) and func.attr in (
                "debug", "info", "warning", "error", "critical", "exception", "log",
            ):
                if isinstance(func.value, ast.Name) and func.value.id in ("logger", "log", "logging"):
                    return True
            break
        current = _get_parent(current)
    return False


_HTTP_UNAMBIGUOUS = {
    201, 202, 204,
    301, 302, 303, 304, 307, 308,
    401, 403, 404, 405, 409, 410, 422, 429,
    502, 503, 504,
}

_WELL_KNOWN_PORTS = {443, 8443}

_HTTP_AMBIGUOUS = {200, 400, 500}

_HTTP_CONTEXT_RE = re.compile(
    r"status_code|status|HTTPException|JSONResponse|Response\(|\.raise_for_status"
)


def _is_http_status_or_port(value: int, source_lines: list[str], line_num: int) -> bool:
    if value in _HTTP_UNAMBIGUOUS or value in _WELL_KNOWN_PORTS:
        return True
    if value in _HTTP_AMBIGUOUS and line_num <= len(source_lines):
        return bool(_HTTP_CONTEXT_RE.search(source_lines[line_num - 1]))
    return False


# ─── Lazy import rule ────────────────────────────────────────────────────────

NO_LAZY_IMPORT_EXCEPTIONS = {
    "scripts/",
}


def check_no_lazy_import(filepath: Path, rel: str) -> list[Violation]:
    """NO_LAZY_IMPORT: Detect import statements inside function/method bodies.

    Imports should be at module level. Lazy imports hide dependency issues
    and can cause runtime ImportError that the linter can't catch.

    Exceptions:
    - TYPE_CHECKING blocks (if TYPE_CHECKING: from ... import ...)
    - Circular import avoidance with inline comment: # noqa: NO_LAZY_IMPORT
    """
    if filepath.name.startswith("test_") or "/tests/" in str(filepath):
        return []

    for exc in NO_LAZY_IMPORT_EXCEPTIONS:
        if exc in rel:
            return []

    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
        source_lines = source.splitlines()
    except (SyntaxError, UnicodeDecodeError):
        return []

    violations = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for child in ast.walk(node):
            if not isinstance(child, (ast.Import, ast.ImportFrom)):
                continue

            line_num = child.lineno
            if line_num <= len(source_lines):
                line_text = source_lines[line_num - 1]
                if "# noqa: NO_LAZY_IMPORT" in line_text or "# noqa:NO_LAZY_IMPORT" in line_text:
                    continue

            if isinstance(child, ast.ImportFrom):
                module = child.module or ""
            else:
                module = ", ".join(alias.name for alias in child.names)

            violations.append(Violation(
                file=rel,
                line=line_num,
                col=child.col_offset + 1,
                rule_id="NO_LAZY_IMPORT",
                message=f"Lazy import inside function body: {module}",
                remediation="Move import to module level, or add # noqa: NO_LAZY_IMPORT if circular",
            ))

    return violations


# ─── Example: Versioned implementation naming ───────────────────────────────
# If your project uses a registry pattern where implementation files must
# follow a dated naming convention (e.g. provider_framework_YYYYMMDD.py),
# you can enforce that with rules like these (commented out — adapt to fit):
#
# _IMPL_DATED_RE = re.compile(r"^[a-z]\w+_[a-z]\w+.*_\d{8}")
#
# def check_dated_impl(filepath: Path, lines: list[str], rel: str) -> list[Violation]:
#     """DATED_IMPL: Files importing the base wrapper must have a dated filename."""
#     if _IMPL_DATED_RE.match(filepath.stem):
#         return []
#     if filepath.name.startswith("test_") or "/tests/" in rel:
#         return []
#     for line in lines:
#         if "import BaseWrapper" in line.strip():
#             return [Violation(
#                 file=rel, line=1, col=1,
#                 rule_id="DATED_IMPL",
#                 message=f"'{filepath.name}' imports BaseWrapper but has no dated name",
#                 remediation="Rename to provider_framework_YYYYMMDD.py",
#             )]
#     return []
#
# def check_registry_base_required() -> list[Violation]:
#     """REGISTRY_BASE: Dirs with dated impl files must have base.py."""
#     violations = []
#     seen_dirs: set[Path] = set()
#     for scan_dir in SCAN_DIRS:
#         if not scan_dir.exists():
#             continue
#         for filepath in scan_dir.rglob("*.py"):
#             if not _IMPL_DATED_RE.match(filepath.stem):
#                 continue
#             parent = filepath.parent
#             if parent in seen_dirs:
#                 continue
#             seen_dirs.add(parent)
#             if not (parent / "base.py").exists():
#                 rel_dir = str(parent.relative_to(PROJECT_ROOT))
#                 violations.append(Violation(
#                     file=rel_dir + "/", line=1, col=1,
#                     rule_id="REGISTRY_BASE",
#                     message="Directory has dated impl files but no base.py registry",
#                     remediation="Add base.py with abstract base class and registry container",
#                 ))
#     return violations


# ─── Global rules ────────────────────────────────────────────────────────────

def check_version_sync() -> list[Violation]:
    """VERSION_SYNC: Root pyproject.toml version must match src/version.py."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    version_py = PROJECT_ROOT / "src" / "version.py"

    if not pyproject.exists() or not version_py.exists():
        return []

    pyproject_version = None
    for line in pyproject.read_text().splitlines():
        m = re.match(r'^version\s*=\s*"([^"]+)"', line)
        if m:
            pyproject_version = m.group(1)
            break

    app_version = None
    for line in version_py.read_text().splitlines():
        m = re.match(r'^__version__\s*=\s*"([^"]+)"', line)
        if m:
            app_version = m.group(1)
            break

    if pyproject_version is None or app_version is None:
        return []

    if pyproject_version != app_version:
        return [Violation(
            file="pyproject.toml",
            line=1, col=1,
            rule_id="VERSION_SYNC",
            message=f"pyproject.toml version \"{pyproject_version}\" != src/version.py \"{app_version}\"",
            remediation="Update both files to the same version",
        )]

    return []


# ─── File collection ─────────────────────────────────────────────────────────

def collect_files() -> list[Path]:
    files = []
    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            if any(part in SKIP_DIRS for part in py_file.parts):
                continue
            files.append(py_file)
    return sorted(files)


def rel_path(filepath: Path) -> str:
    try:
        return str(filepath.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(filepath)


# ─── Rule registry ──────────────────────────────────────────────────────────

LINE_RULES = {
    "NO_TEXT": check_no_text,
    "NO_QUERY": check_no_query,
    "NO_RUN_SYNC": check_no_run_sync,
    "NO_SILENT_FAILURE": check_no_silent_failure,
}

AST_RULES = {
    "NO_MAGIC_NUMBER": check_no_magic_number,
    "NO_LAZY_IMPORT": check_no_lazy_import,
}

GLOBAL_RULES = {
    "VERSION_SYNC": check_version_sync,
}

ALL_RULES = list(LINE_RULES.keys()) + list(AST_RULES.keys()) + list(GLOBAL_RULES.keys())

WARNING_RULES: set[str] = set()


# ─── Reporter ────────────────────────────────────────────────────────────────

def report(violations: list[Violation], active_rules: list[str]) -> int:
    if not violations:
        print(f"No violations found ({len(active_rules)} rules checked)")
        return 0

    errors = [v for v in violations if v.rule_id not in WARNING_RULES]
    warnings = [v for v in violations if v.rule_id in WARNING_RULES]

    violations.sort(key=lambda v: (v.file, v.line))

    for v in violations:
        tag = " (warning)" if v.rule_id in WARNING_RULES else ""
        print(f"{v.file}:{v.line}:{v.col}: {v.rule_id}{tag} {v.message}")

    print()
    rule_counts: dict[str, int] = {}
    for v in violations:
        rule_counts[v.rule_id] = rule_counts.get(v.rule_id, 0) + 1

    print("Summary:")
    print(f"  {'Rule':<25} {'Violations':>10}  {'Level':>7}")
    print(f"  {'─' * 25} {'─' * 10}  {'─' * 7}")
    for rule_id in sorted(rule_counts.keys()):
        level = "warning" if rule_id in WARNING_RULES else "error"
        print(f"  {rule_id:<25} {rule_counts[rule_id]:>10}  {level:>7}")
    print(f"  {'─' * 25} {'─' * 10}  {'─' * 7}")
    print(f"  {'TOTAL':<25} {len(violations):>10}")
    if warnings:
        print(f"  {'errors':<25} {len(errors):>10}")
        print(f"  {'warnings':<25} {len(warnings):>10}")

    return 1 if errors else 0


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Structural linter for project-specific architectural rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available rules: {', '.join(ALL_RULES)}",
    )
    parser.add_argument(
        "--rule", type=str, default=None,
        help="Run only this rule (e.g. --rule NO_TEXT)",
    )
    args = parser.parse_args()

    if args.rule:
        rule_name = args.rule.upper()
        if rule_name not in ALL_RULES:
            print(f"Error: Unknown rule '{args.rule}'. Available: {', '.join(ALL_RULES)}")
            sys.exit(2)
        active_line_rules = {k: v for k, v in LINE_RULES.items() if k == rule_name}
        active_ast_rules = {k: v for k, v in AST_RULES.items() if k == rule_name}
        active_global_rules = {k: v for k, v in GLOBAL_RULES.items() if k == rule_name}
        active_rules = [rule_name]
    else:
        active_line_rules = LINE_RULES
        active_ast_rules = AST_RULES
        active_global_rules = GLOBAL_RULES
        active_rules = ALL_RULES

    files = collect_files()
    all_violations: list[Violation] = []

    for filepath in files:
        rel = rel_path(filepath)

        if active_line_rules:
            try:
                lines = filepath.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, PermissionError):
                continue

            for _rule_id, checker in active_line_rules.items():
                all_violations.extend(checker(filepath, lines, rel))

        for _rule_id, checker in active_ast_rules.items():
            all_violations.extend(checker(filepath, rel))

    for _rule_id, checker in active_global_rules.items():
        all_violations.extend(checker())

    sys.exit(report(all_violations, active_rules))


if __name__ == "__main__":
    main()
