"""Demo of documentation indexing and search."""

import tempfile
from pathlib import Path

from src.core.portal import MemoryPortal
from src.intel.graph import CodeGraph
from src.intel.indexer import CodeIndexer


def create_sample_docs(tmpdir: Path):
    """Create sample documentation files."""
    
    # README
    (tmpdir / "README.md").write_text("""# My Awesome Project

A revolutionary code intelligence system with documentation indexing.

## Features

- Multi-language code parsing
- Project management
- Documentation indexing
- Semantic search

## Getting Started

Install the package:

```bash
pip install my-awesome-project
```

## Usage

```python
from myproject import CodeAnalyzer

analyzer = CodeAnalyzer()
analyzer.index("src/")
```
""")
    
    # API Documentation
    docs_dir = tmpdir / "docs"
    docs_dir.mkdir()
    
    (docs_dir / "api.md").write_text("""# API Reference

## CodeAnalyzer

The main class for code analysis.

### Methods

#### `index(directory: str) -> Stats`

Index a directory of source code.

**Parameters:**
- `directory`: Path to the directory to index

**Returns:**
- `Stats`: Indexing statistics

#### `search(query: str) -> List[Result]`

Search indexed code.

**Parameters:**
- `query`: Search query string

**Returns:**
- `List[Result]`: List of matching results
""")
    
    (docs_dir / "guide.md").write_text("""# User Guide

## Introduction

This guide will help you get started with code intelligence.

## Basic Concepts

### Projects

A project represents a codebase with its own namespace.

### Symbols

Symbols are functions, classes, methods, and variables extracted from code.

### Documents

Documentation files provide context and usage information.

## Advanced Usage

### Multi-Project Workspaces

You can index multiple projects in a single portal:

```python
portal = MemoryPortal("workspace", "multi")
```

### Cross-Project Search

Search across all projects:

```python
results = graph.search_documents("authentication")
```
""")
    
    # Contributing guide
    (tmpdir / "CONTRIBUTING.md").write_text("""# Contributing Guide

Thank you for contributing!

## Development Setup

1. Clone the repository
2. Install dependencies: `pip install -e .[dev]`
3. Run tests: `pytest`

## Code Style

- Use type hints
- Follow PEP 8
- Write docstrings

## Pull Requests

- Create a feature branch
- Write tests
- Update documentation
""")
    
    # Changelog
    (tmpdir / "CHANGELOG.md").write_text("""# Changelog

## [1.1.0] - 2024-01-18

### Added
- Documentation indexing
- Semantic search
- Project management

### Fixed
- Performance improvements
- Bug fixes

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Code parsing
- Symbol extraction
""")


def main():
    """Run documentation indexing demo."""
    print("📚 Documentation Indexing & Search Demo\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        create_sample_docs(tmpdir_path)
        
        print("📝 Created sample documentation:")
        print("   - README.md")
        print("   - docs/api.md")
        print("   - docs/guide.md")
        print("   - CONTRIBUTING.md")
        print("   - CHANGELOG.md")
        print()
        
        # Create portal and project
        portal = MemoryPortal(
            namespace="demo",
            portal_id="docs",
            db_path=tmpdir_path / "docs.db",
        )
        
        graph = CodeGraph(portal)
        
        # Create project
        print("📦 Creating project...")
        project_id = graph.create_project(
            project_name="my-awesome-project",
            root_path=str(tmpdir_path),
            description="A revolutionary code intelligence system",
            version="1.1.0",
        )
        print(f"   Project ID: {project_id[:8]}...")
        
        # Index documents
        print("\n🔍 Indexing documentation...")
        indexer = CodeIndexer(portal, project_id=project_id)
        stats = indexer.index_documents(tmpdir_path, recursive=True)
        
        print(f"   Files indexed: {stats['files_indexed']}")
        print(f"   Total words: {stats['total_words']}")
        
        # List documents
        print("\n📋 Indexed Documents:")
        documents = graph.list_documents(project_id=project_id)
        for doc in documents:
            print(f"   • {doc['doc_type']:15} {doc['file_path']:40} ({doc['word_count']} words)")
        
        # Get specific document
        print("\n📄 README Content:")
        readme = graph.get_document(str(tmpdir_path / "README.md"), project_id=project_id)
        if readme:
            print(f"   Title: {readme['title']}")
            print(f"   Type: {readme['doc_type']}")
            print(f"   Words: {readme['word_count']}")
            print(f"   Format: {readme['format']}")
            print(f"\n   First 200 chars:")
            print(f"   {readme['content'][:200]}...")
        
        # Search documents
        print("\n🔎 Search: 'authentication'")
        results = graph.search_documents("authentication", project_id=project_id)
        print(f"   Found {len(results)} results:")
        for result in results:
            print(f"      {result['file_path']} ({result['word_count']} words)")
        
        print("\n🔎 Search: 'API'")
        results = graph.search_documents("API", project_id=project_id)
        print(f"   Found {len(results)} results:")
        for result in results:
            print(f"      {result['file_path']} - {result.get('title', 'No title')}")
        
        # Document types breakdown
        print("\n📊 Documents by Type:")
        type_counts = portal.query(
            f"""
            SELECT doc_type, COUNT(*) as count, SUM(word_count) as total_words
            FROM _ci_documents
            WHERE project_id = '{project_id}'
            GROUP BY doc_type
            ORDER BY count DESC
            """
        )
        for row in type_counts.data:
            print(f"   {row['doc_type']:15} {row['count']} files, {row['total_words']} words")
        
        # Cross-reference: Find docs mentioning code concepts
        print("\n🔗 Documentation Coverage:")
        concepts = ["CodeAnalyzer", "index", "search", "project"]
        for concept in concepts:
            results = graph.search_documents(concept, project_id=project_id)
            print(f"   '{concept}': mentioned in {len(results)} documents")
        
        portal.close()
    
    print("\n✨ Documentation demo complete!")


if __name__ == "__main__":
    main()
