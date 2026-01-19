# Hotcross

<p align="center">
  <img src="assets/hotcross.png" alt="Hotcross" />
</p>

<p align="center">
  <img src="https://badge.mcpx.dev?type=server" alt="MCP Server" />
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv" /></a>
  <img src="https://img.shields.io/github/commit-activity/w/atelierlogos/hotcross" alt="GitHub commit activity" />
</p>


Hotcross is an MCP-powered code intelligence relay that provides persistent and portable context storage using a `mem://` format with [Clickhouse chDB](https://github.com/chdb-io/chdb) and a thoughtfully defined graph-like data model.

## Get an API key

Chat with James for any commercial inquiries.

<a href="https://cal.com/team/atelierlogos/get-a-hotcross-api-key"><img src="https://cal.com/book-with-cal-dark.svg" alt="Book us with Cal.com"></a>

## Features

- **🔐 Authenticated**: API key authentication for secure access
- **💾 Persistent Storage**: Data survives server restarts in portable `.db` files
- **🔍 SQL Interface**: Query data using familiar SQL syntax
- **📊 Schema Auto-Inference**: Tables are automatically created from data structure
- **🧠 Code Intelligence**: Tree-sitter based code analysis with symbol extraction, dependency tracking, and reference finding
- **📝 Session Management**: Track LLM conversation sessions with message history
- **✅ Todo Management**: Built-in todo system with projects, priorities, and tags
- **🔌 MCP Integration**: Full MCP tools and resources support

## Installation

```bash
# Using uv (recommended)
uv pip install -e .
```

## Quick Start

Configure in Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "hotcross": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.server"],
      "cwd": "/path/to/hotcross",
      "env": {
        "DATABASE_URL": "postgresql://user:password@host/database",
        "HOTCROSS_API_KEY": "hc_live_your_key_here"
      }
    }
  }
}
```

Or run directly:

```bash
export DATABASE_URL="postgresql://..."
export HOTCROSS_API_KEY="hc_live_..."
uv run python -m src.server
```

## MCP Tools

All tools require authentication via API key.

### Memory Portal Tools (7)

| Tool | Description |
|------|-------------|
| `memory_write` | Write data to a portal table |
| `memory_query` | Execute SQL queries |
| `memory_delete` | Delete data with conditions |
| `memory_view` | Get portal info, schema, and stats |
| `memory_list_tables` | List all tables in a portal |
| `memory_drop_table` | Drop a table |
| `memory_list_portals` | List all registered portals |

### Code Intelligence Tools (10)

| Tool | Description |
|------|-------------|
| `code_index_file` | Index a single source file |
| `code_index_directory` | Index all files in a directory |
| `code_find_symbol` | Search for symbols by name/kind |
| `code_get_file_symbols` | Get all symbols in a file |
| `code_get_imports` | Get import statements |
| `code_get_exports` | Get exported symbols |
| `code_get_dependencies` | Get dependency graph |
| `code_find_references` | Find symbol references |
| `code_get_stats` | Get index statistics |
| `code_query` | Raw SQL against code tables |

### Project Management Tools (5)

| Tool | Description |
|------|-------------|
| `code_init_project` | Create a new project |
| `code_get_project` | Get project details |
| `code_list_projects` | List all projects |
| `code_update_project` | Update project metadata |
| `code_delete_project` | Delete project and all data |

### Document Management Tools (4)

| Tool | Description |
|------|-------------|
| `code_index_documents` | Index documentation files |
| `code_get_document` | Get document by path |
| `code_list_documents` | List all documents |
| `code_search_documents` | Search documentation |

### Session Management Tools (6)

| Tool | Description |
|------|-------------|
| `session_create` | Create a new LLM conversation session |
| `session_add_message` | Add a message to a session |
| `session_get` | Get session details |
| `session_get_messages` | Get messages from a session |
| `session_list` | List sessions for a project |
| `session_archive` | Archive a session |

### Todo Management Tools (5)

| Tool | Description |
|------|-------------|
| `todo_create` | Create a new todo item |
| `todo_update` | Update a todo item |
| `todo_get` | Get todo details |
| `todo_list` | List todos with filters |
| `todo_delete` | Delete a todo item |

**Total: 37 authenticated tools**

## MCP Resources

Access portals and tables as resources:

- `mem://{namespace}/{portal_id}` - Portal metadata and schema
- `mem://{namespace}/{portal_id}/{table}` - Table data (limited to 1000 rows)

## URI Scheme

Hotcross uses the `mem://` URI scheme:

```
mem://{namespace}/{portal-id}[/{table}][?query]
```

Examples:
- `mem://conversation/default` - Root portal reference
- `mem://conversation/default/messages` - Specific table
- `mem://conversation/default/messages?limit=10` - With query parameters

## Project Structure

```
hotcross/
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── server.py             # FastMCP server with all tools
│   ├── core/
│   │   ├── portal.py         # MemoryPortal class
│   │   ├── database.py       # ChDBAdapter wrapper
│   │   ├── metadata.py       # _mcp_metadata table management
│   │   ├── registry.py       # Portal registry
│   │   ├── auth.py           # AuthManager for PostgreSQL
│   │   └── middleware.py     # @require_auth decorator
│   ├── uri/
│   │   └── parser.py         # mem:// URI parsing
│   ├── models/
│   │   ├── schemas.py        # Pydantic models
│   │   ├── auth.py           # Auth models
│   │   └── code_intel.py     # Code intelligence models
│   └── intel/
│       ├── parser.py         # Tree-sitter parser
│       ├── graph.py          # Code graph operations
│       ├── indexer.py        # File indexing
│       └── rules/            # Language-specific rules
├── tests/
└── examples/
    ├── basic_usage.py
    ├── code_intel_demo.py
    ├── docs_demo.py
    └── project_demo.py
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run linting
uv run ruff check src/

# Run examples
uv run python examples/basic_usage.py
```

## Testing

```bash
# Test authentication
export HOTCROSS_API_KEY="hc_live_..."
export DATABASE_URL="postgresql://..."
uv run python scripts/test_auth.py

# Run test suite
uv run pytest tests/

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run python -m src.server
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string for authentication |
| `HOTCROSS_API_KEY` | Yes | Developer API key (get from your organization admin) |

## Authentication & Pricing

Hotcross uses organization-based authentication:

- **Organizations** subscribe and pay for seats (e.g., 5 developers)
- **Developers** within an org each get their own API key
- Each developer runs the MCP server locally with their key
- Authentication validates against PostgreSQL on every request

**Pricing models supported:**
- Per-organization with seat limits
- Per-developer (1-seat organizations)
- Hybrid (base fee + per-seat)

See [Admin Scripts](scripts/admin/README.md) for provisioning details.

## Acknowledgements

Special thanks to the Model Context Protocol team, and specifically [@idosal](https://github.com/idosal) and [@pja-ant](https://github.com/pja-ant) for the amazing work they are doing on their respective SEPs, which served as the inspirational basis of the `mem://` approach. 

## License

Elastic License 2.0