---
name: install
description: Install the aigonskills MCP server into Claude Code or other clients. Use when the user asks to "install aigonskills", "add the skills server", "set up aigonskills MCP", or "connect to aigonskills".
---

# Install aigonskills MCP Server

Register the aigonskills MCP server so skill discovery tools become available. No API key required.

**Server endpoint:** `https://aigonskills.aigon.ai/sse` (SSE transport)

## Method 1: Claude Code CLI

1. Check if the server is already configured:
   ```
   claude mcp list
   ```
   If `aigonskills` already appears, tell the user it's already installed and stop.

2. Install the server:
   ```
   claude mcp add --transport sse aigonskills https://aigonskills.aigon.ai/sse
   ```

3. Verify with `claude mcp list` or the `/mcp` command inside Claude Code.

4. **Restart Claude Code** (or start a new session) for the MCP tools to become available.

To remove: `claude mcp remove aigonskills`

## Method 2: Configuration file (manual)

Claude Code stores MCP server config in `.claude/settings.local.json` (project-level) or `~/.claude/settings.json` (global). Add the server entry manually if preferred:

```json
{
  "mcpServers": {
    "aigonskills": {
      "type": "sse",
      "url": "https://aigonskills.aigon.ai/sse"
    }
  }
}
```

## Method 3: Claude Desktop (mcp-remote)

Claude Desktop does not support SSE transport natively. Use `mcp-remote` to bridge the connection.

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aigonskills": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://aigonskills.aigon.ai/sse"]
    }
  }
}
```

This spawns a local process via `npx mcp-remote` that proxies the remote SSE server as a local stdio MCP server that Claude Desktop can talk to. Requires Node.js/npm installed.

## Method 4: Cursor

Go to Cursor settings → MCP → Add new server. Set type to `sse` and URL to `https://aigonskills.aigon.ai/sse`.

## Method 5: Programmatic (Python)

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async with sse_client("https://aigonskills.aigon.ai/sse") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("call", {
            "namespace": "aigonskills",
            "function": "stats",
        })
        print(result.content[0].text)
```

## Verify it works

After restarting Claude Code, run `/mcp` and confirm `aigonskills` shows as connected. If it does, the MCP tools are available and ready to use.

Once installed, see the `asexplore` skill to search and discover skills, and the `use` skill to read and access them.

## Install the as* management skills

For optimal use of the aigonskills server, install the `as*` skill set as local slash commands. These are available in the aigonskills index — search for source `skloesch/aigonskills`:

```
call(namespace="aigonskills", function="list", kwargs={"query": "as", "source": "skloesch/aigonskills"})
```

Then install each one via `asinstall` (or manually download and place in `~/.claude/skills/`):

- `/asexplore` — search and discover skills
- `/asadd` — add a skill reference to CLAUDE.md/AGENT.md
- `/asremove` — remove a skill reference
- `/asrun` — run a referenced skill from remote
- `/asinstall` — install a skill locally as a slash command
- `/asuninstall` — remove a locally installed skill

These give you a complete workflow: explore → add/install → run → remove/uninstall.
