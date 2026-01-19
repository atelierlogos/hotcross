"""Portal registry for managing multiple memory portals."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.core.portal import MemoryPortal
from src.uri.parser import MemoryURI

logger = logging.getLogger(__name__)


class PortalRegistry:
    """Registry for managing multiple memory portals.

    Provides portal resolution, lifecycle management, and URI-based access.
    """

    def __init__(self, base_path: str | Path | None = None):
        """Initialize the registry.

        Args:
            base_path: Base directory for portal databases.
                      Defaults to ~/.memory-portals/
        """
        if base_path is None:
            base_path = Path.home() / ".memory-portals"
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

        self._portals: dict[str, MemoryPortal] = {}
        logger.info(f"Initialized portal registry at {self._base_path}")

    @property
    def base_path(self) -> Path:
        """Get the base path for portal databases."""
        return self._base_path

    def _portal_key(self, namespace: str, portal_id: str) -> str:
        """Generate a unique key for a portal.

        Args:
            namespace: Portal namespace
            portal_id: Portal identifier

        Returns:
            Unique key string
        """
        return f"{namespace}/{portal_id}"

    def _db_path_for(self, namespace: str, portal_id: str) -> Path:
        """Get the database path for a portal.

        Args:
            namespace: Portal namespace
            portal_id: Portal identifier

        Returns:
            Path to the .db directory
        """
        return self._base_path / namespace / f"{portal_id}.db"

    def register(
        self,
        namespace: str,
        portal_id: str,
        name: str | None = None,
        description: str | None = None,
        db_path: str | Path | None = None,
    ) -> MemoryPortal:
        """Register a new portal or return existing one.

        Args:
            namespace: Portal namespace
            portal_id: Portal identifier
            name: Human-readable name
            description: Portal description
            db_path: Optional custom database path

        Returns:
            MemoryPortal instance
        """
        key = self._portal_key(namespace, portal_id)

        if key in self._portals:
            logger.debug(f"Returning existing portal: {key}")
            return self._portals[key]

        if db_path is None:
            db_path = self._db_path_for(namespace, portal_id)

        portal = MemoryPortal(
            namespace=namespace,
            portal_id=portal_id,
            db_path=db_path,
            name=name,
            description=description,
        )

        self._portals[key] = portal
        logger.info(f"Registered portal: {key}")

        return portal

    def get(self, namespace: str, portal_id: str) -> MemoryPortal | None:
        """Get a portal by namespace and id.

        Args:
            namespace: Portal namespace
            portal_id: Portal identifier

        Returns:
            MemoryPortal or None if not registered
        """
        key = self._portal_key(namespace, portal_id)
        return self._portals.get(key)

    def get_or_create(
        self,
        namespace: str,
        portal_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> MemoryPortal:
        """Get existing portal or create a new one.

        Args:
            namespace: Portal namespace
            portal_id: Portal identifier
            name: Human-readable name (for creation)
            description: Portal description (for creation)

        Returns:
            MemoryPortal instance
        """
        portal = self.get(namespace, portal_id)
        if portal is not None:
            return portal
        return self.register(namespace, portal_id, name, description)

    def resolve(self, uri: str | MemoryURI) -> MemoryPortal:
        """Resolve a URI to a portal, creating if needed.

        Args:
            uri: mem:// URI string or MemoryURI instance

        Returns:
            MemoryPortal instance

        Raises:
            ValueError: If URI is invalid
        """
        if isinstance(uri, str):
            uri = MemoryURI.parse(uri)

        return self.get_or_create(uri.namespace, uri.portal_id)

    def unregister(self, namespace: str, portal_id: str) -> bool:
        """Unregister a portal (does not delete data).

        Args:
            namespace: Portal namespace
            portal_id: Portal identifier

        Returns:
            True if portal was registered and removed
        """
        key = self._portal_key(namespace, portal_id)

        if key in self._portals:
            portal = self._portals.pop(key)
            portal.close()
            logger.info(f"Unregistered portal: {key}")
            return True

        return False

    def list_portals(self) -> list[dict[str, Any]]:
        """List all registered portals.

        Returns:
            List of portal info dictionaries
        """
        return [
            {
                "uri": portal.uri,
                "namespace": portal.namespace,
                "portal_id": portal.portal_id,
                "name": portal.name,
                "description": portal.description,
                "db_path": str(portal.db_path),
            }
            for portal in self._portals.values()
        ]

    def discover_portals(self) -> list[dict[str, str]]:
        """Discover portals from the filesystem.

        Scans the base path for existing .db directories.

        Returns:
            List of discovered portal info
        """
        discovered = []

        if not self._base_path.exists():
            return discovered

        for namespace_dir in self._base_path.iterdir():
            if not namespace_dir.is_dir() or namespace_dir.name.startswith("."):
                continue

            namespace = namespace_dir.name

            for db_path in namespace_dir.glob("*.db"):
                portal_id = db_path.stem
                discovered.append({
                    "uri": f"mem://{namespace}/{portal_id}",
                    "namespace": namespace,
                    "portal_id": portal_id,
                    "db_path": str(db_path),
                })

        logger.debug(f"Discovered {len(discovered)} portals")
        return discovered

    def load_discovered(self) -> int:
        """Load all discovered portals into the registry.

        Returns:
            Number of portals loaded
        """
        discovered = self.discover_portals()
        loaded = 0

        for info in discovered:
            key = self._portal_key(info["namespace"], info["portal_id"])
            if key not in self._portals:
                self.register(
                    namespace=info["namespace"],
                    portal_id=info["portal_id"],
                    db_path=info["db_path"],
                )
                loaded += 1

        logger.info(f"Loaded {loaded} discovered portals")
        return loaded

    def close_all(self) -> None:
        """Close all registered portals."""
        for portal in self._portals.values():
            portal.close()
        self._portals.clear()
        logger.info("Closed all portals")

    def __len__(self) -> int:
        """Get number of registered portals."""
        return len(self._portals)

    def __contains__(self, uri: str) -> bool:
        """Check if a portal URI is registered."""
        try:
            parsed = MemoryURI.parse(uri)
            key = self._portal_key(parsed.namespace, parsed.portal_id)
            return key in self._portals
        except ValueError:
            return False

    def __iter__(self):
        """Iterate over registered portals."""
        return iter(self._portals.values())
