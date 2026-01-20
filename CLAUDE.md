# Hotcross

MCP-powered local static code graph persistence for AI agents.

## Project Overview

This is the hotcross MCP server - it provides persistent memory and code intelligence via the `mem://` URI scheme using ChDB (embedded ClickHouse).

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
```

## Using Hotcross MCP Tools

The hotcross MCP server is available in this project. Use these tools for persistent storage and code analysis.

### Portal URI Convention

**Always use `mem://{project_name}/default` as the portal URI**, where `{project_name}` is the name of the project you're working on (typically the directory name).

Examples:
- Working on hotcross → `mem://hotcross/default`
- Working on myapp → `mem://myapp/default`

This keeps all project data (code intelligence, sessions, todos) in a single persistent database per project.

### Memory Operations
- `memory_write` - Store structured data to a portal table
- `memory_query` - Query data with SQL
- `memory_delete` - Remove data
- `memory_list_portals` - See available portals

### Code Intelligence
When analyzing this codebase or any project:
- `code_init_project` - Create a project for indexing
- `code_index_directory` - Index source files with tree-sitter
- `code_find_symbol` - Search for functions, classes, methods
- `code_get_file_symbols` - Get all symbols in a file
- `code_get_dependencies` - Understand import relationships
- `code_find_references` - Find where symbols are used

### Session & Todo Management
- `session_create` / `session_add_message` - Track conversation history
- `todo_create` / `todo_list` - Manage project tasks

## Project Structure

- `src/server.py` - FastMCP server with all tool definitions
- `src/core/` - Portal, database, auth, and registry logic
- `src/intel/` - Tree-sitter parsing and code graph operations
- `src/models/` - Pydantic schemas
- `src/uri/` - mem:// URI parsing
- `tests/` - pytest test suite
- `examples/` - Usage examples
