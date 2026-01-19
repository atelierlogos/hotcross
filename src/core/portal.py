"""MemoryPortal class - core abstraction for a single portal."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.core.database import ChDBAdapter
from src.core.metadata import MetadataManager
from src.models.schemas import (
    ColumnSchema,
    DeleteResult,
    PortalInfo,
    PortalStats,
    QueryResult,
    TableSchema,
    WriteResult,
)
from src.uri.parser import MemoryURI

logger = logging.getLogger(__name__)


class MemoryPortal:
    """A single memory portal backed by chDB.

    Provides CRUD operations, schema management, and statistics access.
    """

    def __init__(
        self,
        namespace: str,
        portal_id: str,
        db_path: str | Path,
        name: str | None = None,
        description: str | None = None,
    ):
        """Initialize a memory portal.

        Args:
            namespace: Portal namespace
            portal_id: Portal identifier
            db_path: Path to the .db file
            name: Human-readable portal name
            description: Portal description
        """
        self._namespace = namespace
        self._portal_id = portal_id
        self._db_path = Path(db_path)
        self._name = name or f"{namespace}/{portal_id}"
        self._description = description

        self._db = ChDBAdapter(self._db_path)
        self._metadata = MetadataManager(self._db)
        self._initialized = False

    @property
    def namespace(self) -> str:
        """Get the portal namespace."""
        return self._namespace

    @property
    def portal_id(self) -> str:
        """Get the portal identifier."""
        return self._portal_id

    @property
    def uri(self) -> str:
        """Get the portal URI."""
        return f"mem://{self._namespace}/{self._portal_id}"

    @property
    def db_path(self) -> Path:
        """Get the database file path."""
        return self._db_path

    @property
    def name(self) -> str:
        """Get the portal name."""
        return self._name

    @property
    def description(self) -> str | None:
        """Get the portal description."""
        return self._description

    def _ensure_initialized(self) -> None:
        """Ensure the portal is initialized with metadata."""
        if not self._initialized:
            self._metadata.initialize_portal(
                portal_id=self._portal_id,
                name=self._name,
                description=self._description,
            )
            self._initialized = True

    def write(
        self,
        table: str,
        data: list[dict[str, Any]],
        create_table: bool = True,
        schema: TableSchema | None = None,
    ) -> WriteResult:
        """Write data to a table.

        Args:
            table: Target table name
            data: List of row dictionaries
            create_table: Auto-create table if it doesn't exist
            schema: Optional explicit schema for table creation

        Returns:
            WriteResult with rows_written count

        Raises:
            ValueError: If table doesn't exist and create_table is False
        """
        self._ensure_initialized()

        if not data:
            return WriteResult(rows_written=0, table=table, portal_uri=self.uri)

        if not self._db.table_exists(table):
            if not create_table:
                raise ValueError(f"Table '{table}' does not exist")
            self._create_table_from_data(table, data, schema)

        rows_written = self._db.insert_rows(table, data)
        logger.info(f"Wrote {rows_written} rows to {self.uri}/{table}")

        return WriteResult(rows_written=rows_written, table=table, portal_uri=self.uri)

    def _create_table_from_data(
        self,
        table: str,
        data: list[dict[str, Any]],
        schema: TableSchema | None = None,
    ) -> None:
        """Create a table from sample data or explicit schema.

        Args:
            table: Table name
            data: Sample data for schema inference
            schema: Optional explicit schema
        """
        if schema:
            columns_sql = ", ".join(
                f"`{col.name}` {col.type}"
                + (f" DEFAULT {col.default}" if col.default else "")
                for col in schema.columns
            )
            order_by = schema.order_by or [schema.columns[0].name] if schema.columns else ["tuple()"]
        else:
            columns_sql, order_by = self._infer_schema(data)

        order_by_sql = ", ".join(f"`{c}`" for c in order_by)
        create_sql = (
            f"CREATE TABLE IF NOT EXISTS `{table}` ({columns_sql}) "
            f"ENGINE = MergeTree() ORDER BY ({order_by_sql})"
        )

        self._db.execute_command(create_sql)
        logger.info(f"Created table {table} in {self.uri}")

    def _infer_schema(self, data: list[dict[str, Any]]) -> tuple[str, list[str]]:
        """Infer schema from sample data.

        Args:
            data: Sample data rows

        Returns:
            Tuple of (columns_sql, order_by_columns)
        """
        if not data:
            raise ValueError("Cannot infer schema from empty data")

        sample = data[0]
        columns = []

        for key, value in sample.items():
            col_type = self._infer_type(value)
            columns.append(f"`{key}` {col_type}")

        first_col = list(sample.keys())[0]
        return ", ".join(columns), [first_col]

    def _infer_type(self, value: Any) -> str:
        """Infer ClickHouse type from Python value.

        Args:
            value: Python value

        Returns:
            ClickHouse type string
        """
        if value is None:
            return "Nullable(String)"
        elif isinstance(value, bool):
            return "Bool"
        elif isinstance(value, int):
            return "Int64"
        elif isinstance(value, float):
            return "Float64"
        elif isinstance(value, str):
            return "String"
        elif isinstance(value, list):
            if value:
                inner_type = self._infer_type(value[0])
                return f"Array({inner_type})"
            return "Array(String)"
        elif isinstance(value, dict):
            return "String"  # Store as JSON string
        else:
            return "String"

    def query(self, sql: str) -> QueryResult:
        """Execute a SQL query.

        Args:
            sql: SQL query (SELECT statements only recommended)

        Returns:
            QueryResult with data and metadata
        """
        self._ensure_initialized()

        import time
        start = time.perf_counter()
        data = self._db.query(sql)
        execution_time = (time.perf_counter() - start) * 1000

        column_names = list(data[0].keys()) if data else []

        return QueryResult(
            data=data,
            row_count=len(data),
            column_names=column_names,
            execution_time_ms=execution_time,
        )

    def delete(
        self,
        table: str,
        where: dict[str, Any] | None = None,
        delete_all: bool = False,
    ) -> DeleteResult:
        """Delete data from a table.

        Args:
            table: Target table name
            where: Conditions for deletion (key-value pairs for equality)
            delete_all: Delete all rows if True (requires explicit flag)

        Returns:
            DeleteResult with rows_deleted count

        Raises:
            ValueError: If neither where nor delete_all is specified
        """
        self._ensure_initialized()

        if not self._db.table_exists(table):
            raise ValueError(f"Table '{table}' does not exist")

        count_before = self._db.get_table_row_count(table)

        if delete_all:
            self._db.execute_command(f"TRUNCATE TABLE `{table}`")
        elif where:
            conditions = " AND ".join(
                f"`{k}` = {self._db._format_value(v)}" for k, v in where.items()
            )
            self._db.execute_command(f"ALTER TABLE `{table}` DELETE WHERE {conditions}")
        else:
            raise ValueError("Must specify 'where' conditions or set 'delete_all=True'")

        count_after = self._db.get_table_row_count(table)
        rows_deleted = count_before - count_after

        logger.info(f"Deleted {rows_deleted} rows from {self.uri}/{table}")

        return DeleteResult(rows_deleted=rows_deleted, table=table, portal_uri=self.uri)

    def drop_table(self, table: str) -> None:
        """Drop a table entirely.

        Args:
            table: Table name to drop
        """
        self._ensure_initialized()
        self._db.execute_command(f"DROP TABLE IF EXISTS `{table}`")
        logger.info(f"Dropped table {table} from {self.uri}")

    def get_tables(self) -> list[str]:
        """Get list of tables (excluding metadata table).

        Returns:
            List of table names
        """
        self._ensure_initialized()
        tables = self._db.get_tables()
        return [t for t in tables if not t.startswith("_mcp_")]

    def get_table_schema(self, table: str) -> TableSchema:
        """Get schema for a table.

        Args:
            table: Table name

        Returns:
            TableSchema with column definitions
        """
        self._ensure_initialized()

        columns_data = self._db.get_table_schema(table)
        columns = [
            ColumnSchema(
                name=col["name"],
                type=col["type"],
                primary=bool(col.get("is_in_primary_key")),
                nullable="Nullable" in col["type"],
                default=col.get("default_expression") or None,
            )
            for col in columns_data
        ]

        return TableSchema(name=table, columns=columns)

    def get_stats(self) -> PortalStats:
        """Get statistics for the portal.

        Returns:
            PortalStats with row counts and table info
        """
        self._ensure_initialized()

        tables = self.get_tables()
        table_stats = {}
        total_rows = 0

        for table in tables:
            count = self._db.get_table_row_count(table)
            table_stats[table] = count
            total_rows += count

        size_bytes = 0
        if self._db_path.exists():
            size_bytes = sum(
                f.stat().st_size
                for f in self._db_path.rglob("*")
                if f.is_file()
            ) if self._db_path.is_dir() else self._db_path.stat().st_size

        return PortalStats(
            total_rows=total_rows,
            total_tables=len(tables),
            size_bytes=size_bytes,
            table_stats=table_stats,
        )

    def get_info(self) -> PortalInfo:
        """Get full portal information.

        Returns:
            PortalInfo with schema and stats
        """
        self._ensure_initialized()

        tables = self.get_tables()
        schema = {table: self.get_table_schema(table) for table in tables}
        stats = self.get_stats()
        meta_info = self._metadata.get_portal_info()

        from datetime import datetime

        created_at = None
        if meta_info.get("created_at"):
            try:
                created_at = datetime.fromisoformat(meta_info["created_at"])
            except (ValueError, TypeError):
                pass

        return PortalInfo(
            uri=self.uri,
            name=self._name,
            description=self._description,
            db_path=str(self._db_path),
            tables_schema=schema,
            stats=stats,
            created_at=created_at,
        )

    def get_metadata(self, key: str, default: str | None = None) -> str | None:
        """Get a metadata value.

        Args:
            key: Metadata key
            default: Default value

        Returns:
            Metadata value or default
        """
        self._ensure_initialized()
        return self._metadata.get(key, default)

    def set_metadata(self, key: str, value: str) -> None:
        """Set a metadata value.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._ensure_initialized()
        self._metadata.set(key, value)

    def close(self) -> None:
        """Close the portal and release resources."""
        self._db.close()
        logger.debug(f"Closed portal {self.uri}")

    def __enter__(self) -> MemoryPortal:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return f"MemoryPortal(uri={self.uri!r}, db_path={str(self._db_path)!r})"
