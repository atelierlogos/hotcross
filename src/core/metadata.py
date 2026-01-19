"""Metadata table management for Memory Portals."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.database import ChDBAdapter

logger = logging.getLogger(__name__)

METADATA_TABLE = "_mcp_metadata"

METADATA_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {METADATA_TABLE} (
    key String,
    value String,
    created_at DateTime64(3) DEFAULT now64(3),
    updated_at DateTime64(3) DEFAULT now64(3)
) ENGINE = MergeTree()
ORDER BY key
"""


class MetadataManager:
    """Manages the _mcp_metadata table for a Memory Portal.

    Standard metadata keys:
    - mcp.version: MCP protocol version
    - mcp.portal.id: Portal identifier
    - mcp.portal.name: Human-readable name
    - mcp.portal.description: Portal description
    - mcp.server.name: Creating server name
    - mcp.server.version: Creating server version
    - mcp.created_at: Creation timestamp
    - mcp.schema_version: Schema version for migrations
    """

    def __init__(self, db: ChDBAdapter):
        """Initialize the metadata manager.

        Args:
            db: ChDB adapter instance
        """
        self._db = db
        self._initialized = False

    def ensure_table(self) -> None:
        """Ensure the metadata table exists."""
        if not self._initialized:
            self._db.execute_command(METADATA_SCHEMA)
            self._initialized = True
            logger.debug("Ensured _mcp_metadata table exists")

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get a metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        self.ensure_table()
        result = self._db.query_single(
            f"SELECT value FROM {METADATA_TABLE} WHERE key = '{key}' "
            "ORDER BY updated_at DESC LIMIT 1"
        )
        return result["value"] if result else default

    def set(self, key: str, value: str) -> None:
        """Set a metadata value (upsert).

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.ensure_table()
        escaped_value = value.replace("\\", "\\\\").replace("'", "\\'")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        existing = self.get(key)
        if existing is not None:
            self._db.execute_command(
                f"ALTER TABLE {METADATA_TABLE} DELETE WHERE key = '{key}'"
            )

        self._db.execute_command(
            f"INSERT INTO {METADATA_TABLE} (key, value, created_at, updated_at) "
            f"VALUES ('{key}', '{escaped_value}', '{now}', '{now}')"
        )
        logger.debug(f"Set metadata {key}={value}")

    def delete(self, key: str) -> bool:
        """Delete a metadata key.

        Args:
            key: Metadata key to delete

        Returns:
            True if key existed and was deleted
        """
        self.ensure_table()
        existing = self.get(key)
        if existing is not None:
            self._db.execute_command(
                f"ALTER TABLE {METADATA_TABLE} DELETE WHERE key = '{key}'"
            )
            logger.debug(f"Deleted metadata key: {key}")
            return True
        return False

    def get_all(self) -> dict[str, str]:
        """Get all metadata as a dictionary.

        Returns:
            Dictionary of all metadata key-value pairs
        """
        self.ensure_table()
        rows = self._db.query(
            f"SELECT key, value FROM {METADATA_TABLE} ORDER BY key"
        )
        return {row["key"]: row["value"] for row in rows}

    def set_many(self, metadata: dict[str, str]) -> None:
        """Set multiple metadata values.

        Args:
            metadata: Dictionary of key-value pairs
        """
        for key, value in metadata.items():
            self.set(key, value)

    def initialize_portal(
        self,
        portal_id: str,
        name: str,
        description: str | None = None,
        server_name: str = "memory-portals",
        server_version: str = "0.1.0",
        mcp_version: str = "1.0",
    ) -> None:
        """Initialize portal metadata with standard keys.

        Args:
            portal_id: Portal identifier
            name: Human-readable portal name
            description: Optional portal description
            server_name: Name of the creating server
            server_version: Version of the creating server
            mcp_version: MCP protocol version
        """
        now = datetime.now(timezone.utc).isoformat()

        metadata: dict[str, str] = {
            "mcp.version": mcp_version,
            "mcp.portal.id": portal_id,
            "mcp.portal.name": name,
            "mcp.server.name": server_name,
            "mcp.server.version": server_version,
            "mcp.created_at": now,
            "mcp.schema_version": "1",
        }

        if description:
            metadata["mcp.portal.description"] = description

        for key, value in metadata.items():
            if self.get(key) is None:
                self.set(key, value)

        logger.info(f"Initialized portal metadata for {portal_id}")

    def get_portal_info(self) -> dict[str, Any]:
        """Get portal information from metadata.

        Returns:
            Dictionary with portal info
        """
        all_meta = self.get_all()
        return {
            "id": all_meta.get("mcp.portal.id"),
            "name": all_meta.get("mcp.portal.name"),
            "description": all_meta.get("mcp.portal.description"),
            "mcp_version": all_meta.get("mcp.version"),
            "server_name": all_meta.get("mcp.server.name"),
            "server_version": all_meta.get("mcp.server.version"),
            "created_at": all_meta.get("mcp.created_at"),
            "schema_version": all_meta.get("mcp.schema_version"),
        }
