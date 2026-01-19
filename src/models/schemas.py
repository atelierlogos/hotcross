"""Pydantic models for Memory Portals."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    """Schema for a table column."""

    name: str = Field(..., description="Column name")
    type: str = Field(..., description="ClickHouse/chDB column type")
    primary: bool = Field(default=False, description="Whether this is a primary key column")
    nullable: bool = Field(default=True, description="Whether NULL values are allowed")
    default: str | None = Field(default=None, description="Default value expression")


class TableSchema(BaseModel):
    """Schema for a table."""

    name: str = Field(..., description="Table name")
    columns: list[ColumnSchema] = Field(default_factory=list, description="Column definitions")
    order_by: list[str] | None = Field(default=None, description="ORDER BY columns for MergeTree")
    partition_by: str | None = Field(default=None, description="PARTITION BY expression")


class PortalStats(BaseModel):
    """Statistics for a memory portal."""

    total_rows: int = Field(default=0, description="Total rows across all tables")
    total_tables: int = Field(default=0, description="Number of tables")
    size_bytes: int = Field(default=0, description="Approximate storage size in bytes")
    table_stats: dict[str, int] = Field(
        default_factory=dict, description="Row count per table"
    )


class PortalInfo(BaseModel):
    """Information about a memory portal."""

    uri: str = Field(..., description="Portal URI (mem://namespace/portal-id)")
    name: str = Field(..., description="Human-readable portal name")
    description: str | None = Field(default=None, description="Portal description")
    db_path: str = Field(..., description="Path to the .db file")
    tables_schema: dict[str, TableSchema] = Field(
        default_factory=dict, description="Table schemas by name"
    )
    stats: PortalStats = Field(default_factory=PortalStats, description="Portal statistics")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class WriteResult(BaseModel):
    """Result of a write operation."""

    rows_written: int = Field(..., description="Number of rows written")
    table: str = Field(..., description="Target table name")
    portal_uri: str = Field(..., description="Portal URI")


class QueryResult(BaseModel):
    """Result of a query operation."""

    data: list[dict[str, Any]] = Field(default_factory=list, description="Query result rows")
    row_count: int = Field(default=0, description="Number of rows returned")
    column_names: list[str] = Field(default_factory=list, description="Column names in order")
    execution_time_ms: float | None = Field(default=None, description="Query execution time")


class DeleteResult(BaseModel):
    """Result of a delete operation."""

    rows_deleted: int = Field(..., description="Number of rows deleted")
    table: str = Field(..., description="Target table name")
    portal_uri: str = Field(..., description="Portal URI")


class ImportResult(BaseModel):
    """Result of an import operation."""

    rows_imported: int = Field(..., description="Number of rows imported")
    table: str = Field(..., description="Target table name")
    portal_uri: str = Field(..., description="Portal URI")
    source: str = Field(..., description="Source file path or URL")


class ExportResult(BaseModel):
    """Result of an export operation."""

    rows_exported: int = Field(..., description="Number of rows exported")
    destination: str = Field(..., description="Export destination path")
    format: str = Field(..., description="Export format")
    portal_uri: str = Field(..., description="Portal URI")
