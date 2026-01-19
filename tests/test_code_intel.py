"""Tests for code intelligence functionality."""

import tempfile
from pathlib import Path

import pytest

from src.core.portal import MemoryPortal
from src.intel.graph import CodeGraph
from src.intel.indexer import CodeIndexer
from src.intel.parser import CodeParser
from src.intel.rules.registry import RuleRegistry


@pytest.fixture
def temp_portal():
    """Create a temporary portal for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        portal = MemoryPortal("test", "code-intel", db_path)
        yield portal
        portal.close()


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return b'''
"""Sample module for testing."""

from typing import List, Optional
import os


class Calculator:
    """A simple calculator class."""

    def __init__(self, name: str):
        self.name = name

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Subtract two numbers."""
        return a - b


def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y


_private_var = 42
PUBLIC_CONSTANT = "hello"

__all__ = ["Calculator", "multiply", "PUBLIC_CONSTANT"]
'''


def test_parser_initialization():
    """Test that parser initializes correctly."""
    parser = CodeParser()
    assert parser is not None


def test_rule_registry():
    """Test that Python rules are registered."""
    rules = RuleRegistry.get_for_file("test.py")
    assert rules is not None
    assert rules.language == "python"

    # Test unsupported file
    rules = RuleRegistry.get_for_file("test.txt")
    assert rules is None


def test_code_graph_initialization(temp_portal):
    """Test that code graph initializes and creates tables."""
    graph = CodeGraph(temp_portal)
    graph.ensure_tables()

    # Check that tables were created
    tables = temp_portal.get_tables()
    assert "_ci_files" in tables
    assert "_ci_symbols" in tables
    assert "_ci_types" in tables
    assert "_ci_imports" in tables


def test_parse_python_code(sample_python_code):
    """Test parsing Python code."""
    parser = CodeParser()
    tree = parser.parse(sample_python_code, "python")

    assert tree is not None
    assert tree.root_node is not None


def test_extract_symbols(sample_python_code):
    """Test symbol extraction from Python code."""
    from src.intel.rules.python import PythonRules

    parser = CodeParser()
    tree = parser.parse(sample_python_code, "python")
    rules = PythonRules()

    symbols = list(rules.extract_symbols(tree, sample_python_code))

    # Should find Calculator class, __init__, add, subtract, and multiply
    assert len(symbols) >= 5

    # Check for Calculator class
    calculator = next((s for s in symbols if s.name == "Calculator"), None)
    assert calculator is not None
    assert calculator.kind == "class"

    # Check for multiply function
    multiply_func = next((s for s in symbols if s.name == "multiply"), None)
    assert multiply_func is not None
    assert multiply_func.kind == "function"


def test_extract_imports(sample_python_code):
    """Test import extraction from Python code."""
    from src.intel.rules.python import PythonRules

    parser = CodeParser()
    tree = parser.parse(sample_python_code, "python")
    rules = PythonRules()

    imports = list(rules.extract_imports(tree, sample_python_code))

    # Should find imports for typing and os
    assert len(imports) >= 2

    # Check for typing import
    typing_import = next((i for i in imports if "typing" in i.module_path), None)
    assert typing_import is not None
    assert typing_import.import_kind == "from_import"


def test_extract_exports(sample_python_code):
    """Test export extraction from Python code."""
    from src.intel.rules.python import PythonRules

    parser = CodeParser()
    tree = parser.parse(sample_python_code, "python")
    rules = PythonRules()

    exports = list(rules.extract_exports(tree, sample_python_code))

    # Should find __all__ exports
    assert len(exports) >= 3

    export_names = [e.exported_name for e in exports]
    assert "Calculator" in export_names
    assert "multiply" in export_names
    assert "PUBLIC_CONSTANT" in export_names


def test_index_file(temp_portal, sample_python_code):
    """Test indexing a Python file."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".py", delete=False) as f:
        f.write(sample_python_code)
        temp_file = Path(f.name)

    try:
        # Create a project first
        graph = CodeGraph(temp_portal)
        project_id = graph.create_project("test-project", str(temp_file.parent))
        
        indexer = CodeIndexer(temp_portal, project_id=project_id)
        result = indexer.index_file(temp_file)

        assert result["status"] == "indexed"
        assert result["symbols"] >= 5
        assert result["imports"] >= 2
        assert result["exports"] >= 3

        # Verify data was stored
        graph = CodeGraph(temp_portal)
        symbols = graph.get_file_symbols(str(temp_file))
        assert len(symbols) >= 5

    finally:
        temp_file.unlink()


def test_incremental_indexing(temp_portal, sample_python_code):
    """Test that unchanged files are skipped."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".py", delete=False) as f:
        f.write(sample_python_code)
        temp_file = Path(f.name)

    try:
        # Create a project first
        graph = CodeGraph(temp_portal)
        project_id = graph.create_project("test-project", str(temp_file.parent))
        
        indexer = CodeIndexer(temp_portal, project_id=project_id)

        # First index
        result1 = indexer.index_file(temp_file)
        assert result1["status"] == "indexed"

        # Second index without changes
        result2 = indexer.index_file(temp_file)
        assert result2["status"] == "skipped"
        assert result2["reason"] == "unchanged"

        # Force re-index
        result3 = indexer.index_file(temp_file, force=True)
        assert result3["status"] == "indexed"

    finally:
        temp_file.unlink()


def test_find_symbols(temp_portal, sample_python_code):
    """Test symbol search."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".py", delete=False) as f:
        f.write(sample_python_code)
        temp_file = Path(f.name)

    try:
        # Create a project first
        graph = CodeGraph(temp_portal)
        project_id = graph.create_project("test-project", str(temp_file.parent))
        
        indexer = CodeIndexer(temp_portal, project_id=project_id)
        indexer.index_file(temp_file)

        # Find by name
        results = graph.find_symbols(name="Calculator")
        assert len(results) >= 1
        assert results[0]["name"] == "Calculator"

        # Find by kind
        results = graph.find_symbols(kind="function")
        assert len(results) >= 1

        # Find by kind (class)
        results = graph.find_symbols(kind="class")
        assert len(results) >= 1
        assert results[0]["name"] == "Calculator"

    finally:
        temp_file.unlink()


def test_get_stats(temp_portal, sample_python_code):
    """Test getting index statistics."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".py", delete=False) as f:
        f.write(sample_python_code)
        temp_file = Path(f.name)

    try:
        # Create a project first
        graph = CodeGraph(temp_portal)
        project_id = graph.create_project("test-project", str(temp_file.parent))
        
        indexer = CodeIndexer(temp_portal, project_id=project_id)
        indexer.index_file(temp_file)
        stats = graph.get_stats()

        assert stats["total_files"] >= 1
        assert stats["total_symbols"] >= 5
        assert stats["total_imports"] >= 2
        assert "python" in stats["languages"]

    finally:
        temp_file.unlink()
