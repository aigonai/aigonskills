---
name: mcp-cash-compliance
description: Check whether an MCP server conforms to the CaSH (Call-Skill-Help) standard. Use when the user asks to "check CaSH compliance", "validate MCP server", "audit CaSH conformance", or "test MCP CaSH".
---

# CaSH Compliance Checker

Verify that an MCP server conforms to the CaSH specification (https://aigon.ai/rfc-mcp-cash-model/). The CaSH model prescribes exactly three MCP tools — `call`, `help`, `skill` — with specific behavioral requirements.

## How to check

Connect to the server and run the checks below in order. Each check references a MUST/SHOULD requirement from the spec. Report results as PASS/FAIL/WARN.

## 1. Tool registration

**SHOULD: Server exposes no more than three tools: `call`, `help`, `skill`.**

List the tools the server registers. Check:
- Are `call`, `help`, `skill` present?
- Are there any additional tools beyond these three? (WARN if yes)

## 2. help() — Progressive disclosure

### 2a. Layer 0 — Top-level index

Call `help()` with no arguments.

- MUST return a list of top-level namespaces with one-line descriptions
- MUST NOT include function lists, sub-namespace contents, or parameter information
- SHOULD be markdown format

### 2b. Layer N — Namespace listing

For each namespace returned in 2a, call `help(namespace="<ns>")`.

- MUST return child namespaces and/or functions with one-line descriptions
- MUST NOT contain full signatures or parameter detail
- MUST NOT include skill references (skills and namespaces are separate hierarchies)

### 2c. Leaf — Function documentation

For each function returned in 2b, call `help(namespace="<ns>", function="<fn>")`.

- MUST return function documentation with parameters
- Check that parameter names, types, and descriptions are present

### 2d. Disclosure discipline

- Context cost MUST be proportional to discovery depth — each layer should be substantially smaller than the next
- Compare character count of Layer 0 vs Layer N vs Leaf responses

## 3. call() — Function execution

### 3a. Valid call

Pick a function discovered via help and call it with valid arguments:
```
call(namespace="<ns>", function="<fn>", kwargs={...})
```

- MUST return a response (format is implementation-defined)

### 3b. Unknown namespace

```
call(namespace="nonexistent_namespace_xyz", function="anything")
```

- MUST return an error (suggested code: `UNKNOWN_NAMESPACE`)

### 3c. Unknown function

Use a valid namespace but invalid function:
```
call(namespace="<valid_ns>", function="nonexistent_function_xyz")
```

- MUST return an error (suggested code: `UNKNOWN_FUNCTION`)

### 3d. Output size gating

Call a function likely to return a large result (e.g. a list without filters):

- If response exceeds gate threshold (default 10,000 characters), server MUST NOT return full response
- Gated response MUST communicate: that it was gated, count/summary of results, suggested size limit, directive to narrow query
- If gate threshold differs from default 10,000, it MUST be advertised in the top-level `help()` response

### 3e. sizelimit parameter

```
call(namespace="<ns>", function="<fn>", kwargs={...}, sizelimit=100)
```

- SHOULD accept `sizelimit` to override default gate threshold

## 4. skill() — Skill delivery

### 4a. Skill listing

Call `skill()` with no arguments (or `skill(namespace="")`) to discover available skills/namespaces.

### 4b. Fetch a skill

```
skill(namespace="<ns>", name="<skillname>")
```

- MUST return natural-language text suitable for LLM consumption
- MUST be text-only — no executable code blocks
- MUST be self-contained without assuming prior context
- MAY reference other skills by name using `skill(skillname="<name>")` convention
- MAY reference `help` and `call` in instructions

### 4c. Unknown skill

```
skill(namespace="<ns>", name="nonexistent_skill_xyz")
```

- MUST return an error (suggested code: `UNKNOWN_SKILL`)

## 5. Naming conventions

Check namespace labels, function names, and skill names discovered via help/skill:

- MUST contain only alphanumeric characters and optional underscores (a-z, A-Z, 0-9, _)
- MUST NOT contain hyphens, dots (except as hierarchy separator), slashes, whitespace, or punctuation
- Dot (.) is reserved for hierarchical separation only
- Labels that normalize identically (strip underscores + lowercase) MUST NOT coexist
- Function names SHOULD use verb-object form
- Namespace depth SHOULD be 2–3 levels

## 6. Server manifest (optional)

Check if `/.well-known/cash-mcp.yaml` is served at the server's host:

```bash
curl -s https://<server-host>/.well-known/cash-mcp.yaml
```

If present, validate required fields:
- `cash_version` — spec version
- `last_updated` — ISO 8601 date
- `publisher` — organization/individual
- `endpoint` — MCP endpoint URL
- `namespaces` — at least one with `suggested` and `description`

Optional fields: `copyright`, `cache_ttl`, `authentication`, `skills`.

## Reporting

Summarize results in a table:

| Check | Requirement | Result |
|-------|------------|--------|
| Tool registration | SHOULD only 3 tools | PASS/FAIL/WARN |
| help() Layer 0 | MUST list namespaces only | PASS/FAIL |
| help(ns) Layer N | MUST NOT include signatures | PASS/FAIL |
| help(ns, fn) Leaf | MUST include parameters | PASS/FAIL |
| call() valid | MUST return response | PASS/FAIL |
| call() unknown ns | MUST return error | PASS/FAIL |
| call() unknown fn | MUST return error | PASS/FAIL |
| call() size gating | MUST gate large responses | PASS/FAIL/SKIP |
| call() sizelimit | SHOULD accept override | PASS/WARN |
| skill() fetch | MUST return text-only | PASS/FAIL |
| skill() unknown | MUST return error | PASS/FAIL |
| Naming conventions | MUST be alphanumeric+underscore | PASS/FAIL |
| Server manifest | Optional | PASS/SKIP |

Use FAIL for MUST violations, WARN for SHOULD violations, SKIP for checks that couldn't be performed.

## Reference

Full CaSH specification: https://aigon.ai/rfc-mcp-cash-model/
