# Hotcross

<p align="center">
  <img src="assets/hotcross.png" alt="Hotcross" />
</p>

<p align="center">
  <img src="https://badge.mcpx.dev?type=server" alt="MCP Server" />
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv" /></a>
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="GitHub commit activity" />
  <img src="https://img.shields.io/github/commit-activity/w/atelierlogos/hotcross" alt="GitHub commit activity" />
  <img src="https://img.shields.io/github/stars/atelierlogos/hotcross?style=social" alt="GitHub stars" />
</p>

> **MCP-powered local static code graph persistence for AI agents**

Hotcross provides a `mem://` URI scheme for storing and querying structured data using [Clickhouse chDB](https://github.com/chdb-io/chdb), combined with tree-sitter-based code analysis for deep codebase understanding.

## Why Hotcross?

- **Persistent Memory**: Your AI conversations and code analysis survive restarts
- **Portable Storage**: ChDB files are self-contained and easy to backup/share
- **SQL-Powered**: Query your data with familiar SQL syntax
- **Code-Aware**: Understands symbols, dependencies, and references across languages
- **Organization-Ready**: Built-in multi-tenant auth with seat management

## Get an API Key

Need support? Book a call with James:

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

### Claude Code CLI (Recommended)

The fastest way to get started with Claude Code:

```bash
# Self-hosted (free tier)
claude mcp add hotcross -- uvx --from git+https://github.com/atelierlogos/hotcross hotcross

# Commercial (with license key)
claude mcp add hotcross -e HOTCROSS_LICENSE=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9... -- uvx --from git+https://github.com/atelierlogos/hotcross hotcross
```

To verify the installation:

```bash
claude mcp list
```

### Manual Configuration

#### OSS

No configuration needed! Just run it:

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

## Configuring with CLAUDE.md

You can use a `CLAUDE.md` file in your project root to provide Claude Code with context about how to use Hotcross in your project. This file acts as persistent instructions that Claude reads at the start of each session.

### Example CLAUDE.md

```markdown
# Project Configuration

## Hotcross Memory Portal

This project uses Hotcross for persistent code intelligence and memory.

### Portal Configuration
- **Portal URI**: `mem://myproject/default`
- **Project Name**: `myproject`

### Tool Usage Guidelines

When working on this codebase:

1. **Index the codebase** at the start of a session if not already indexed:
   - Use `code_init_project` to initialize the project
   - Use `code_index_directory` to index source files

2. **Use code intelligence** for navigation:
   - Use `code_find_symbol` to locate functions and classes
   - Use `code_get_dependencies` to understand file relationships
   - Use `code_find_references` to find usages of symbols

3. **Track work with todos**:
   - Use `todo_create` for new tasks
   - Use `todo_list` to see current work items

4. **Persist session context**:
   - Use `session_create` to start a new conversation session
   - Use `session_add_message` to save important context

### Project-Specific Paths
- Source code: `src/`
- Tests: `tests/`
- Documentation: `docs/`
```

### What to Include in CLAUDE.md

| Section | Purpose |
|---------|---------|
| Portal URI | Define the `mem://` URI for your project's data |
| Project Name | Consistent project identifier across sessions |
| Tool Usage | Guidelines for which Hotcross tools to use and when |
| Directory Structure | Help Claude understand your codebase layout |
| Indexing Instructions | How to set up code intelligence for the project |
| Workflow Preferences | Custom workflows for todos, sessions, etc. |

### Multiple CLAUDE.md Files

You can have multiple `CLAUDE.md` files at different levels:
- **Root `CLAUDE.md`**: Project-wide configuration
- **Subdirectory `CLAUDE.md`**: Module-specific instructions (e.g., `src/api/CLAUDE.md`)

Claude Code will read all applicable `CLAUDE.md` files when working in a directory.

## Use Cases

- **AI Context Persistence**: Store conversation history and context across sessions
- **Codebase Analysis**: Index and query your entire codebase structure
- **Documentation Management**: Searchable documentation with semantic understanding
- **Project Memory**: Track todos, sessions, and project metadata
- **Team Knowledge Base**: Shared memory portals for team collaboration

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

**Total: 37 tools** (28 tools on Free tier, 37 tools on Commercial)

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

## Storage Format

Hotcross uses [chDB](https://github.com/chdb-io/chdb) (embedded ClickHouse) for storage. Unlike SQLite which uses a single `.db` file, ClickHouse stores data as a **directory structure**:

```
~/.memory-portals/
└── myproject/
    └── default.db/           # This is a directory, not a file
        ├── data/default/     # Columnar table data
        │   ├── _ci_symbols/
        │   ├── _ci_files/
        │   └── ...
        ├── store/            # Internal ClickHouse storage
        ├── metadata/         # Table schemas
        └── tmp/              # Temporary query files
```

**Why directories instead of a single file?**

ClickHouse is a columnar database optimized for analytics:
- **Columnar storage**: Each column stored and compressed separately
- **Better compression**: Similar data types compress efficiently together
- **Faster queries**: Reads only the columns needed for each query
- **Parallel I/O**: Multiple files can be read simultaneously

**Still fully SQL-queryable**

The directory structure is an implementation detail. You query data with standard SQL:

```sql
SELECT * FROM _ci_symbols WHERE kind = 'function' LIMIT 10
```

**Portable and self-contained**

Each `.db` directory is self-contained. You can zip it up and move it to another machine:

```bash
# Backup a portal
zip -r myproject-backup.zip ~/.memory-portals/myproject/default.db

# Restore on another machine
unzip myproject-backup.zip -d ~/.memory-portals/myproject/
```

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
# Test authentication (for development only)
export HOTCROSS_API_KEY="hc_live_..."
export DATABASE_URL="postgresql://..."  # Only needed for local development
uv run python scripts/test_auth.py

# Run test suite
uv run pytest tests/

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run python -m src.server
```

## Support

- 🐛 [Issue Tracker](https://github.com/atelierlogos/hotcross/issues)
- 💬 [Discussions](https://github.com/atelierlogos/hotcross/discussions)
- 📧 Email: support@atelierlogos.com

## Acknowledgements

Special thanks to the Model Context Protocol team, and specifically [@idosal](https://github.com/idosal) and [@pja-ant](https://github.com/pja-ant) for the amazing work they are doing on their respective SEPs, which served as the inspirational basis of the `mem://` approach. 

## License

MIT