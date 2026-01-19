"""Tests for MCP server tools."""

import json
import tempfile
from pathlib import Path

import pytest

from src.core.registry import PortalRegistry
from src import server
from src.core import middleware


@pytest.fixture(autouse=True)
def setup_test_registry(temp_dir):
    """Replace the global registry with a test registry and disable auth."""
    original_registry = server.registry
    original_auth_enabled = middleware._auth_enabled
    
    # Disable auth for tests
    middleware._auth_enabled = False
    
    server.registry = PortalRegistry(base_path=temp_dir)
    yield
    server.registry.close_all()
    server.registry = original_registry
    middleware._auth_enabled = original_auth_enabled


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestMemoryWrite:
    """Tests for memory_write tool."""

    def test_write_basic(self):
        """Test basic write operation."""
        result = server.memory_write(
            portal_uri="mem://test/write",
            table="users",
            data=[{"id": 1, "name": "Alice"}],
        )

        assert result["success"] is True
        assert result["rows_written"] == 1
        assert result["table"] == "users"

    def test_write_multiple_rows(self):
        """Test writing multiple rows."""
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]

        result = server.memory_write(
            portal_uri="mem://test/multi",
            table="users",
            data=data,
        )

        assert result["success"] is True
        assert result["rows_written"] == 3

    def test_write_empty(self):
        """Test writing empty data."""
        result = server.memory_write(
            portal_uri="mem://test/empty",
            table="users",
            data=[],
        )

        assert result["success"] is True
        assert result["rows_written"] == 0

    def test_write_invalid_uri(self):
        """Test write with invalid URI."""
        result = server.memory_write(
            portal_uri="invalid://uri",
            table="users",
            data=[{"id": 1}],
        )

        assert result["success"] is False
        assert "error" in result


class TestMemoryQuery:
    """Tests for memory_query tool."""

    def test_query_basic(self):
        """Test basic query operation."""
        server.memory_write(
            portal_uri="mem://test/query",
            table="users",
            data=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        )

        result = server.memory_query(
            portal_uri="mem://test/query",
            sql="SELECT * FROM users ORDER BY id",
        )

        assert result["success"] is True
        assert result["row_count"] == 2
        assert result["data"][0]["name"] == "Alice"

    def test_query_with_filter(self):
        """Test query with WHERE clause."""
        server.memory_write(
            portal_uri="mem://test/filter",
            table="users",
            data=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        )

        result = server.memory_query(
            portal_uri="mem://test/filter",
            sql="SELECT * FROM users WHERE id = 1",
        )

        assert result["success"] is True
        assert result["row_count"] == 1
        assert result["data"][0]["name"] == "Alice"

    def test_query_empty_result(self):
        """Test query returning no results."""
        server.memory_write(
            portal_uri="mem://test/empty_query",
            table="users",
            data=[{"id": 1}],
        )

        result = server.memory_query(
            portal_uri="mem://test/empty_query",
            sql="SELECT * FROM users WHERE id = 999",
        )

        assert result["success"] is True
        assert result["row_count"] == 0
        assert result["data"] == []


class TestMemoryDelete:
    """Tests for memory_delete tool."""

    def test_delete_with_where(self):
        """Test delete with conditions."""
        server.memory_write(
            portal_uri="mem://test/delete",
            table="users",
            data=[{"id": 1}, {"id": 2}, {"id": 3}],
        )

        result = server.memory_delete(
            portal_uri="mem://test/delete",
            table="users",
            where={"id": 2},
        )

        assert result["success"] is True
        assert result["rows_deleted"] == 1

    def test_delete_all(self):
        """Test delete all rows."""
        server.memory_write(
            portal_uri="mem://test/delete_all",
            table="users",
            data=[{"id": 1}, {"id": 2}, {"id": 3}],
        )

        result = server.memory_delete(
            portal_uri="mem://test/delete_all",
            table="users",
            delete_all=True,
        )

        assert result["success"] is True
        assert result["rows_deleted"] == 3

    def test_delete_no_condition(self):
        """Test delete without condition fails."""
        server.memory_write(
            portal_uri="mem://test/no_cond",
            table="users",
            data=[{"id": 1}],
        )

        result = server.memory_delete(
            portal_uri="mem://test/no_cond",
            table="users",
        )

        assert result["success"] is False


class TestMemoryView:
    """Tests for memory_view tool."""

    def test_view_portal(self):
        """Test viewing portal info."""
        server.memory_write(
            portal_uri="mem://test/view",
            table="users",
            data=[{"id": 1}, {"id": 2}],
        )

        result = server.memory_view(portal_uri="mem://test/view")

        assert result["success"] is True
        assert result["uri"] == "mem://test/view"
        assert "users" in result["schema"]
        assert result["stats"]["total_rows"] == 2

    def test_view_invalid_uri(self):
        """Test view with invalid URI."""
        result = server.memory_view(portal_uri="invalid://uri")

        assert result["success"] is False


class TestMemoryListTables:
    """Tests for memory_list_tables tool."""

    def test_list_tables(self):
        """Test listing tables."""
        server.memory_write(
            portal_uri="mem://test/list",
            table="table1",
            data=[{"a": 1}],
        )
        server.memory_write(
            portal_uri="mem://test/list",
            table="table2",
            data=[{"b": 2}],
        )

        result = server.memory_list_tables(portal_uri="mem://test/list")

        assert result["success"] is True
        assert "table1" in result["tables"]
        assert "table2" in result["tables"]


class TestMemoryDropTable:
    """Tests for memory_drop_table tool."""

    def test_drop_table(self):
        """Test dropping a table."""
        server.memory_write(
            portal_uri="mem://test/drop",
            table="to_drop",
            data=[{"id": 1}],
        )

        result = server.memory_drop_table(
            portal_uri="mem://test/drop",
            table="to_drop",
        )

        assert result["success"] is True
        assert result["table_dropped"] == "to_drop"

        list_result = server.memory_list_tables(portal_uri="mem://test/drop")
        assert "to_drop" not in list_result["tables"]


class TestMemoryListPortals:
    """Tests for memory_list_portals tool."""

    def test_list_portals(self):
        """Test listing portals."""
        server.memory_write(
            portal_uri="mem://ns1/portal1",
            table="t",
            data=[{"x": 1}],
        )
        server.memory_write(
            portal_uri="mem://ns2/portal2",
            table="t",
            data=[{"x": 2}],
        )

        result = server.memory_list_portals()

        assert result["success"] is True
        assert result["count"] >= 2

        uris = [p["uri"] for p in result["portals"]]
        assert "mem://ns1/portal1" in uris
        assert "mem://ns2/portal2" in uris
