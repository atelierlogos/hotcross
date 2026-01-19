"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from src.core.portal import MemoryPortal
from src.core.registry import PortalRegistry


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def portal(temp_dir):
    """Create a test portal."""
    db_path = temp_dir / "test.db"
    portal = MemoryPortal(
        namespace="test",
        portal_id="default",
        db_path=db_path,
        name="Test Portal",
        description="Portal for testing",
    )
    yield portal
    portal.close()


@pytest.fixture
def registry(temp_dir):
    """Create a test registry."""
    reg = PortalRegistry(base_path=temp_dir)
    yield reg
    reg.close_all()


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return [
        {"id": 1, "name": "Alice", "score": 95.5, "active": True},
        {"id": 2, "name": "Bob", "score": 87.0, "active": True},
        {"id": 3, "name": "Charlie", "score": 72.5, "active": False},
    ]
