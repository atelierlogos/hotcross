"""Memory URI parser for mem:// scheme."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode


@dataclass(frozen=True)
class MemoryURI:
    """Parsed mem:// URI representation.

    URI format: mem://{namespace}/{portal-id}[/{table}][?query]

    Examples:
        - mem://conversation/default
        - mem://conversation/default/messages
        - mem://conversation/default/messages?limit=10&since=2024-01-01
    """

    namespace: str
    portal_id: str
    table: str | None = None
    query_params: dict[str, list[str]] | None = None

    _URI_PATTERN = re.compile(
        r"^mem://(?P<namespace>[a-zA-Z0-9_-]+)/(?P<portal_id>[a-zA-Z0-9_-]+)"
        r"(?:/(?P<table>[a-zA-Z0-9_-]+))?(?:\?(?P<query>.*))?$"
    )

    @classmethod
    def parse(cls, uri: str) -> MemoryURI:
        """Parse a mem:// URI string.

        Args:
            uri: The URI string to parse

        Returns:
            Parsed MemoryURI instance

        Raises:
            ValueError: If the URI is invalid
        """
        if not uri:
            raise ValueError("URI cannot be empty")

        match = cls._URI_PATTERN.match(uri)
        if not match:
            raise ValueError(
                f"Invalid mem:// URI: {uri}. "
                "Expected format: mem://{{namespace}}/{{portal-id}}[/{{table}}][?query]"
            )

        groups = match.groupdict()
        query_params = None
        if groups.get("query"):
            query_params = parse_qs(groups["query"])

        return cls(
            namespace=groups["namespace"],
            portal_id=groups["portal_id"],
            table=groups.get("table"),
            query_params=query_params,
        )

    @property
    def portal_uri(self) -> str:
        """Get the base portal URI without table or query params."""
        return f"mem://{self.namespace}/{self.portal_id}"

    @property
    def full_uri(self) -> str:
        """Get the full URI including table and query params."""
        uri = self.portal_uri
        if self.table:
            uri += f"/{self.table}"
        if self.query_params:
            uri += "?" + urlencode(self.query_params, doseq=True)
        return uri

    def with_table(self, table: str) -> MemoryURI:
        """Create a new URI with a different table."""
        return MemoryURI(
            namespace=self.namespace,
            portal_id=self.portal_id,
            table=table,
            query_params=self.query_params,
        )

    def with_query(self, **params: Any) -> MemoryURI:
        """Create a new URI with additional/modified query parameters."""
        new_params = dict(self.query_params) if self.query_params else {}
        for key, value in params.items():
            if value is None:
                new_params.pop(key, None)
            elif isinstance(value, list):
                new_params[key] = [str(v) for v in value]
            else:
                new_params[key] = [str(value)]
        return MemoryURI(
            namespace=self.namespace,
            portal_id=self.portal_id,
            table=self.table,
            query_params=new_params if new_params else None,
        )

    def get_param(self, key: str, default: str | None = None) -> str | None:
        """Get a single query parameter value."""
        if not self.query_params or key not in self.query_params:
            return default
        values = self.query_params[key]
        return values[0] if values else default

    def get_param_list(self, key: str) -> list[str]:
        """Get all values for a query parameter."""
        if not self.query_params or key not in self.query_params:
            return []
        return self.query_params[key]

    def __str__(self) -> str:
        """String representation returns the full URI."""
        return self.full_uri

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"MemoryURI(namespace={self.namespace!r}, portal_id={self.portal_id!r}, "
            f"table={self.table!r}, query_params={self.query_params!r})"
        )
