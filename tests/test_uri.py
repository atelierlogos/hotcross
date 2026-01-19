"""Tests for URI parser."""

import pytest

from src.uri.parser import MemoryURI


class TestMemoryURI:
    """Tests for MemoryURI parsing and manipulation."""

    def test_parse_basic(self):
        """Test parsing a basic mem:// URI."""
        uri = MemoryURI.parse("mem://conversation/default")
        assert uri.namespace == "conversation"
        assert uri.portal_id == "default"
        assert uri.table is None
        assert uri.query_params is None

    def test_parse_with_table(self):
        """Test parsing URI with table."""
        uri = MemoryURI.parse("mem://conversation/default/messages")
        assert uri.namespace == "conversation"
        assert uri.portal_id == "default"
        assert uri.table == "messages"
        assert uri.query_params is None

    def test_parse_with_query(self):
        """Test parsing URI with query parameters."""
        uri = MemoryURI.parse("mem://conversation/default/messages?limit=10&offset=5")
        assert uri.namespace == "conversation"
        assert uri.portal_id == "default"
        assert uri.table == "messages"
        assert uri.query_params == {"limit": ["10"], "offset": ["5"]}

    def test_parse_invalid_empty(self):
        """Test parsing empty URI fails."""
        with pytest.raises(ValueError):
            MemoryURI.parse("")

    def test_parse_invalid_scheme(self):
        """Test parsing invalid scheme fails."""
        with pytest.raises(ValueError):
            MemoryURI.parse("http://conversation/default")

    def test_parse_invalid_format(self):
        """Test parsing invalid format fails."""
        with pytest.raises(ValueError):
            MemoryURI.parse("mem://")

        with pytest.raises(ValueError):
            MemoryURI.parse("mem://namespace")

    def test_portal_uri(self):
        """Test portal_uri property."""
        uri = MemoryURI.parse("mem://conversation/default/messages?limit=10")
        assert uri.portal_uri == "mem://conversation/default"

    def test_full_uri(self):
        """Test full_uri property."""
        uri = MemoryURI.parse("mem://conversation/default")
        assert uri.full_uri == "mem://conversation/default"

        uri = MemoryURI.parse("mem://conversation/default/messages")
        assert uri.full_uri == "mem://conversation/default/messages"

    def test_with_table(self):
        """Test creating URI with different table."""
        uri = MemoryURI.parse("mem://conversation/default")
        new_uri = uri.with_table("events")
        assert new_uri.table == "events"
        assert new_uri.namespace == uri.namespace
        assert new_uri.portal_id == uri.portal_id

    def test_with_query(self):
        """Test creating URI with query parameters."""
        uri = MemoryURI.parse("mem://conversation/default/messages")
        new_uri = uri.with_query(limit=10, offset=5)
        assert new_uri.get_param("limit") == "10"
        assert new_uri.get_param("offset") == "5"

    def test_get_param(self):
        """Test getting query parameters."""
        uri = MemoryURI.parse("mem://conversation/default?limit=10")
        assert uri.get_param("limit") == "10"
        assert uri.get_param("missing") is None
        assert uri.get_param("missing", "default") == "default"

    def test_str(self):
        """Test string representation."""
        uri = MemoryURI.parse("mem://conversation/default/messages")
        assert str(uri) == "mem://conversation/default/messages"

    def test_repr(self):
        """Test repr representation."""
        uri = MemoryURI.parse("mem://conversation/default")
        assert "MemoryURI" in repr(uri)
        assert "conversation" in repr(uri)
        assert "default" in repr(uri)
