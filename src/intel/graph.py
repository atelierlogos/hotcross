"""Code intelligence graph storage using chDB tables."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from src.core.portal import MemoryPortal

from src.models.code_intel import (
    EdgeInfo,
    ExportInfo,
    FileInfo,
    ImportInfo,
    ReferenceInfo,
    ScopeInfo,
    SymbolInfo,
    TypeInfo,
)

logger = logging.getLogger(__name__)


# SQL for creating code intelligence tables
_CI_TABLES_SQL = {
    "_ci_projects": """
        CREATE TABLE IF NOT EXISTS _ci_projects (
            project_id UUID DEFAULT generateUUIDv4(),
            project_name String,
            root_path String,
            description Nullable(String),
            version Nullable(String),
            git_remote Nullable(String),
            git_branch Nullable(String),
            git_commit Nullable(String),
            created_at DateTime64(3) DEFAULT now64(3),
            updated_at DateTime64(3) DEFAULT now64(3),
            metadata JSON DEFAULT '{}'
        ) ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (project_name)
    """,
    "_ci_documents": """
        CREATE TABLE IF NOT EXISTS _ci_documents (
            document_id UUID DEFAULT generateUUIDv4(),
            project_id UUID,
            file_path String,
            doc_type String,
            title Nullable(String),
            content String,
            content_hash String,
            format String,
            word_count UInt32,
            indexed_at DateTime64(3) DEFAULT now64(3),
            metadata JSON DEFAULT '{}'
        ) ENGINE = ReplacingMergeTree(indexed_at)
        ORDER BY (project_id, file_path)
    """,
    "_ci_files": """
        CREATE TABLE IF NOT EXISTS _ci_files (
            file_id UUID DEFAULT generateUUIDv4(),
            project_id UUID,
            file_path String,
            language String,
            content_hash String,
            line_count UInt32,
            byte_size UInt64,
            indexed_at DateTime64(3) DEFAULT now64(3),
            parse_duration_ms Float32,
            error_message Nullable(String)
        ) ENGINE = ReplacingMergeTree(indexed_at)
        ORDER BY (project_id, file_path)
    """,
    "_ci_symbols": """
        CREATE TABLE IF NOT EXISTS _ci_symbols (
            symbol_id UUID DEFAULT generateUUIDv4(),
            project_id UUID,
            file_path String,
            name String,
            qualified_name String,
            kind String,
            visibility String,
            start_line UInt32,
            end_line UInt32,
            start_col UInt16,
            end_col UInt16,
            parent_symbol_id Nullable(UUID),
            scope_id Nullable(UUID),
            docstring Nullable(String),
            signature Nullable(String),
            is_async Bool DEFAULT false,
            is_static Bool DEFAULT false,
            decorators Array(String),
            metadata JSON DEFAULT '{}'
        ) ENGINE = MergeTree()
        ORDER BY (project_id, file_path, start_line, name)
    """,
    "_ci_types": """
        CREATE TABLE IF NOT EXISTS _ci_types (
            type_id UUID DEFAULT generateUUIDv4(),
            project_id UUID,
            file_path String,
            symbol_id Nullable(UUID),
            name String,
            kind String,
            type_expression String,
            start_line UInt32,
            end_line UInt32,
            is_generic Bool DEFAULT false,
            generic_params Array(String),
            metadata JSON DEFAULT '{}'
        ) ENGINE = MergeTree()
        ORDER BY (project_id, file_path, start_line)
    """,
    "_ci_imports": """
        CREATE TABLE IF NOT EXISTS _ci_imports (
            import_id UUID DEFAULT generateUUIDv4(),
            project_id UUID,
            file_path String,
            module_path String,
            imported_names Array(String),
            alias Nullable(String),
            is_relative Bool DEFAULT false,
            relative_level UInt8 DEFAULT 0,
            import_kind String,
            start_line UInt32,
            is_type_only Bool DEFAULT false
        ) ENGINE = MergeTree()
        ORDER BY (project_id, file_path, start_line)
    """,
    "_ci_exports": """
        CREATE TABLE IF NOT EXISTS _ci_exports (
            export_id UUID DEFAULT generateUUIDv4(),
            project_id UUID,
            file_path String,
            symbol_id Nullable(UUID),
            exported_name String,
            original_name Nullable(String),
            export_kind String,
            start_line UInt32
        ) ENGINE = MergeTree()
        ORDER BY (project_id, file_path, exported_name)
    """,
    "_ci_scopes": """
        CREATE TABLE IF NOT EXISTS _ci_scopes (
            scope_id UUID DEFAULT generateUUIDv4(),
            project_id UUID,
            file_path String,
            parent_scope_id Nullable(UUID),
            kind String,
            name Nullable(String),
            start_line UInt32,
            end_line UInt32,
            depth UInt8
        ) ENGINE = MergeTree()
        ORDER BY (project_id, file_path, start_line)
    """,
    "_ci_references": """
        CREATE TABLE IF NOT EXISTS _ci_references (
            reference_id UUID DEFAULT generateUUIDv4(),
            project_id UUID,
            file_path String,
            symbol_id Nullable(UUID),
            name String,
            kind String,
            start_line UInt32,
            start_col UInt16,
            scope_id Nullable(UUID),
            is_definition Bool DEFAULT false
        ) ENGINE = MergeTree()
        ORDER BY (project_id, file_path, start_line, start_col)
    """,
    "_ci_edges": """
        CREATE TABLE IF NOT EXISTS _ci_edges (
            edge_id UUID DEFAULT generateUUIDv4(),
            source_file String,
            source_line UInt32,
            source_col UInt16,
            source_symbol_id Nullable(UUID),
            target_file String,
            target_line UInt32,
            target_col UInt16,
            target_symbol_id Nullable(UUID),
            edge_type String,
            resolved_by String,
            lsp_server Nullable(String),
            resolved_at DateTime64(3) DEFAULT now64(3)
        ) ENGINE = ReplacingMergeTree(resolved_at)
        ORDER BY (edge_type, source_file, source_line, source_col)
    """,
    "_ci_sessions": """
        CREATE TABLE IF NOT EXISTS _ci_sessions (
            session_id UUID DEFAULT generateUUIDv4(),
            project_id UUID,
            title String,
            description Nullable(String),
            model Nullable(String),
            provider Nullable(String),
            message_count UInt32 DEFAULT 0,
            token_count UInt64 DEFAULT 0,
            created_at DateTime64(3) DEFAULT now64(3),
            updated_at DateTime64(3) DEFAULT now64(3),
            archived_at Nullable(DateTime64(3)),
            metadata JSON DEFAULT '{}'
        ) ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (project_id, session_id)
    """,
    "_ci_session_messages": """
        CREATE TABLE IF NOT EXISTS _ci_session_messages (
            message_id UUID DEFAULT generateUUIDv4(),
            session_id UUID,
            project_id UUID,
            role String,
            content String,
            token_count UInt32 DEFAULT 0,
            created_at DateTime64(3) DEFAULT now64(3),
            sequence_number UInt32,
            metadata JSON DEFAULT '{}'
        ) ENGINE = MergeTree()
        ORDER BY (session_id, sequence_number)
    """,
    "_ci_todos": """
        CREATE TABLE IF NOT EXISTS _ci_todos (
            todo_id UUID DEFAULT generateUUIDv4(),
            project_id UUID,
            title String,
            description Nullable(String),
            status String DEFAULT 'open',
            priority String DEFAULT 'medium',
            file_path Nullable(String),
            line_number Nullable(UInt32),
            assigned_to Nullable(String),
            created_at DateTime64(3) DEFAULT now64(3),
            updated_at DateTime64(3) DEFAULT now64(3),
            completed_at Nullable(DateTime64(3)),
            due_date Nullable(DateTime64(3)),
            tags Array(String),
            metadata JSON DEFAULT '{}'
        ) ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (project_id, status, priority, created_at)
    """,
}


class CodeGraph:
    """Manages code intelligence data in chDB tables.

    Provides CRUD operations for symbols, types, imports, exports,
    scopes, references, and resolved edges.
    """

    def __init__(self, portal: MemoryPortal, project_id: str | None = None):
        """Initialize the code graph.

        Args:
            portal: MemoryPortal instance for database access
            project_id: Optional project ID to use for all operations
        """
        self._portal = portal
        self._initialized = False
        self._current_project_id = project_id

    @property
    def portal(self) -> MemoryPortal:
        """Get the underlying portal."""
        return self._portal

    def ensure_tables(self) -> None:
        """Create code intelligence tables if they don't exist."""
        if self._initialized:
            return

        for table_name, create_sql in _CI_TABLES_SQL.items():
            if not self._portal._db.table_exists(table_name):
                self._portal._db.execute_command(create_sql)
                logger.debug(f"Created table {table_name}")

        self._initialized = True

    # --- Project operations ---

    def create_project(
        self,
        project_name: str,
        root_path: str,
        description: str | None = None,
        version: str | None = None,
        git_remote: str | None = None,
        git_branch: str | None = None,
        git_commit: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new project.

        Args:
            project_name: Project name
            root_path: Root directory path
            description: Optional project description
            version: Optional version string
            git_remote: Optional git remote URL
            git_branch: Optional git branch name
            git_commit: Optional git commit hash
            metadata: Optional additional metadata

        Returns:
            Project ID (UUID string)
        """
        self.ensure_tables()
        project_id = str(uuid4())

        metadata_json = json.dumps(metadata or {}).replace('"', '\\"')

        self._portal._db.execute_command(f"""
            INSERT INTO _ci_projects (
                project_id, project_name, root_path, description, version,
                git_remote, git_branch, git_commit, metadata
            ) VALUES (
                '{project_id}',
                '{_escape(project_name)}',
                '{_escape(root_path)}',
                {_nullable_str(description)},
                {_nullable_str(version)},
                {_nullable_str(git_remote)},
                {_nullable_str(git_branch)},
                {_nullable_str(git_commit)},
                '{metadata_json}'
            )
        """)

        logger.info(f"Created project {project_name} with ID {project_id}")
        return project_id

    def get_project(self, project_name: str) -> dict[str, Any] | None:
        """Get project by name.

        Args:
            project_name: Project name

        Returns:
            Project dictionary or None if not found
        """
        self.ensure_tables()
        return self._portal._db.query_single(
            f"SELECT * FROM _ci_projects WHERE project_name = '{_escape(project_name)}' "
            "ORDER BY updated_at DESC LIMIT 1"
        )

    def get_project_by_id(self, project_id: str) -> dict[str, Any] | None:
        """Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project dictionary or None if not found
        """
        self.ensure_tables()
        return self._portal._db.query_single(
            f"SELECT * FROM _ci_projects WHERE project_id = '{project_id}' LIMIT 1"
        )

    def list_projects(self) -> list[dict[str, Any]]:
        """List all projects.

        Returns:
            List of project dictionaries
        """
        self.ensure_tables()
        return self._portal._db.query(
            "SELECT * FROM _ci_projects ORDER BY project_name"
        )

    def update_project(
        self,
        project_id: str,
        description: str | None = None,
        version: str | None = None,
        git_branch: str | None = None,
        git_commit: str | None = None,
    ) -> None:
        """Update project metadata.

        Args:
            project_id: Project ID
            description: Optional new description
            version: Optional new version
            git_branch: Optional new git branch
            git_commit: Optional new git commit
        """
        self.ensure_tables()

        # Get current project
        project = self.get_project_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Update fields
        if description is not None:
            project["description"] = description
        if version is not None:
            project["version"] = version
        if git_branch is not None:
            project["git_branch"] = git_branch
        if git_commit is not None:
            project["git_commit"] = git_commit

        # Insert new version (ReplacingMergeTree will replace old one)
        metadata = project.get("metadata", {})
        if isinstance(metadata, str):
            metadata_json = metadata.replace('"', '\\"')
        else:
            metadata_json = json.dumps(metadata).replace('"', '\\"')
        
        self._portal._db.execute_command(f"""
            INSERT INTO _ci_projects (
                project_id, project_name, root_path, description, version,
                git_remote, git_branch, git_commit, metadata
            ) VALUES (
                '{project_id}',
                '{_escape(project["project_name"])}',
                '{_escape(project["root_path"])}',
                {_nullable_str(project.get("description"))},
                {_nullable_str(project.get("version"))},
                {_nullable_str(project.get("git_remote"))},
                {_nullable_str(project.get("git_branch"))},
                {_nullable_str(project.get("git_commit"))},
                '{metadata_json}'
            )
        """)

    def delete_project(self, project_id: str) -> None:
        """Delete a project and all its data.

        Args:
            project_id: Project ID to delete
        """
        self.ensure_tables()

        # Delete from all tables
        for table in [
            "_ci_files", "_ci_symbols", "_ci_types", "_ci_imports",
            "_ci_exports", "_ci_scopes", "_ci_references", "_ci_projects"
        ]:
            self._portal._db.execute_command(
                f"ALTER TABLE {table} DELETE WHERE project_id = '{project_id}'"
            )

        logger.info(f"Deleted project {project_id} and all its data")

    def set_current_project(self, project_id: str) -> None:
        """Set the current project ID for subsequent operations.

        Args:
            project_id: Project ID to use
        """
        self._current_project_id = project_id

    def get_current_project_id(self) -> str | None:
        """Get the current project ID.

        Returns:
            Current project ID or None
        """
        return self._current_project_id

    # --- Convenience methods for indexer (singular operations) ---

    def store_file_info(
        self,
        file_path: str,
        language: str,
        content_hash: str,
        line_count: int,
        byte_size: int,
        parse_duration_ms: float,
        error_message: str | None = None,
        project_id: str | None = None,
    ) -> str:
        """Store file information.

        Args:
            file_path: File path
            language: Programming language
            content_hash: SHA-256 hash of file contents
            line_count: Number of lines
            byte_size: File size in bytes
            parse_duration_ms: Parse duration in milliseconds
            error_message: Optional error message
            project_id: Optional project ID (uses current if not provided)

        Returns:
            File ID as string
        """
        self.ensure_tables()
        file_id = str(uuid4())
        proj_id = project_id or self._current_project_id
        
        if not proj_id:
            raise ValueError("project_id must be provided or set via set_current_project()")

        self._portal._db.execute_command(f"""
            INSERT INTO _ci_files (
                file_id, project_id, file_path, language, content_hash, line_count,
                byte_size, parse_duration_ms, error_message
            ) VALUES (
                '{file_id}',
                '{proj_id}',
                '{_escape(file_path)}',
                '{_escape(language)}',
                '{_escape(content_hash)}',
                {line_count},
                {byte_size},
                {parse_duration_ms},
                {_nullable_str(error_message)}
            )
        """)
        return file_id

    def store_symbol(self, file_path: str, symbol: SymbolInfo, project_id: str | None = None) -> str:
        """Store a single symbol.

        Args:
            file_path: File path
            symbol: Symbol information
            project_id: Optional project ID (uses current if not provided)

        Returns:
            Symbol ID as string
        """
        self.ensure_tables()
        symbol_id = str(uuid4())
        proj_id = project_id or self._current_project_id
        
        if not proj_id:
            raise ValueError("project_id must be provided or set via set_current_project()")

        # Format decorators as ClickHouse array
        if symbol.decorators:
            decorators_array = "[" + ", ".join(f"'{_escape(d)}'" for d in symbol.decorators) + "]"
        else:
            decorators_array = "[]"

        # Format metadata as JSON string (escaped)
        metadata_json = json.dumps(symbol.metadata).replace('"', '\\"')

        self._portal._db.execute_command(f"""
            INSERT INTO _ci_symbols (
                symbol_id, project_id, file_path, name, qualified_name, kind, visibility,
                start_line, end_line, start_col, end_col, parent_symbol_id, scope_id,
                docstring, signature, is_async, is_static, decorators, metadata
            ) VALUES (
                '{symbol_id}',
                '{proj_id}',
                '{_escape(file_path)}',
                '{_escape(symbol.name)}',
                '{_escape(symbol.qualified_name)}',
                '{_escape(symbol.kind)}',
                '{_escape(symbol.visibility)}',
                {symbol.start_line},
                {symbol.end_line},
                {symbol.start_col},
                {symbol.end_col},
                {_nullable_str(symbol.parent_symbol_id)},
                {_nullable_str(symbol.scope_id)},
                {_nullable_str(symbol.docstring)},
                {_nullable_str(symbol.signature)},
                {1 if symbol.is_async else 0},
                {1 if symbol.is_static else 0},
                {decorators_array},
                '{metadata_json}'
            )
        """)
        return symbol_id

    def store_type(self, file_path: str, type_info: TypeInfo, project_id: str | None = None) -> str:
        """Store a single type.

        Args:
            file_path: File path
            type_info: Type information
            project_id: Optional project ID (uses current if not provided)

        Returns:
            Type ID as string
        """
        self.ensure_tables()
        type_id = str(uuid4())
        proj_id = project_id or self._current_project_id
        
        if not proj_id:
            raise ValueError("project_id must be provided or set via set_current_project()")

        # Format generic_params as ClickHouse array
        if type_info.generic_params:
            params_array = "[" + ", ".join(f"'{_escape(p)}'" for p in type_info.generic_params) + "]"
        else:
            params_array = "[]"

        # Format metadata as JSON string (escaped)
        metadata_json = json.dumps(type_info.metadata).replace('"', '\\"')

        self._portal._db.execute_command(f"""
            INSERT INTO _ci_types (
                type_id, project_id, file_path, symbol_id, name, kind, type_expression,
                start_line, end_line, is_generic, generic_params, metadata
            ) VALUES (
                '{type_id}',
                '{proj_id}',
                '{_escape(file_path)}',
                {_nullable_str(type_info.symbol_id)},
                '{_escape(type_info.name)}',
                '{_escape(type_info.kind)}',
                '{_escape(type_info.type_expression)}',
                {type_info.start_line},
                {type_info.end_line},
                {1 if type_info.is_generic else 0},
                {params_array},
                '{metadata_json}'
            )
        """)
        return type_id

    def store_import(self, file_path: str, import_info: ImportInfo, project_id: str | None = None) -> str:
        """Store a single import.

        Args:
            file_path: File path
            import_info: Import information
            project_id: Optional project ID (uses current if not provided)

        Returns:
            Import ID as string
        """
        self.ensure_tables()
        import_id = str(uuid4())
        proj_id = project_id or self._current_project_id
        
        if not proj_id:
            raise ValueError("project_id must be provided or set via set_current_project()")

        # Format imported_names as ClickHouse array
        if import_info.imported_names:
            names_array = "[" + ", ".join(f"'{_escape(n)}'" for n in import_info.imported_names) + "]"
        else:
            names_array = "[]"

        self._portal._db.execute_command(f"""
            INSERT INTO _ci_imports (
                import_id, project_id, file_path, module_path, imported_names, alias,
                is_relative, relative_level, import_kind, start_line, is_type_only
            ) VALUES (
                '{import_id}',
                '{proj_id}',
                '{_escape(file_path)}',
                '{_escape(import_info.module_path)}',
                {names_array},
                {_nullable_str(import_info.alias)},
                {1 if import_info.is_relative else 0},
                {import_info.relative_level},
                '{_escape(import_info.import_kind)}',
                {import_info.start_line},
                {1 if import_info.is_type_only else 0}
            )
        """)
        return import_id

    def store_export(self, file_path: str, export_info: ExportInfo, project_id: str | None = None) -> str:
        """Store a single export.

        Args:
            file_path: File path
            export_info: Export information
            project_id: Optional project ID (uses current if not provided)

        Returns:
            Export ID as string
        """
        self.ensure_tables()
        export_id = str(uuid4())
        proj_id = project_id or self._current_project_id
        
        if not proj_id:
            raise ValueError("project_id must be provided or set via set_current_project()")

        self._portal._db.execute_command(f"""
            INSERT INTO _ci_exports (
                export_id, project_id, file_path, symbol_id, exported_name, original_name,
                export_kind, start_line
            ) VALUES (
                '{export_id}',
                '{proj_id}',
                '{_escape(file_path)}',
                {_nullable_str(export_info.symbol_id)},
                '{_escape(export_info.exported_name)}',
                {_nullable_str(export_info.original_name)},
                '{_escape(export_info.export_kind)}',
                {export_info.start_line}
            )
        """)
        return export_id

    def store_scope(self, file_path: str, scope: ScopeInfo, project_id: str | None = None) -> str:
        """Store a single scope.

        Args:
            file_path: File path
            scope: Scope information
            project_id: Optional project ID (uses current if not provided)

        Returns:
            Scope ID as string
        """
        self.ensure_tables()
        scope_id = str(uuid4())
        proj_id = project_id or self._current_project_id
        
        if not proj_id:
            raise ValueError("project_id must be provided or set via set_current_project()")

        self._portal._db.execute_command(f"""
            INSERT INTO _ci_scopes (
                scope_id, project_id, file_path, parent_scope_id, kind, name,
                start_line, end_line, depth
            ) VALUES (
                '{scope_id}',
                '{proj_id}',
                '{_escape(file_path)}',
                {_nullable_str(scope.parent_scope_id)},
                '{_escape(scope.kind)}',
                {_nullable_str(scope.name)},
                {scope.start_line},
                {scope.end_line},
                {scope.depth}
            )
        """)
        return scope_id

    def store_reference(self, file_path: str, reference: ReferenceInfo, project_id: str | None = None) -> str:
        """Store a single reference.

        Args:
            file_path: File path
            reference: Reference information
            project_id: Optional project ID (uses current if not provided)

        Returns:
            Reference ID as string
        """
        self.ensure_tables()
        reference_id = str(uuid4())
        proj_id = project_id or self._current_project_id
        
        if not proj_id:
            raise ValueError("project_id must be provided or set via set_current_project()")

        self._portal._db.execute_command(f"""
            INSERT INTO _ci_references (
                reference_id, project_id, file_path, symbol_id, name, kind,
                start_line, start_col, scope_id, is_definition
            ) VALUES (
                '{reference_id}',
                '{proj_id}',
                '{_escape(file_path)}',
                {_nullable_str(reference.symbol_id)},
                '{_escape(reference.name)}',
                '{_escape(reference.kind)}',
                {reference.start_line},
                {reference.start_col},
                {_nullable_str(reference.scope_id)},
                {1 if reference.is_definition else 0}
            )
        """)
        return reference_id

    # --- File operations ---

    def get_file_hash(self, file_path: str) -> str | None:
        """Get the stored content hash for a file.

        Args:
            file_path: File path

        Returns:
            Content hash or None if not indexed
        """
        self.ensure_tables()
        row = self._portal._db.query_single(
            f"SELECT content_hash FROM _ci_files WHERE file_path = '{_escape(file_path)}' "
            "ORDER BY indexed_at DESC LIMIT 1"
        )
        return row["content_hash"] if row else None

    def store_file(self, result: FileIndexResult) -> UUID:
        """Store file index result.

        Args:
            result: File index result

        Returns:
            File UUID
        """
        self.ensure_tables()
        file_id = uuid4()

        self._portal._db.execute_command(f"""
            INSERT INTO _ci_files (
                file_id, file_path, language, content_hash, line_count,
                byte_size, parse_duration_ms, error_message
            ) VALUES (
                '{file_id}',
                '{_escape(result.file_path)}',
                '{_escape(result.language)}',
                '{_escape(result.content_hash)}',
                {result.line_count},
                {result.byte_size},
                {result.parse_duration_ms},
                {_nullable_str(result.error_message)}
            )
        """)
        return file_id

    def delete_file_data(self, file_path: str) -> None:
        """Delete all data for a file.

        Args:
            file_path: File path to delete
        """
        self.ensure_tables()
        escaped_path = _escape(file_path)

        # Delete from all tables
        for table in [
            "_ci_files", "_ci_symbols", "_ci_types", "_ci_imports",
            "_ci_exports", "_ci_scopes", "_ci_references"
        ]:
            self._portal._db.execute_command(
                f"ALTER TABLE {table} DELETE WHERE file_path = '{escaped_path}'"
            )

        # Also delete edges with this file as source
        self._portal._db.execute_command(
            f"ALTER TABLE _ci_edges DELETE WHERE source_file = '{escaped_path}'"
        )

    # --- Symbol operations ---

    def store_symbols(
        self,
        file_path: str,
        symbols: list[SymbolInfo],
        scope_ids: dict[int, UUID] | None = None,
    ) -> dict[str, UUID]:
        """Store symbols for a file.

        Args:
            file_path: Source file path
            symbols: List of symbol info objects
            scope_ids: Mapping of scope index to scope UUID

        Returns:
            Mapping of qualified_name to symbol UUID
        """
        self.ensure_tables()
        if not symbols:
            return {}

        symbol_ids: dict[str, UUID] = {}
        rows = []

        for symbol in symbols:
            symbol_id = uuid4()
            symbol_ids[symbol.qualified_name] = symbol_id

            # Look up parent symbol ID
            parent_id = None
            if symbol.parent_qualified_name:
                parent_id = symbol_ids.get(symbol.parent_qualified_name)

            rows.append({
                "symbol_id": str(symbol_id),
                "file_path": file_path,
                "name": symbol.name,
                "qualified_name": symbol.qualified_name,
                "kind": symbol.kind.value,
                "visibility": symbol.visibility.value,
                "start_line": symbol.start_line,
                "end_line": symbol.end_line,
                "start_col": symbol.start_col,
                "end_col": symbol.end_col,
                "parent_symbol_id": str(parent_id) if parent_id else None,
                "scope_id": None,  # TODO: link to scope
                "docstring": symbol.docstring,
                "signature": symbol.signature,
                "is_async": symbol.is_async,
                "is_static": symbol.is_static,
                "decorators": symbol.decorators,
                "metadata": symbol.metadata,
            })

        self._insert_rows("_ci_symbols", rows)
        return symbol_ids

    def find_symbols(
        self,
        project_name: str,
        name: str | None = None,
        kind: str | None = None,
        file_pattern: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Search for symbols within a project.

        Args:
            project_name: Project name to search within
            name: Symbol name pattern (supports % wildcards)
            kind: Symbol kind filter
            file_pattern: File path pattern (supports % wildcards)
            limit: Maximum results

        Returns:
            List of matching symbols as dictionaries
        """
        self.ensure_tables()

        # Look up project_id from project_name
        project = self.get_project(project_name)
        if not project:
            return []
        project_id = project["project_id"]

        conditions = [f"project_id = '{project_id}'"]
        if name:
            if "%" in name:
                conditions.append(f"name LIKE '{_escape(name)}'")
            else:
                conditions.append(f"name = '{_escape(name)}'")
        if kind:
            conditions.append(f"kind = '{_escape(kind)}'")
        if file_pattern:
            if "%" in file_pattern:
                conditions.append(f"file_path LIKE '{_escape(file_pattern)}'")
            else:
                conditions.append(f"file_path = '{_escape(file_pattern)}'")

        where = f"WHERE {' AND '.join(conditions)}"

        rows = self._portal._db.query(f"""
            SELECT symbol_id, file_path, name, qualified_name, kind,
                   start_line, end_line, signature, docstring
            FROM _ci_symbols
            {where}
            ORDER BY file_path, start_line
            LIMIT {limit}
        """)

        return rows

    def get_file_symbols(self, project_name: str, file_path: str) -> list[dict[str, Any]]:
        """Get all symbols in a file within a project.

        Args:
            project_name: Project name
            file_path: File path

        Returns:
            List of symbols in the file as dictionaries
        """
        return self.find_symbols(project_name=project_name, file_pattern=file_path, limit=10000)

    # --- Type operations ---

    def store_types(
        self,
        file_path: str,
        types: list[TypeInfo],
        symbol_ids: dict[str, UUID] | None = None,
    ) -> list[UUID]:
        """Store type annotations for a file.

        Args:
            file_path: Source file path
            types: List of type info objects
            symbol_ids: Mapping of qualified_name to symbol UUID

        Returns:
            List of type UUIDs
        """
        self.ensure_tables()
        if not types:
            return []

        type_ids = []
        rows = []

        for type_info in types:
            type_id = uuid4()
            type_ids.append(type_id)

            # Look up symbol ID
            symbol_id = None
            if type_info.symbol_qualified_name and symbol_ids:
                symbol_id = symbol_ids.get(type_info.symbol_qualified_name)

            rows.append({
                "type_id": str(type_id),
                "file_path": file_path,
                "symbol_id": str(symbol_id) if symbol_id else None,
                "name": type_info.name,
                "kind": type_info.kind.value,
                "type_expression": type_info.type_expression,
                "start_line": type_info.start_line,
                "end_line": type_info.end_line,
                "is_generic": type_info.is_generic,
                "generic_params": type_info.generic_params,
                "metadata": type_info.metadata,
            })

        self._insert_rows("_ci_types", rows)
        return type_ids

    # --- Import operations ---

    def store_imports(self, file_path: str, imports: list[ImportInfo]) -> list[UUID]:
        """Store imports for a file.

        Args:
            file_path: Source file path
            imports: List of import info objects

        Returns:
            List of import UUIDs
        """
        self.ensure_tables()
        if not imports:
            return []

        import_ids = []
        rows = []

        for imp in imports:
            import_id = uuid4()
            import_ids.append(import_id)

            rows.append({
                "import_id": str(import_id),
                "file_path": file_path,
                "module_path": imp.module_path,
                "imported_names": imp.imported_names,
                "alias": imp.alias,
                "is_relative": imp.is_relative,
                "relative_level": imp.relative_level,
                "import_kind": imp.import_kind.value,
                "start_line": imp.start_line,
                "is_type_only": imp.is_type_only,
            })

        self._insert_rows("_ci_imports", rows)
        return import_ids

    def get_file_imports(self, project_name: str, file_path: str) -> list[dict[str, Any]]:
        """Get imports for a file within a project.

        Args:
            project_name: Project name
            file_path: File path

        Returns:
            List of import records
        """
        self.ensure_tables()

        # Look up project_id from project_name
        project = self.get_project(project_name)
        if not project:
            return []
        project_id = project["project_id"]

        return self._portal._db.query(
            f"SELECT * FROM _ci_imports WHERE project_id = '{project_id}' "
            f"AND file_path = '{_escape(file_path)}' ORDER BY start_line"
        )

    # --- Export operations ---

    def store_exports(
        self,
        file_path: str,
        exports: list[ExportInfo],
        symbol_ids: dict[str, UUID] | None = None,
    ) -> list[UUID]:
        """Store exports for a file.

        Args:
            file_path: Source file path
            exports: List of export info objects
            symbol_ids: Mapping of qualified_name to symbol UUID

        Returns:
            List of export UUIDs
        """
        self.ensure_tables()
        if not exports:
            return []

        export_ids = []
        rows = []

        for exp in exports:
            export_id = uuid4()
            export_ids.append(export_id)

            # Look up symbol ID
            symbol_id = None
            if exp.symbol_qualified_name and symbol_ids:
                symbol_id = symbol_ids.get(exp.symbol_qualified_name)

            rows.append({
                "export_id": str(export_id),
                "file_path": file_path,
                "symbol_id": str(symbol_id) if symbol_id else None,
                "exported_name": exp.exported_name,
                "original_name": exp.original_name,
                "export_kind": exp.export_kind.value,
                "start_line": exp.start_line,
            })

        self._insert_rows("_ci_exports", rows)
        return export_ids

    # --- Scope operations ---

    def store_scopes(self, file_path: str, scopes: list[ScopeInfo]) -> dict[int, UUID]:
        """Store scopes for a file.

        Args:
            file_path: Source file path
            scopes: List of scope info objects (in order)

        Returns:
            Mapping of scope index to scope UUID
        """
        self.ensure_tables()
        if not scopes:
            return {}

        scope_ids: dict[int, UUID] = {}
        rows = []

        for i, scope in enumerate(scopes):
            scope_id = uuid4()
            scope_ids[i] = scope_id

            # Look up parent scope ID
            parent_id = None
            if scope.parent_index is not None:
                parent_id = scope_ids.get(scope.parent_index)

            rows.append({
                "scope_id": str(scope_id),
                "file_path": file_path,
                "parent_scope_id": str(parent_id) if parent_id else None,
                "kind": scope.kind.value,
                "name": scope.name,
                "start_line": scope.start_line,
                "end_line": scope.end_line,
                "depth": scope.depth,
            })

        self._insert_rows("_ci_scopes", rows)
        return scope_ids

    # --- Reference operations ---

    def store_references(
        self,
        file_path: str,
        references: list[ReferenceInfo],
        scope_ids: dict[int, UUID] | None = None,
    ) -> list[UUID]:
        """Store references for a file.

        Args:
            file_path: Source file path
            references: List of reference info objects
            scope_ids: Mapping of scope index to scope UUID

        Returns:
            List of reference UUIDs
        """
        self.ensure_tables()
        if not references:
            return []

        ref_ids = []
        rows = []

        for ref in references:
            ref_id = uuid4()
            ref_ids.append(ref_id)

            # Look up scope ID
            scope_id = None
            if ref.scope_index is not None and scope_ids:
                scope_id = scope_ids.get(ref.scope_index)

            rows.append({
                "reference_id": str(ref_id),
                "file_path": file_path,
                "symbol_id": None,  # Will be resolved later
                "name": ref.name,
                "kind": ref.kind.value,
                "start_line": ref.start_line,
                "start_col": ref.start_col,
                "scope_id": str(scope_id) if scope_id else None,
                "is_definition": ref.is_definition,
            })

        self._insert_rows("_ci_references", rows)
        return ref_ids

    # --- Edge operations (LSP resolved) ---

    def store_edges(self, edges: list[EdgeInfo]) -> list[UUID]:
        """Store resolved edges.

        Args:
            edges: List of edge info objects

        Returns:
            List of edge UUIDs
        """
        self.ensure_tables()
        if not edges:
            return []

        edge_ids = []
        rows = []

        for edge in edges:
            edge_id = uuid4()
            edge_ids.append(edge_id)

            rows.append({
                "edge_id": str(edge_id),
                "source_file": edge.source_file,
                "source_line": edge.source_line,
                "source_col": edge.source_col,
                "source_symbol_id": None,  # TODO: resolve
                "target_file": edge.target_file,
                "target_line": edge.target_line,
                "target_col": edge.target_col,
                "target_symbol_id": None,  # TODO: resolve
                "edge_type": edge.edge_type.value,
                "resolved_by": edge.resolved_by.value,
                "lsp_server": edge.lsp_server,
            })

        self._insert_rows("_ci_edges", rows)
        return edge_ids

    # --- Query methods ---

    def get_dependencies(self, project_name: str, file_path: str | None = None) -> list[dict[str, Any]]:
        """Get dependency information for a project.

        Args:
            project_name: Project name
            file_path: Optional file path to filter dependencies

        Returns:
            List of dependency records
        """
        self.ensure_tables()

        # Look up project_id from project_name
        project = self.get_project(project_name)
        if not project:
            return []
        project_id = project["project_id"]

        conditions = [f"project_id = '{project_id}'"]
        if file_path:
            conditions.append(f"file_path = '{_escape(file_path)}'")

        where = f"WHERE {' AND '.join(conditions)}"

        rows = self._portal._db.query(f"""
            SELECT file_path, module_path, imported_names, import_kind, is_relative
            FROM _ci_imports
            {where}
            ORDER BY file_path, start_line
        """)

        return rows

    def find_references(
        self, project_name: str, symbol_name: str, file_path: str | None = None
    ) -> list[dict[str, Any]]:
        """Find references to a symbol within a project.

        Args:
            project_name: Project name
            symbol_name: Symbol name to search for
            file_path: Optional file path to limit search

        Returns:
            List of reference records
        """
        self.ensure_tables()

        # Look up project_id from project_name
        project = self.get_project(project_name)
        if not project:
            return []
        project_id = project["project_id"]

        conditions = [
            f"project_id = '{project_id}'",
            f"name = '{_escape(symbol_name)}'"
        ]
        if file_path:
            conditions.append(f"file_path = '{_escape(file_path)}'")

        where = f"WHERE {' AND '.join(conditions)}"

        rows = self._portal._db.query(f"""
            SELECT file_path, name, kind, start_line, start_col
            FROM _ci_references
            {where}
            ORDER BY file_path, start_line, start_col
        """)

        return rows
    
    def get_file_exports(self, project_name: str, file_path: str) -> list[dict[str, Any]]:
        """Get exports for a file within a project.

        Args:
            project_name: Project name
            file_path: File path

        Returns:
            List of export records
        """
        self.ensure_tables()

        # Look up project_id from project_name
        project = self.get_project(project_name)
        if not project:
            return []
        project_id = project["project_id"]

        return self._portal._db.query(
            f"SELECT * FROM _ci_exports WHERE project_id = '{project_id}' "
            f"AND file_path = '{_escape(file_path)}' ORDER BY start_line"
        )

    # --- Statistics ---

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics.

        Returns:
            Index statistics as dictionary
        """
        self.ensure_tables()

        # Get counts from each table
        file_count = self._portal._db.query_value("SELECT count() FROM _ci_files") or 0
        symbol_count = self._portal._db.query_value("SELECT count() FROM _ci_symbols") or 0
        type_count = self._portal._db.query_value("SELECT count() FROM _ci_types") or 0
        import_count = self._portal._db.query_value("SELECT count() FROM _ci_imports") or 0
        export_count = self._portal._db.query_value("SELECT count() FROM _ci_exports") or 0
        scope_count = self._portal._db.query_value("SELECT count() FROM _ci_scopes") or 0
        ref_count = self._portal._db.query_value("SELECT count() FROM _ci_references") or 0

        # Get files by language
        lang_rows = self._portal._db.query(
            "SELECT language, count() as cnt FROM _ci_files GROUP BY language"
        )
        languages = {row["language"]: int(row["cnt"]) for row in lang_rows}

        # Get last indexed timestamp
        last_indexed = self._portal._db.query_value(
            "SELECT max(indexed_at) FROM _ci_files"
        )

        return {
            "total_files": int(file_count),
            "total_symbols": int(symbol_count),
            "total_types": int(type_count),
            "total_imports": int(import_count),
            "total_exports": int(export_count),
            "total_scopes": int(scope_count),
            "total_references": int(ref_count),
            "languages": languages,
            "last_indexed": last_indexed,
        }

    # --- Internal helpers ---

    def _insert_rows(self, table: str, rows: list[dict[str, Any]]) -> None:
        """Insert rows into a table with proper formatting.

        Args:
            table: Table name
            rows: List of row dictionaries
        """
        if not rows:
            return

        columns = list(rows[0].keys())
        col_list = ", ".join(columns)
        values_list = []

        for row in rows:
            values = []
            for col in columns:
                val = row.get(col)
                values.append(_format_value(val))
            values_list.append(f"({', '.join(values)})")

        sql = f"INSERT INTO {table} ({col_list}) VALUES {', '.join(values_list)}"
        self._portal._db.execute_command(sql)


def _escape(value: str) -> str:
    """Escape a string for SQL."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _nullable_str(value: str | None) -> str:
    """Format a nullable string for SQL."""
    if value is None:
        return "NULL"
    return f"'{_escape(value)}'"


def _format_value(value: Any) -> str:
    """Format a Python value for SQL insertion."""
    if value is None:
        return "NULL"
    elif isinstance(value, bool):
        return "1" if value else "0"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return f"'{_escape(value)}'"
    elif isinstance(value, (list, tuple)):
        # Format as ClickHouse array
        if not value:
            return "[]"
        items = [_format_value(v) for v in value]
        return f"[{', '.join(items)}]"
    elif isinstance(value, dict):
        # Format as JSON string
        json_str = json.dumps(value)
        return f"'{_escape(json_str)}'"
    else:
        return f"'{_escape(str(value))}'"
