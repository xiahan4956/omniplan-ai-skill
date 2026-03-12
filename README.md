# omniplan-mcp

MCP server for [OmniPlan 4](https://www.omnigroup.com/omniplan) on macOS. Manage your project tasks with natural language via Claude or any MCP-compatible client.

## Requirements

- macOS
- OmniPlan 4 (must be running)
- Python 3.11+
- Automation permission granted to your terminal / MCP host app

## Installation

```bash
pip install git+https://github.com/xiahan4956/omniplan-mcp.git
```

Or clone and install in editable mode:

```bash
git clone https://github.com/xiahan4956/omniplan-mcp.git
cd omniplan-mcp
pip install -e .
```

### Grant Automation Permission

The first time you run the server, macOS may prompt for Automation access. If not, grant it manually:

**System Settings → Privacy & Security → Automation** — enable OmniPlan for your terminal or the app running the MCP server.

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "omniplan": {
      "command": "python3",
      "args": ["-m", "omniplan_mcp"]
    }
  }
}
```

Then restart Claude Desktop.

## Tools

| Tool | Description |
|------|-------------|
| `list_documents` | List all currently open OmniPlan documents |
| `query_tasks` | Search and filter tasks by keyword, type, completion, color, or date range |
| `get_task` | Get full details of a task by ID |
| `create_task` | Create a new task under a parent task or project root |
| `update_task` | Update task fields (title, note, dates, completion, color) |
| `delete_task` | Delete a task by ID |

All tools accept an optional `document_name` parameter. If omitted, the frontmost open document is used.

### query_tasks parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `keyword` | string | Filter by title or note (case-insensitive) |
| `task_type` | string | `task` / `group` / `milestone` / `hammock` |
| `completed` | boolean | `true` = completed only, `false` = incomplete only |
| `color` | string | `red` / `orange` / `yellow` / `green` / `blue` / `purple` / `brown` / `gray` / `clear` |
| `due_before` | string | ISO date, e.g. `2025-12-31` |
| `due_after` | string | ISO date, e.g. `2025-01-01` |
| `limit` | int | Max results (default 50) |

### update_task parameters

Pass only the fields you want to change. Set `completed: true` to mark a task done, or `color: "clear"` to reset the bar color.

## Example Prompts

> "Show me all incomplete tasks due this week in my project."

> "Create a milestone called 'Beta Launch' under the Deployment group."

> "Mark task 42 as complete and set its bar color to green."

> "What tasks are assigned the red color?"

## License

MIT
