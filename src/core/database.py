"""ChDB database adapter for Memory Portals."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from chdb import session as chdb_session

logger = logging.getLogger(__name__)


class ChDBAdapter:
    """Wrapper around chDB session for database operations.

    Provides lazy connection initialization, query execution,
    and format conversion for Memory Portals.
    """

    def __init__(self, db_path: str | Path):
        """Initialize the adapter.

        Args:
            db_path: Path to the chDB database file
        """
        self._db_path = Path(db_path)
        self._session: chdb_session.Session | None = None

    @property
    def db_path(self) -> Path:
        """Get the database file path."""
        return self._db_path

    @property
    def session(self) -> chdb_session.Session:
        """Get or create the chDB session (lazy initialization)."""
        if self._session is None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._session = chdb_session.Session(str(self._db_path))
            logger.debug(f"Created chDB session at {self._db_path}")
        return self._session

    def execute(self, sql: str, output_format: str = "JSON") -> str:
        """Execute a SQL query and return raw result.

        Args:
            sql: SQL query to execute
            output_format: Output format (JSON, CSV, etc.)

        Returns:
            Raw query result as string
        """
        result = self.session.query(sql, output_format)
        return result.bytes().decode("utf-8") if result.bytes() else ""

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts.

        Args:
            sql: SQL SELECT query

        Returns:
            List of row dictionaries
        """
        result = self.execute(sql, "JSON")
        if not result:
            return []
        try:
            parsed = json.loads(result)
            return parsed.get("data", [])
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON result: {result[:200]}")
            return []

    def query_single(self, sql: str) -> dict[str, Any] | None:
        """Execute a query expecting a single row result.

        Args:
            sql: SQL query

        Returns:
            Single row dictionary or None
        """
        rows = self.query(sql)
        return rows[0] if rows else None

    def query_value(self, sql: str) -> Any:
        """Execute a query expecting a single value result.

        Args:
            sql: SQL query

        Returns:
            Single value from first column of first row, or None
        """
        row = self.query_single(sql)
        if row:
            return next(iter(row.values()), None)
        return None

    def execute_command(self, sql: str) -> None:
        """Execute a non-SELECT SQL command (CREATE, INSERT, etc.).

        Args:
            sql: SQL command to execute
        """
        self.session.query(sql)

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the current database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists
        """
        result = self.query_value(
            f"SELECT count() FROM system.tables "
            f"WHERE name = '{table_name}' AND database = currentDatabase()"
        )
        return bool(result and int(result) > 0)

    def get_tables(self) -> list[str]:
        """Get list of all user tables (excluding system tables).

        Returns:
            List of table names
        """
        rows = self.query(
            "SELECT name FROM system.tables WHERE database = currentDatabase() "
            "AND name NOT LIKE '.%' ORDER BY name"
        )
        return [row["name"] for row in rows]

    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            List of column definitions with name, type, default_kind, etc.
        """
        return self.query(
            f"SELECT name, type, default_kind, default_expression, is_in_primary_key "
            f"FROM system.columns WHERE table = '{table_name}' "
            f"AND database = currentDatabase() ORDER BY position"
        )

    def get_table_row_count(self, table_name: str) -> int:
        """Get the row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows
        """
        result = self.query_value(f"SELECT count() FROM `{table_name}`")
        return int(result) if result else 0

    def insert_rows(
        self, table_name: str, rows: list[dict[str, Any]], columns: list[str] | None = None
    ) -> int:
        """Insert rows into a table.

        Args:
            table_name: Target table name
            rows: List of row dictionaries
            columns: Optional column order (inferred from first row if not provided)

        Returns:
            Number of rows inserted
        """
        if not rows:
            return 0

        if columns is None:
            columns = list(rows[0].keys())

        col_list = ", ".join(f"`{c}`" for c in columns)
        values_list = []

        for row in rows:
            values = []
            for col in columns:
                val = row.get(col)
                values.append(self._format_value(val))
            values_list.append(f"({', '.join(values)})")

        sql = f"INSERT INTO `{table_name}` ({col_list}) VALUES {', '.join(values_list)}"
        self.execute_command(sql)
        return len(rows)

    def _format_value(self, value: Any) -> str:
        """Format a Python value for SQL insertion.

        Args:
            value: Python value

        Returns:
            SQL-formatted string
        """
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace("'", "\\'")
            return f"'{escaped}'"
        elif isinstance(value, (list, dict)):
            json_str = json.dumps(value)
            escaped = json_str.replace("\\", "\\\\").replace("'", "\\'")
            return f"'{escaped}'"
        else:
            escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
            return f"'{escaped}'"

    def close(self) -> None:
        """Close the database session."""
        if self._session is not None:
            self._session = None
            logger.debug(f"Closed chDB session at {self._db_path}")

    def __enter__(self) -> ChDBAdapter:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
