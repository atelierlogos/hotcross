# Hotcross

<div align="center">
  <img src="assets/hotcross.png" alt="Hotcross Logo" width="200"/>
</div>

<div align="center">

[![License](https://img.shields.io/badge/license-MIT%202.0-blue.svg)](LICENSE.md)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

</div>

Hotcross is an MCP-powered code intelligence relay that provides persistent and portable context storage using a `mem://` format with [Clickhouse chDB](https://github.com/chdb-io/chdb) and a thoughtfully defined graph-like data model.

## Features

- **💾 Persistent Storage**: Data survives server restarts in portable `.db` files
- **🔍 SQL Interface**: Query data using familiar SQL syntax
- **📊 Schema Auto-Inference**: Tables are automatically created from data structure
- **🧠 Code Intelligence**: Tree-sitter based code analysis with symbol extraction, dependency tracking, and reference finding
- **📝 Session Management**: Track LLM conversation sessions with message history
- **✅ Todo Management**: Built-in todo system with projects, priorities, and tags
- **📚 Document Management**: Index and search documentation
- **🔌 MCP Integration**: Full MCP tools and resources support

## Installation

```bash
# Using uvx (recommended - no installation needed)
uvx --from git+https://github.com/atelierlogos/hotcross hotcross

# Or install with uv
uv pip install git+https://github.com/atelierlogos/hotcross

# Or clone for development
git clone https://github.com/atelierlogos/hotcross
cd hotcross
uv pip install -e .
```

## Quick Start

### Configure in Claude Desktop or Kiro

Add to your MCP config:

```json
{
  "mcpServers": {
    "hotcross": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/atelierlogos/hotcross", "hotcross"]
    }
  }
}
```

Or for local development:

```json
{
  "mcpServers": {
    "hotcross": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.server"],
      "cwd": "/path/to/hotcross"
    }
  }
}
```

That's it! All features are available - no authentication or configuration needed.

## Use Cases

- **AI Context Persistence**: Store conversation history and context across sessions
- **Codebase Analysis**: Index and query your entire codebase structure
- **Documentation Management**: Searchable documentation with semantic understanding
- **Project Memory**: Track todos, sessions, and project metadata
- **Team Knowledge Base**: Shared memory portals for team collaboration

## MCP Tools

All 37 tools are available without any authentication.

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
│   │   └── registry.py       # Portal registry
│   ├── uri/
│   │   └── parser.py         # mem:// URI parsing
│   ├── models/
│   │   ├── schemas.py        # Pydantic models
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
# Run test suite
uv run pytest tests/

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run python -m src.server
```

## License

MIT License - See [LICENSE.md](LICENSE.md) for details.

## Acknowledgments

Special thanks to the Model Context Protocol team, and specifically [@idosal](https://github.com/idosal) and [@pja-ant](https://github.com/pja-ant) for the amazing work they are doing on their respective SEPs, which served as the inspirational basis of the `mem://` approach.
