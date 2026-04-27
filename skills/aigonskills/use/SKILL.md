---
name: use
description: View and use a skill from the aigonskills index. Use when the user has found a skill and wants to read it, inspect its metadata, or access its associated files (scripts, examples, images).
---

# Use a skill

Once you've found a skill via search (see the `asexplore` skill), here's how to read it, inspect its metadata, and access its files.

If the aigonskills MCP server is not installed, see the `install` skill.

## Read the skill

Fetch the SKILL.md body by ID, normalized name, URL hash, or body hash:

```
skill(namespace="byid", name="2774")
skill(namespace="bynormalizedname", name="neolabhq_context_engineering_kit_reflect")
skill(namespace="byurlhash", name="af2dd6c3")
skill(namespace="byskillhash", name="85e3696f")
```

The ID and normalized name come from search results. The hashes come from metadata.

## Get metadata

```
call(namespace="aigonskills", function="metadata", kwargs={"id": 2774})
```

Returns:
- `name`, `description`, `repo`, `raw_url` — what the skill is and where it comes from
- `language` — detected language code
- `flags` — `shell`, `scripts`, `tools`, `invocable`
- `gh_stars` — GitHub stars of the source repo
- `file_count` and `files` — associated files in the skill directory
- `url_hash`, `body_hash`, `normalized_name` — alternative lookup keys

## Access associated files

Skills can have associated files (scripts, examples, images, config). These appear in the `files` list in metadata, each with `path`, `size`, `content_type`, and `url`.

### Via MCP (text and images)

Use the `skill` tool with a `path` parameter to fetch a file through MCP:

```
skill(namespace="byid", name="15022", path="skills/examples/fourier/scripts/fft_plot.py")
```

- Text files return as a string
- Images (jpeg/png/gif/webp) return as ImageContent that Claude can see directly
- Other binary files return as base64

### Via API (direct download)

Each file in metadata has a `url` field pointing to the API endpoint:

```
https://skills.aigon.ai/api/files/<file_hash>
```

Use this when you need to download a file to disk, e.g. with `curl` or `wget`:

```bash
curl -o fft_plot.py "https://skills.aigon.ai/api/files/e1cb8096e14ad339"
curl -o spectrum.png "https://skills.aigon.ai/api/files/8fed859a5b4fa9b6"
```

This is useful for images or binary files you want to save locally rather than view inline, or when working outside an MCP-connected client.
