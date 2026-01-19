"""Pydantic models for code intelligence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Information about an indexed file."""

    file_id: str = Field(..., description="Unique file identifier")
    file_path: str = Field(..., description="File path")
    language: str = Field(..., description="Programming language")
    content_hash: str = Field(..., description="SHA-256 hash of file contents")
    line_count: int = Field(..., description="Number of lines")
    byte_size: int = Field(..., description="File size in bytes")
    indexed_at: datetime = Field(..., description="Indexing timestamp")
    parse_duration_ms: float = Field(..., description="Parse duration in milliseconds")
    error_message: str | None = Field(default=None, description="Error message if parsing failed")


class SymbolInfo(BaseModel):
    """Information about a code symbol."""

    symbol_id: str | None = Field(default=None, description="Unique symbol identifier")
    file_path: str | None = Field(default=None, description="File path")
    name: str = Field(..., description="Symbol name")
    qualified_name: str = Field(..., description="Fully qualified name")
    kind: str = Field(..., description="Symbol kind (function, class, method, variable, constant)")
    visibility: str = Field(default="public", description="Visibility (public, private, protected)")
    start_line: int = Field(..., description="Start line number")
    end_line: int = Field(..., description="End line number")
    start_col: int = Field(default=0, description="Start column")
    end_col: int = Field(default=0, description="End column")
    parent_symbol_id: str | None = Field(default=None, description="Parent symbol ID")
    scope_id: str | None = Field(default=None, description="Scope ID")
    docstring: str | None = Field(default=None, description="Documentation string")
    signature: str | None = Field(default=None, description="Function/method signature")
    is_async: bool = Field(default=False, description="Is async function")
    is_static: bool = Field(default=False, description="Is static method")
    decorators: list[str] = Field(default_factory=list, description="Decorator names")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TypeInfo(BaseModel):
    """Information about a type annotation or alias."""

    type_id: str | None = Field(default=None, description="Unique type identifier")
    file_path: str | None = Field(default=None, description="File path")
    symbol_id: str | None = Field(default=None, description="Associated symbol ID")
    name: str = Field(..., description="Type name")
    kind: str = Field(..., description="Type kind (annotation, alias, generic, interface)")
    type_expression: str = Field(..., description="Type expression string")
    start_line: int = Field(..., description="Start line number")
    end_line: int = Field(..., description="End line number")
    is_generic: bool = Field(default=False, description="Is generic type")
    generic_params: list[str] = Field(default_factory=list, description="Generic parameters")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ImportInfo(BaseModel):
    """Information about an import statement."""

    import_id: str | None = Field(default=None, description="Unique import identifier")
    file_path: str | None = Field(default=None, description="File path")
    module_path: str = Field(..., description="Imported module path")
    imported_names: list[str] = Field(default_factory=list, description="Imported names")
    alias: str | None = Field(default=None, description="Import alias")
    is_relative: bool = Field(default=False, description="Is relative import")
    relative_level: int = Field(default=0, description="Relative import level")
    import_kind: str = Field(..., description="Import kind (import, from_import)")
    start_line: int = Field(..., description="Line number")
    is_type_only: bool = Field(default=False, description="Is type-only import")


class ExportInfo(BaseModel):
    """Information about an export."""

    export_id: str | None = Field(default=None, description="Unique export identifier")
    file_path: str | None = Field(default=None, description="File path")
    symbol_id: str | None = Field(default=None, description="Associated symbol ID")
    exported_name: str = Field(..., description="Exported name")
    original_name: str | None = Field(default=None, description="Original name if re-exported")
    export_kind: str = Field(..., description="Export kind (direct, re_export, default)")
    start_line: int = Field(..., description="Line number")


class ScopeInfo(BaseModel):
    """Information about a lexical scope."""

    scope_id: str | None = Field(default=None, description="Unique scope identifier")
    file_path: str | None = Field(default=None, description="File path")
    parent_scope_id: str | None = Field(default=None, description="Parent scope ID")
    kind: str = Field(..., description="Scope kind (module, class, function, block)")
    name: str | None = Field(default=None, description="Scope name")
    start_line: int = Field(..., description="Start line number")
    end_line: int = Field(..., description="End line number")
    depth: int = Field(default=0, description="Nesting depth")


class ReferenceInfo(BaseModel):
    """Information about a symbol reference."""

    reference_id: str | None = Field(default=None, description="Unique reference identifier")
    file_path: str | None = Field(default=None, description="File path")
    symbol_id: str | None = Field(default=None, description="Referenced symbol ID")
    name: str = Field(..., description="Referenced name")
    kind: str = Field(..., description="Reference kind (read, write, call, type_reference)")
    start_line: int = Field(..., description="Line number")
    start_col: int = Field(default=0, description="Column number")
    scope_id: str | None = Field(default=None, description="Scope ID")
    is_definition: bool = Field(default=False, description="Is definition site")


class EdgeInfo(BaseModel):
    """Information about a resolved graph edge (from LSP)."""

    edge_id: str | None = Field(default=None, description="Unique edge identifier")
    source_file: str = Field(..., description="Source file path")
    source_line: int = Field(..., description="Source line number")
    source_col: int = Field(default=0, description="Source column")
    source_symbol_id: str | None = Field(default=None, description="Source symbol ID")
    target_file: str = Field(..., description="Target file path")
    target_line: int = Field(..., description="Target line number")
    target_col: int = Field(default=0, description="Target column")
    target_symbol_id: str | None = Field(default=None, description="Target symbol ID")
    edge_type: str = Field(
        ..., description="Edge type (definition, call, extends, implements, type_ref)"
    )
    resolved_by: str = Field(default="lsp", description="Resolution method (lsp, heuristic)")
    lsp_server: str | None = Field(default=None, description="LSP server name")
    resolved_at: datetime | None = Field(default=None, description="Resolution timestamp")


class CodeIntelStats(BaseModel):
    """Statistics for code intelligence index."""

    total_files: int = Field(default=0, description="Total indexed files")
    total_symbols: int = Field(default=0, description="Total symbols")
    total_types: int = Field(default=0, description="Total types")
    total_imports: int = Field(default=0, description="Total imports")
    total_exports: int = Field(default=0, description="Total exports")
    total_scopes: int = Field(default=0, description="Total scopes")
    total_references: int = Field(default=0, description="Total references")
    total_edges: int = Field(default=0, description="Total resolved edges")
    languages: dict[str, int] = Field(default_factory=dict, description="Files per language")
    last_indexed: datetime | None = Field(default=None, description="Last indexing time")
