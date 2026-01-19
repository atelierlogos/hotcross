"""Tests for MemoryPortal."""

import pytest

from src.core.portal import MemoryPortal


class TestMemoryPortal:
    """Tests for MemoryPortal operations."""

    def test_create_portal(self, portal):
        """Test portal creation."""
        assert portal.namespace == "test"
        assert portal.portal_id == "default"
        assert portal.name == "Test Portal"
        assert portal.uri == "mem://test/default"

    def test_write_and_query(self, portal, sample_data):
        """Test writing and querying data."""
        result = portal.write("users", sample_data)
        assert result.rows_written == 3
        assert result.table == "users"

        query_result = portal.query("SELECT * FROM users ORDER BY id")
        assert query_result.row_count == 3
        assert query_result.data[0]["name"] == "Alice"

    def test_auto_create_table(self, portal, sample_data):
        """Test automatic table creation."""
        portal.write("auto_table", sample_data)

        tables = portal.get_tables()
        assert "auto_table" in tables

    def test_write_empty_data(self, portal):
        """Test writing empty data."""
        result = portal.write("empty_table", [])
        assert result.rows_written == 0

    def test_delete_with_where(self, portal, sample_data):
        """Test deleting data with conditions."""
        portal.write("users", sample_data)

        result = portal.delete("users", where={"id": 2})
        assert result.rows_deleted == 1

        query_result = portal.query("SELECT COUNT(*) as cnt FROM users")
        assert query_result.data[0]["cnt"] == 2

    def test_delete_all(self, portal, sample_data):
        """Test deleting all data."""
        portal.write("users", sample_data)

        result = portal.delete("users", delete_all=True)
        assert result.rows_deleted == 3

        query_result = portal.query("SELECT COUNT(*) as cnt FROM users")
        assert query_result.data[0]["cnt"] == 0

    def test_delete_requires_condition(self, portal, sample_data):
        """Test that delete requires condition or delete_all."""
        portal.write("users", sample_data)

        with pytest.raises(ValueError):
            portal.delete("users")

    def test_delete_nonexistent_table(self, portal):
        """Test deleting from nonexistent table fails."""
        with pytest.raises(ValueError):
            portal.delete("nonexistent", delete_all=True)

    def test_drop_table(self, portal, sample_data):
        """Test dropping a table."""
        portal.write("users", sample_data)
        assert "users" in portal.get_tables()

        portal.drop_table("users")
        assert "users" not in portal.get_tables()

    def test_get_tables(self, portal, sample_data):
        """Test listing tables."""
        portal.write("table1", [{"a": 1}])
        portal.write("table2", [{"b": 2}])

        tables = portal.get_tables()
        assert "table1" in tables
        assert "table2" in tables
        assert "_mcp_metadata" not in tables

    def test_get_table_schema(self, portal, sample_data):
        """Test getting table schema."""
        portal.write("users", sample_data)

        schema = portal.get_table_schema("users")
        assert schema.name == "users"
        assert len(schema.columns) > 0

        col_names = [c.name for c in schema.columns]
        assert "id" in col_names
        assert "name" in col_names
        assert "score" in col_names

    def test_get_stats(self, portal, sample_data):
        """Test getting portal statistics."""
        portal.write("users", sample_data)
        portal.write("events", [{"event": "test"}])

        stats = portal.get_stats()
        assert stats.total_rows == 4
        assert stats.total_tables == 2
        assert stats.table_stats["users"] == 3
        assert stats.table_stats["events"] == 1

    def test_get_info(self, portal, sample_data):
        """Test getting full portal info."""
        portal.write("users", sample_data)

        info = portal.get_info()
        assert info.uri == "mem://test/default"
        assert info.name == "Test Portal"
        assert "users" in info.tables_schema
        assert info.stats.total_rows == 3

    def test_metadata(self, portal):
        """Test metadata operations."""
        portal.set_metadata("custom.key", "custom_value")
        assert portal.get_metadata("custom.key") == "custom_value"
        assert portal.get_metadata("missing") is None
        assert portal.get_metadata("missing", "default") == "default"

    def test_type_inference(self, portal):
        """Test type inference from data."""
        data = [
            {
                "int_col": 42,
                "float_col": 3.14,
                "str_col": "hello",
                "bool_col": True,
                "list_col": [1, 2, 3],
            }
        ]
        portal.write("typed", data)

        schema = portal.get_table_schema("typed")
        col_types = {c.name: c.type for c in schema.columns}

        assert "Int64" in col_types["int_col"]
        assert "Float64" in col_types["float_col"]
        assert "String" in col_types["str_col"]

    def test_context_manager(self, temp_dir):
        """Test portal as context manager."""
        db_path = temp_dir / "context.db"

        with MemoryPortal("test", "context", db_path) as portal:
            portal.write("data", [{"x": 1}])
            result = portal.query("SELECT * FROM data")
            assert len(result.data) == 1
