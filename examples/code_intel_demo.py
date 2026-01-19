"""Demo of code intelligence features."""

from pathlib import Path

from src.core.portal import MemoryPortal
from src.intel.indexer import CodeIndexer
from src.intel.graph import CodeGraph


def main():
    """Run code intelligence demo."""
    # Create a portal for code intelligence
    portal = MemoryPortal(
        namespace="code",
        portal_id="memory-portals",
        db_path="~/.memory-portals/code/memory-portals.db",
        name="Memory Portals Code Intelligence",
        description="Code intelligence index for the memory-portals project",
    )

    print("🔍 Memory Portals Code Intelligence Demo\n")

    # Index the memory_portals directory
    print("📚 Indexing memory_portals directory...")
    indexer = CodeIndexer(portal)
    stats = indexer.index_directory("memory_portals", recursive=True)

    print(f"\n✅ Indexing complete!")
    print(f"   Files indexed: {stats.files_indexed}")
    print(f"   Files skipped: {stats.files_skipped}")
    print(f"   Symbols extracted: {stats.symbols_extracted}")
    print(f"   Types extracted: {stats.types_extracted}")
    print(f"   Imports extracted: {stats.imports_extracted}")
    print(f"   Duration: {stats.total_duration_ms:.1f}ms")

    # Get statistics
    graph = CodeGraph(portal)
    index_stats = graph.get_stats()

    print(f"\n📊 Index Statistics:")
    print(f"   Total files: {index_stats['total_files']}")
    print(f"   Total symbols: {index_stats['total_symbols']}")
    print(f"   Total imports: {index_stats['total_imports']}")
    print(f"   Languages: {', '.join(index_stats['languages'].keys())}")

    # Find symbols
    print(f"\n🔎 Finding 'MemoryPortal' class...")
    results = graph.find_symbols(name="MemoryPortal", kind="class")
    if results:
        for result in results:
            print(f"   Found in: {result['file_path']}")
            print(f"   Line: {result['start_line']}")
            if result.get('docstring'):
                print(f"   Doc: {result['docstring'][:60]}...")

    # Get file symbols
    print(f"\n📄 Symbols in memory_portals/core/portal.py:")
    file_symbols = graph.get_file_symbols("memory_portals/core/portal.py")
    for symbol in file_symbols[:5]:  # Show first 5
        print(f"   {symbol['kind']:10} {symbol['name']:30} (line {symbol['start_line']})")

    # Get imports
    print(f"\n📦 Imports in memory_portals/server.py:")
    imports = graph.get_file_imports("memory_portals/server.py")
    for imp in imports[:5]:  # Show first 5
        print(f"   {imp['import_kind']:12} {imp['module_path']}")

    # Find references
    print(f"\n🔗 References to 'MemoryPortal':")
    refs = graph.find_references("MemoryPortal")
    print(f"   Found {len(refs)} references across {len(set(r['file_path'] for r in refs))} files")

    portal.close()
    print(f"\n✨ Demo complete!")


if __name__ == "__main__":
    main()
