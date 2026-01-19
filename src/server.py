"""FastMCP server for Memory Portals."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from src.core.registry import PortalRegistry
from src.core.middleware import require_auth, init_auth, is_auth_enabled
from src.uri.parser import MemoryURI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Memory Portals")

registry = PortalRegistry()


@mcp.tool()
@require_auth
def memory_write(
    portal_uri: str = Field(description="mem:// URI of the portal (e.g., mem://conversation/default)"),
    table: str = Field(description="Target table name"),
    data: list[dict[str, Any]] = Field(description="Array of records to insert"),
) -> dict[str, Any]:
    """Write data to a memory portal.

    Creates the table if it doesn't exist, inferring schema from the data.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)
        result = portal.write(table, data)

        return {
            "success": True,
            "rows_written": result.rows_written,
            "table": result.table,
            "portal_uri": result.portal_uri,
        }
    except Exception as e:
        logger.error(f"memory/write error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def memory_query(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    sql: str = Field(description="SQL query to execute (SELECT recommended)"),
) -> dict[str, Any]:
    """Query a memory portal using SQL.

    Returns query results as an array of records.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)
        result = portal.query(sql)

        return {
            "success": True,
            "data": result.data,
            "row_count": result.row_count,
            "column_names": result.column_names,
            "execution_time_ms": result.execution_time_ms,
        }
    except Exception as e:
        logger.error(f"memory/query error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def memory_delete(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    table: str = Field(description="Table to delete from"),
    where: dict[str, Any] | None = Field(default=None, description="Conditions for deletion (key-value equality)"),
    delete_all: bool = Field(default=False, description="Delete all rows (requires explicit True)"),
) -> dict[str, Any]:
    """Delete data from a memory portal.

    Either specify 'where' conditions or set 'delete_all' to True.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        # Handle Field defaults not being properly converted
        actual_where = where if isinstance(where, dict) else None
        actual_delete_all = delete_all if isinstance(delete_all, bool) else False

        result = portal.delete(table, where=actual_where, delete_all=actual_delete_all)

        return {
            "success": True,
            "rows_deleted": result.rows_deleted,
            "table": result.table,
            "portal_uri": result.portal_uri,
        }
    except Exception as e:
        logger.error(f"memory/delete error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def memory_view(
    portal_uri: str = Field(description="mem:// URI to view"),
) -> dict[str, Any]:
    """Get portal information including schema and statistics.

    Returns portal metadata, table schemas, and usage statistics.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)
        info = portal.get_info()

        schema_dict = {
            name: {
                "name": ts.name,
                "columns": [
                    {"name": c.name, "type": c.type, "primary": c.primary, "nullable": c.nullable}
                    for c in ts.columns
                ],
            }
            for name, ts in info.tables_schema.items()
        }

        return {
            "success": True,
            "uri": info.uri,
            "name": info.name,
            "description": info.description,
            "db_path": info.db_path,
            "schema": schema_dict,
            "stats": {
                "total_rows": info.stats.total_rows,
                "total_tables": info.stats.total_tables,
                "size_bytes": info.stats.size_bytes,
                "table_stats": info.stats.table_stats,
            },
            "created_at": info.created_at.isoformat() if info.created_at else None,
        }
    except Exception as e:
        logger.error(f"memory/view error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def memory_list_tables(
    portal_uri: str = Field(description="mem:// URI of the portal"),
) -> dict[str, Any]:
    """List all tables in a memory portal."""
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)
        tables = portal.get_tables()

        return {
            "success": True,
            "portal_uri": portal.uri,
            "tables": tables,
        }
    except Exception as e:
        logger.error(f"memory/list_tables error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def memory_drop_table(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    table: str = Field(description="Table name to drop"),
) -> dict[str, Any]:
    """Drop a table from a memory portal.

    This permanently deletes the table and all its data.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)
        portal.drop_table(table)

        return {
            "success": True,
            "portal_uri": portal.uri,
            "table_dropped": table,
        }
    except Exception as e:
        logger.error(f"memory/drop_table error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def memory_list_portals() -> dict[str, Any]:
    """List all registered memory portals.

    Also discovers portals from the filesystem that haven't been registered.
    """
    try:
        registry.load_discovered()
        portals = registry.list_portals()

        return {
            "success": True,
            "portals": portals,
            "count": len(portals),
        }
    except Exception as e:
        logger.error(f"memory/list_portals error: {e}")
        return {"success": False, "error": str(e)}


@mcp.resource("mem://{namespace}/{portal_id}")
def get_portal_resource(namespace: str, portal_id: str) -> str:
    """Get portal information as a resource.

    Returns JSON with schema, stats, and metadata.
    """
    try:
        portal = registry.get_or_create(namespace, portal_id)
        info = portal.get_info()

        schema_dict = {
            name: {
                "name": ts.name,
                "columns": [
                    {"name": c.name, "type": c.type, "primary": c.primary}
                    for c in ts.columns
                ],
            }
            for name, ts in info.tables_schema.items()
        }

        return json.dumps({
            "uri": info.uri,
            "name": info.name,
            "description": info.description,
            "db_path": info.db_path,
            "schema": schema_dict,
            "stats": {
                "total_rows": info.stats.total_rows,
                "total_tables": info.stats.total_tables,
                "size_bytes": info.stats.size_bytes,
                "table_stats": info.stats.table_stats,
            },
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("mem://{namespace}/{portal_id}/{table}")
def get_table_resource(namespace: str, portal_id: str, table: str) -> str:
    """Get table data as a resource.

    Returns JSON array of all rows in the table (limited to 1000 rows).
    """
    try:
        portal = registry.get_or_create(namespace, portal_id)
        result = portal.query(f"SELECT * FROM `{table}` LIMIT 1000")

        return json.dumps(result.data, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def main() -> None:
    """Run the Memory Portals MCP server."""
    logger.info("Starting Memory Portals MCP server")
    
    # Initialize authentication (required)
    init_auth()
    logger.info("🔐 Authentication enabled - API keys required")
    logger.info("   Set HOTCROSS_API_KEY environment variable to authenticate")
    
    registry.load_discovered()
    mcp.run()


if __name__ == "__main__":
    main()


# ============================================================================
# Code Intelligence Tools
# ============================================================================

from src.intel.indexer import CodeIndexer


@mcp.tool()
@require_auth
def code_index_file(
    portal_uri: str = Field(description="mem:// URI of the portal for code intelligence storage"),
    file_path: str = Field(description="Path to source file to index"),
    force: bool = Field(default=False, description="Force re-indexing even if unchanged"),
) -> dict[str, Any]:
    """Index a single source file for code intelligence.

    Extracts symbols, types, imports, exports, scopes, and references using tree-sitter.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)
        indexer = CodeIndexer(portal)

        result = indexer.index_file(file_path, force=force)

        return {
            "success": True,
            **result,
        }
    except Exception as e:
        logger.error(f"code_index_file error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_index_directory(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    directory: str = Field(description="Directory path to index"),
    project_name: str | None = Field(default=None, description="Project name (creates if doesn't exist)"),
    recursive: bool = Field(default=True, description="Recursively index subdirectories"),
    force: bool = Field(default=False, description="Force re-indexing of all files"),
    file_patterns: list[str] | None = Field(default=None, description="Optional glob patterns to filter files"),
) -> dict[str, Any]:
    """Index all supported source files in a directory.

    Supports Python, JavaScript, TypeScript, and other languages with tree-sitter parsers.
    If project_name is provided, creates or uses that project for indexing.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        from src.intel.indexer import CodeIndexer
        from pathlib import Path

        # Handle Field defaults
        actual_patterns = file_patterns if isinstance(file_patterns, list) else None
        actual_project = project_name if isinstance(project_name, str) else None

        # Get or create project
        project_id = None
        if actual_project:
            graph = CodeGraph(portal)
            project = graph.get_project(actual_project)
            
            if not project:
                # Create new project
                project_id = graph.create_project(
                    project_name=actual_project,
                    root_path=str(Path(directory).resolve()),
                    description=f"Auto-created project for {directory}",
                )
            else:
                project_id = project["project_id"]

        indexer = CodeIndexer(portal, project_id=project_id)

        stats = indexer.index_directory(
            directory,
            recursive=recursive,
            force=force,
            file_patterns=actual_patterns,
        )

        result = {
            "success": True,
            **stats.to_dict(),
        }
        
        if project_id:
            result["project_id"] = project_id
            result["project_name"] = actual_project

        return result
    except Exception as e:
        logger.error(f"code_index_directory error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_find_symbol(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    name: str | None = Field(default=None, description="Symbol name to search for (supports wildcards)"),
    kind: str | None = Field(default=None, description="Symbol kind filter (function, class, method, variable)"),
    file_pattern: str | None = Field(default=None, description="File path pattern to filter"),
    limit: int = Field(default=100, description="Maximum number of results"),
) -> dict[str, Any]:
    """Search for symbols by name, kind, or file pattern.

    Returns matching symbols with their locations and metadata.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        # Handle Field defaults
        actual_name = name if isinstance(name, str) else None
        actual_kind = kind if isinstance(kind, str) else None
        actual_pattern = file_pattern if isinstance(file_pattern, str) else None

        symbols = graph.find_symbols(
            name=actual_name,
            kind=actual_kind,
            file_pattern=actual_pattern,
            limit=limit,
        )

        return {
            "success": True,
            "symbols": symbols,
            "count": len(symbols),
        }
    except Exception as e:
        logger.error(f"code_find_symbol error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_get_file_symbols(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    file_path: str = Field(description="File path to get symbols from"),
) -> dict[str, Any]:
    """Get all symbols defined in a specific file.

    Returns functions, classes, methods, and variables with their locations.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        symbols = graph.get_file_symbols(file_path)

        return {
            "success": True,
            "file_path": file_path,
            "symbols": symbols,
            "count": len(symbols),
        }
    except Exception as e:
        logger.error(f"code_get_file_symbols error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_get_imports(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    file_path: str = Field(description="File path to get imports from"),
) -> dict[str, Any]:
    """Get all import statements from a file.

    Returns imported modules and names with their locations.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        imports = graph.get_file_imports(file_path)

        return {
            "success": True,
            "file_path": file_path,
            "imports": imports,
            "count": len(imports),
        }
    except Exception as e:
        logger.error(f"code_get_imports error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_get_exports(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    file_path: str = Field(description="File path to get exports from"),
) -> dict[str, Any]:
    """Get all exports from a file (public API surface).

    Returns exported symbols and their locations.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        exports = graph.get_file_exports(file_path)

        return {
            "success": True,
            "file_path": file_path,
            "exports": exports,
            "count": len(exports),
        }
    except Exception as e:
        logger.error(f"code_get_exports error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_get_dependencies(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    file_path: str | None = Field(default=None, description="File path to get dependencies for (or all if None)"),
) -> dict[str, Any]:
    """Get dependency graph showing which files import which modules.

    Returns file-to-file dependencies based on import statements.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        # Handle Field default
        actual_file = file_path if isinstance(file_path, str) else None

        dependencies = graph.get_dependencies(actual_file)

        return {
            "success": True,
            "dependencies": dependencies,
            "count": len(dependencies),
        }
    except Exception as e:
        logger.error(f"code_get_dependencies error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_find_references(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    symbol_name: str = Field(description="Symbol name to find references for"),
    file_path: str | None = Field(default=None, description="Optional file path to limit search"),
) -> dict[str, Any]:
    """Find all references to a symbol (unresolved, syntax-based).

    Returns all locations where the symbol name appears in the code.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        # Handle Field default
        actual_file = file_path if isinstance(file_path, str) else None

        references = graph.find_references(symbol_name, actual_file)

        return {
            "success": True,
            "symbol_name": symbol_name,
            "references": references,
            "count": len(references),
        }
    except Exception as e:
        logger.error(f"code_find_references error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_get_stats(
    portal_uri: str = Field(description="mem:// URI of the portal"),
) -> dict[str, Any]:
    """Get code intelligence index statistics.

    Returns counts of indexed files, symbols, types, imports, etc.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        stats = graph.get_stats()

        return {
            "success": True,
            **stats,
        }
    except Exception as e:
        logger.error(f"code_get_stats error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_query(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    sql: str = Field(description="SQL query against _ci_* tables"),
) -> dict[str, Any]:
    """Execute raw SQL queries against code intelligence tables.

    Tables: _ci_files, _ci_symbols, _ci_types, _ci_imports, _ci_exports, _ci_scopes, _ci_references
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        result = portal.query(sql)

        return {
            "success": True,
            "data": result.data,
            "row_count": result.row_count,
            "column_names": result.column_names,
        }
    except Exception as e:
        logger.error(f"code_query error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# Code Intelligence Project Management Tools
# ============================================================================

@mcp.tool()
@require_auth
def code_init_project(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    project_name: str = Field(description="Project name"),
    root_path: str = Field(description="Root directory path"),
    description: str | None = Field(default=None, description="Project description"),
    version: str | None = Field(default=None, description="Project version"),
    git_remote: str | None = Field(default=None, description="Git remote URL"),
    git_branch: str | None = Field(default=None, description="Git branch name"),
    git_commit: str | None = Field(default=None, description="Git commit hash"),
) -> dict[str, Any]:
    """Initialize a new code intelligence project.

    Creates a project entry for organizing indexed code.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        # Handle Field defaults
        actual_desc = description if isinstance(description, str) else None
        actual_ver = version if isinstance(version, str) else None
        actual_remote = git_remote if isinstance(git_remote, str) else None
        actual_branch = git_branch if isinstance(git_branch, str) else None
        actual_commit = git_commit if isinstance(git_commit, str) else None

        project_id = graph.create_project(
            project_name=project_name,
            root_path=root_path,
            description=actual_desc,
            version=actual_ver,
            git_remote=actual_remote,
            git_branch=actual_branch,
            git_commit=actual_commit,
        )

        return {
            "success": True,
            "project_id": project_id,
            "project_name": project_name,
            "root_path": root_path,
        }
    except Exception as e:
        logger.error(f"code_init_project error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_get_project(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    project_name: str = Field(description="Project name"),
) -> dict[str, Any]:
    """Get project information by name.

    Returns project metadata including ID, paths, and git info.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        project = graph.get_project(project_name)

        if not project:
            return {
                "success": False,
                "error": f"Project '{project_name}' not found",
            }

        return {
            "success": True,
            "project": project,
        }
    except Exception as e:
        logger.error(f"code_get_project error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_list_projects(
    portal_uri: str = Field(description="mem:// URI of the portal"),
) -> dict[str, Any]:
    """List all code intelligence projects.

    Returns all projects with their metadata.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        projects = graph.list_projects()

        return {
            "success": True,
            "projects": projects,
            "count": len(projects),
        }
    except Exception as e:
        logger.error(f"code_list_projects error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_update_project(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    project_id: str = Field(description="Project ID to update"),
    description: str | None = Field(default=None, description="New description"),
    version: str | None = Field(default=None, description="New version"),
    git_branch: str | None = Field(default=None, description="New git branch"),
    git_commit: str | None = Field(default=None, description="New git commit"),
) -> dict[str, Any]:
    """Update project metadata.

    Updates project information like version, description, or git info.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        # Handle Field defaults
        actual_desc = description if isinstance(description, str) else None
        actual_ver = version if isinstance(version, str) else None
        actual_branch = git_branch if isinstance(git_branch, str) else None
        actual_commit = git_commit if isinstance(git_commit, str) else None

        graph.update_project(
            project_id=project_id,
            description=actual_desc,
            version=actual_ver,
            git_branch=actual_branch,
            git_commit=actual_commit,
        )

        return {
            "success": True,
            "project_id": project_id,
            "message": "Project updated successfully",
        }
    except Exception as e:
        logger.error(f"code_update_project error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_delete_project(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    project_id: str = Field(description="Project ID to delete"),
) -> dict[str, Any]:
    """Delete a project and all its indexed data.

    WARNING: This permanently deletes all code intelligence data for the project.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        graph = CodeGraph(portal)

        graph.delete_project(project_id)

        return {
            "success": True,
            "project_id": project_id,
            "message": "Project and all data deleted successfully",
        }
    except Exception as e:
        logger.error(f"code_delete_project error: {e}")
        return {"success": False, "error": str(e)}



# ============================================================================
# Code Intelligence Document Management Tools
# ============================================================================

@mcp.tool()
@require_auth
def code_index_documents(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    directory: str = Field(description="Directory path to index"),
    project_name: str | None = Field(default=None, description="Project name"),
    recursive: bool = Field(default=True, description="Recursively search subdirectories"),
) -> dict[str, Any]:
    """Index documentation files (README, *.md, docs/, etc.).

    Automatically finds and indexes markdown, RST, and text documentation.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        from src.intel.indexer import CodeIndexer

        # Handle Field defaults
        actual_project = project_name if isinstance(project_name, str) else None

        # Get or create project
        project_id = None
        if actual_project:
            graph = CodeGraph(portal)
            project = graph.get_project(actual_project)
            
            if project:
                project_id = project["project_id"]

        indexer = CodeIndexer(portal, project_id=project_id)
        stats = indexer.index_documents(directory, recursive=recursive)

        result = {
            "success": True,
            **stats,
        }
        
        if project_id:
            result["project_id"] = project_id
            result["project_name"] = actual_project

        return result
    except Exception as e:
        logger.error(f"code_index_documents error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_get_document(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    file_path: str = Field(description="Document file path"),
    project_name: str | None = Field(default=None, description="Optional project name"),
) -> dict[str, Any]:
    """Get a documentation file by path.

    Returns the full document content and metadata.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        
        # Handle Field defaults
        actual_project = project_name if isinstance(project_name, str) else None

        # Get project ID if provided
        project_id = None
        if actual_project:
            graph = CodeGraph(portal)
            project = graph.get_project(actual_project)
            if project:
                project_id = project["project_id"]
        else:
            graph = CodeGraph(portal)

        document = graph.get_document(file_path, project_id=project_id)

        if not document:
            return {
                "success": False,
                "error": f"Document '{file_path}' not found",
            }

        return {
            "success": True,
            "document": document,
        }
    except Exception as e:
        logger.error(f"code_get_document error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_list_documents(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    project_name: str | None = Field(default=None, description="Optional project name filter"),
    doc_type: str | None = Field(default=None, description="Optional document type filter"),
) -> dict[str, Any]:
    """List all documentation files.

    Returns document metadata without full content.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        
        # Handle Field defaults
        actual_project = project_name if isinstance(project_name, str) else None
        actual_type = doc_type if isinstance(doc_type, str) else None

        # Get project ID if provided
        project_id = None
        if actual_project:
            graph = CodeGraph(portal)
            project = graph.get_project(actual_project)
            if project:
                project_id = project["project_id"]
        else:
            graph = CodeGraph(portal)

        documents = graph.list_documents(project_id=project_id, doc_type=actual_type)

        return {
            "success": True,
            "documents": documents,
            "count": len(documents),
        }
    except Exception as e:
        logger.error(f"code_list_documents error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def code_search_documents(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    query: str = Field(description="Search query"),
    project_name: str | None = Field(default=None, description="Optional project name filter"),
    limit: int = Field(default=10, description="Maximum results"),
) -> dict[str, Any]:
    """Search documentation by content.

    Performs text search across all indexed documentation.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph
        
        # Handle Field defaults
        actual_project = project_name if isinstance(project_name, str) else None

        # Get project ID if provided
        project_id = None
        if actual_project:
            graph = CodeGraph(portal)
            project = graph.get_project(actual_project)
            if project:
                project_id = project["project_id"]
        else:
            graph = CodeGraph(portal)

        results = graph.search_documents(query, project_id=project_id, limit=limit)

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": query,
        }
    except Exception as e:
        logger.error(f"code_search_documents error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# Session Management Tools
# ============================================================================

@mcp.tool()
@require_auth
def session_create(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    title: str = Field(description="Session title"),
    project_name: str = Field(description="Project name"),
    description: str | None = Field(default=None, description="Optional session description"),
    model: str | None = Field(default=None, description="LLM model name (e.g., 'gpt-4', 'claude-3')"),
    provider: str | None = Field(default=None, description="LLM provider (e.g., 'openai', 'anthropic')"),
) -> dict[str, Any]:
    """Create a new LLM conversation session.
    
    Sessions allow you to persist LLM conversations within a project.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        project = graph.get_project(project_name)
        if not project:
            return {"success": False, "error": f"Project '{project_name}' not found"}

        session_id = graph.create_session(
            title=title,
            project_id=project["project_id"],
            description=description,
            model=model,
            provider=provider,
        )

        return {
            "success": True,
            "session_id": session_id,
            "title": title,
            "project_name": project_name,
        }
    except Exception as e:
        logger.error(f"session_create error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def session_add_message(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    session_id: str = Field(description="Session ID"),
    role: str = Field(description="Message role (user, assistant, system)"),
    content: str = Field(description="Message content"),
    project_name: str = Field(description="Project name"),
    token_count: int = Field(default=0, description="Token count for this message"),
) -> dict[str, Any]:
    """Add a message to a session.
    
    Use this to persist LLM conversation messages.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        project = graph.get_project(project_name)
        if not project:
            return {"success": False, "error": f"Project '{project_name}' not found"}

        message_id = graph.add_message(
            session_id=session_id,
            role=role,
            content=content,
            project_id=project["project_id"],
            token_count=token_count,
        )

        return {
            "success": True,
            "message_id": message_id,
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"session_add_message error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def session_get(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    session_id: str = Field(description="Session ID"),
) -> dict[str, Any]:
    """Get session details.
    
    Returns session metadata including message count and token usage.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        session = graph.get_session(session_id)

        if not session:
            return {"success": False, "error": f"Session '{session_id}' not found"}

        return {
            "success": True,
            "session": session,
        }
    except Exception as e:
        logger.error(f"session_get error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def session_get_messages(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    session_id: str = Field(description="Session ID"),
    limit: int = Field(default=100, description="Maximum number of messages"),
) -> dict[str, Any]:
    """Get messages from a session.
    
    Returns messages in chronological order.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        messages = graph.get_session_messages(session_id, limit=limit)

        return {
            "success": True,
            "messages": messages,
            "count": len(messages),
        }
    except Exception as e:
        logger.error(f"session_get_messages error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def session_list(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    project_name: str = Field(description="Project name"),
    include_archived: bool = Field(default=False, description="Include archived sessions"),
    limit: int = Field(default=50, description="Maximum number of sessions"),
) -> dict[str, Any]:
    """List sessions for a project.
    
    Returns sessions ordered by most recently updated.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        project = graph.get_project(project_name)
        if not project:
            return {"success": False, "error": f"Project '{project_name}' not found"}

        sessions = graph.list_sessions(
            project_id=project["project_id"],
            include_archived=include_archived,
            limit=limit,
        )

        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions),
        }
    except Exception as e:
        logger.error(f"session_list error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def session_archive(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    session_id: str = Field(description="Session ID"),
) -> dict[str, Any]:
    """Archive a session.
    
    Archived sessions are hidden from default listings but not deleted.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        graph.archive_session(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "message": "Session archived",
        }
    except Exception as e:
        logger.error(f"session_archive error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# Todo Management Tools
# ============================================================================

@mcp.tool()
@require_auth
def todo_create(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    title: str = Field(description="Todo title"),
    project_name: str = Field(description="Project name"),
    description: str | None = Field(default=None, description="Optional description"),
    status: str = Field(default="open", description="Status (open, in_progress, completed, blocked)"),
    priority: str = Field(default="medium", description="Priority (low, medium, high, urgent)"),
    file_path: str | None = Field(default=None, description="Optional file path reference"),
    line_number: int | None = Field(default=None, description="Optional line number reference"),
    assigned_to: str | None = Field(default=None, description="Optional assignee"),
    due_date: str | None = Field(default=None, description="Optional due date (ISO format)"),
    tags: list[str] | None = Field(default=None, description="Optional tags"),
) -> dict[str, Any]:
    """Create a new todo item.
    
    Todos can be linked to specific files and lines for code-related tasks.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        project = graph.get_project(project_name)
        if not project:
            return {"success": False, "error": f"Project '{project_name}' not found"}

        todo_id = graph.create_todo(
            title=title,
            project_id=project["project_id"],
            description=description,
            status=status,
            priority=priority,
            file_path=file_path,
            line_number=line_number,
            assigned_to=assigned_to,
            due_date=due_date,
            tags=tags,
        )

        return {
            "success": True,
            "todo_id": todo_id,
            "title": title,
            "project_name": project_name,
        }
    except Exception as e:
        logger.error(f"todo_create error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def todo_update(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    todo_id: str = Field(description="Todo ID"),
    status: str | None = Field(default=None, description="New status"),
    priority: str | None = Field(default=None, description="New priority"),
    description: str | None = Field(default=None, description="New description"),
    assigned_to: str | None = Field(default=None, description="New assignee"),
    due_date: str | None = Field(default=None, description="New due date"),
    tags: list[str] | None = Field(default=None, description="New tags"),
) -> dict[str, Any]:
    """Update a todo item.
    
    Only provided fields will be updated.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        graph.update_todo(
            todo_id=todo_id,
            status=status,
            priority=priority,
            description=description,
            assigned_to=assigned_to,
            due_date=due_date,
            tags=tags,
        )

        return {
            "success": True,
            "todo_id": todo_id,
            "message": "Todo updated",
        }
    except Exception as e:
        logger.error(f"todo_update error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def todo_get(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    todo_id: str = Field(description="Todo ID"),
) -> dict[str, Any]:
    """Get todo details.
    
    Returns complete todo information.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        todo = graph.get_todo(todo_id)

        if not todo:
            return {"success": False, "error": f"Todo '{todo_id}' not found"}

        return {
            "success": True,
            "todo": todo,
        }
    except Exception as e:
        logger.error(f"todo_get error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def todo_list(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    project_name: str = Field(description="Project name"),
    status: str | None = Field(default=None, description="Filter by status"),
    priority: str | None = Field(default=None, description="Filter by priority"),
    assigned_to: str | None = Field(default=None, description="Filter by assignee"),
    file_path: str | None = Field(default=None, description="Filter by file path"),
    limit: int = Field(default=100, description="Maximum number of todos"),
) -> dict[str, Any]:
    """List todos with optional filters.
    
    Returns todos ordered by priority and creation date.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        project = graph.get_project(project_name)
        if not project:
            return {"success": False, "error": f"Project '{project_name}' not found"}

        todos = graph.list_todos(
            project_id=project["project_id"],
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            file_path=file_path,
            limit=limit,
        )

        return {
            "success": True,
            "todos": todos,
            "count": len(todos),
        }
    except Exception as e:
        logger.error(f"todo_list error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
@require_auth
def todo_delete(
    portal_uri: str = Field(description="mem:// URI of the portal"),
    todo_id: str = Field(description="Todo ID"),
) -> dict[str, Any]:
    """Delete a todo item.
    
    This permanently removes the todo.
    """
    try:
        uri = MemoryURI.parse(portal_uri)
        portal = registry.resolve(uri)

        from src.intel.graph import CodeGraph

        graph = CodeGraph(portal)
        graph.delete_todo(todo_id)

        return {
            "success": True,
            "todo_id": todo_id,
            "message": "Todo deleted",
        }
    except Exception as e:
        logger.error(f"todo_delete error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# Server Initialization
# ============================================================================

from src.core.middleware import init_auth, is_auth_enabled

