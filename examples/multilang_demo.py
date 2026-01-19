"""Demo of multi-language code intelligence."""

import tempfile
from pathlib import Path

from src.core.portal import MemoryPortal
from src.intel.indexer import CodeIndexer
from src.intel.graph import CodeGraph


def create_sample_files(tmpdir: Path):
    """Create sample files in different languages."""
    
    # Python file
    (tmpdir / "calculator.py").write_text("""
class Calculator:
    '''A simple calculator.'''
    
    def add(self, a: int, b: int) -> int:
        return a + b
    
    async def fetch_result(self):
        return await self.add(1, 2)
""")
    
    # JavaScript file
    (tmpdir / "utils.js").write_text("""
export class Logger {
    constructor(name) {
        this.name = name;
    }
    
    log(message) {
        console.log(`[${this.name}] ${message}`);
    }
    
    async logAsync(message) {
        await this.log(message);
    }
}

export function formatDate(date) {
    return date.toISOString();
}
""")
    
    # TypeScript file
    (tmpdir / "types.ts").write_text("""
interface User {
    id: number;
    name: string;
    email: string;
}

type UserId = string | number;

class UserService {
    private users: Map<UserId, User> = new Map();
    
    async getUser(id: UserId): Promise<User | null> {
        return this.users.get(id) || null;
    }
    
    addUser(user: User): void {
        this.users.set(user.id, user);
    }
}

export { User, UserService };
export type { UserId };
""")


def main():
    """Run multi-language demo."""
    print("🌍 Multi-Language Code Intelligence Demo\n")
    
    # Create temporary directory with sample files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        create_sample_files(tmpdir_path)
        
        print("📝 Created sample files:")
        print("   - calculator.py (Python)")
        print("   - utils.js (JavaScript)")
        print("   - types.ts (TypeScript)")
        print()
        
        # Create portal and index
        portal = MemoryPortal(
            namespace="demo",
            portal_id="multilang",
            db_path=tmpdir_path / "multilang.db",
        )
        
        print("🔍 Indexing files...")
        indexer = CodeIndexer(portal)
        stats = indexer.index_directory(tmpdir_path, recursive=False)
        
        print(f"\n✅ Indexing complete!")
        print(f"   Files indexed: {stats.files_indexed}")
        print(f"   Symbols extracted: {stats.symbols_extracted}")
        print(f"   Types extracted: {stats.types_extracted}")
        print(f"   Imports extracted: {stats.imports_extracted}")
        print(f"   Exports extracted: {stats.exports_extracted}")
        
        # Get statistics by language
        graph = CodeGraph(portal)
        index_stats = graph.get_stats()
        
        print(f"\n📊 Statistics by Language:")
        for lang, count in index_stats['languages'].items():
            print(f"   {lang:12} {count} files")
        
        # Show symbols from each language
        print(f"\n🔎 Symbols by File:\n")
        
        for file in ["calculator.py", "utils.js", "types.ts"]:
            file_path = str(tmpdir_path / file)
            symbols = graph.get_file_symbols(file_path)
            
            print(f"   {file}:")
            for symbol in symbols:
                async_marker = " (async)" if symbol.get('is_async') else ""
                print(f"      {symbol['kind']:10} {symbol['name']}{async_marker}")
            print()
        
        # Show TypeScript types
        print(f"📐 TypeScript Types:\n")
        types_file = str(tmpdir_path / "types.ts")
        result = portal.query(f"SELECT name, kind FROM _ci_types WHERE file_path = '{types_file}'")
        for row in result.data:
            print(f"   {row['kind']:10} {row['name']}")
        
        # Show async functions across all languages
        print(f"\n⚡ Async Functions Across All Languages:")
        async_symbols = portal.query(
            "SELECT file_path, name, kind FROM _ci_symbols WHERE is_async = 1"
        )
        for row in async_symbols.data:
            filename = Path(row['file_path']).name
            print(f"   {filename:20} {row['kind']:10} {row['name']}")
        
        portal.close()
    
    print(f"\n✨ Multi-language demo complete!")


if __name__ == "__main__":
    main()
