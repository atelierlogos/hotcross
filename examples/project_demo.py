"""Demo of code intelligence project management."""

import tempfile
from pathlib import Path

from src.core.portal import MemoryPortal
from src.intel.graph import CodeGraph
from src.intel.indexer import CodeIndexer


def create_sample_projects(tmpdir: Path):
    """Create sample project directories."""
    
    # Project 1: Backend API
    backend = tmpdir / "backend"
    backend.mkdir()
    (backend / "api.py").write_text("""
class UserAPI:
    def get_user(self, user_id: int):
        return {"id": user_id, "name": "John"}
    
    async def create_user(self, data: dict):
        return await self.save(data)
""")
    (backend / "models.py").write_text("""
class User:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
""")
    
    # Project 2: Frontend App
    frontend = tmpdir / "frontend"
    frontend.mkdir()
    (frontend / "app.js").write_text("""
class App {
    constructor() {
        this.users = [];
    }
    
    async fetchUsers() {
        const response = await fetch('/api/users');
        this.users = await response.json();
    }
}

export default App;
""")
    (frontend / "utils.ts").write_text("""
interface Config {
    apiUrl: string;
    timeout: number;
}

export function getConfig(): Config {
    return {
        apiUrl: 'http://localhost:3000',
        timeout: 5000
    };
}
""")
    
    return backend, frontend


def main():
    """Run project management demo."""
    print("🗂️  Code Intelligence Project Management Demo\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        backend_dir, frontend_dir = create_sample_projects(tmpdir_path)
        
        # Create portal
        portal = MemoryPortal(
            namespace="demo",
            portal_id="projects",
            db_path=tmpdir_path / "projects.db",
        )
        
        graph = CodeGraph(portal)
        
        # Create Project 1: Backend
        print("📦 Creating Backend Project...")
        backend_id = graph.create_project(
            project_name="backend-api",
            root_path=str(backend_dir),
            description="Backend API service",
            version="1.0.0",
            git_branch="main",
        )
        print(f"   Created project: backend-api (ID: {backend_id[:8]}...)")
        
        # Create Project 2: Frontend
        print("\n📦 Creating Frontend Project...")
        frontend_id = graph.create_project(
            project_name="frontend-app",
            root_path=str(frontend_dir),
            description="Frontend web application",
            version="2.0.0",
            git_branch="develop",
        )
        print(f"   Created project: frontend-app (ID: {frontend_id[:8]}...)")
        
        # Index Backend Project
        print("\n🔍 Indexing Backend Project...")
        backend_indexer = CodeIndexer(portal, project_id=backend_id)
        backend_stats = backend_indexer.index_directory(backend_dir, recursive=False)
        print(f"   Files: {backend_stats.files_indexed}")
        print(f"   Symbols: {backend_stats.symbols_extracted}")
        
        # Index Frontend Project
        print("\n🔍 Indexing Frontend Project...")
        frontend_indexer = CodeIndexer(portal, project_id=frontend_id)
        frontend_stats = frontend_indexer.index_directory(frontend_dir, recursive=False)
        print(f"   Files: {frontend_stats.files_indexed}")
        print(f"   Symbols: {frontend_stats.symbols_extracted}")
        print(f"   Types: {frontend_stats.types_extracted}")
        
        # List all projects
        print("\n📋 All Projects:")
        projects = graph.list_projects()
        for proj in projects:
            print(f"   • {proj['project_name']:20} v{proj.get('version', 'N/A'):6} ({proj['root_path']})")
        
        # Query symbols by project
        print("\n🔎 Symbols by Project:\n")
        
        print("   Backend API:")
        backend_symbols = portal.query(
            f"SELECT name, kind FROM _ci_symbols WHERE project_id = '{backend_id}' ORDER BY name"
        )
        for row in backend_symbols.data:
            print(f"      {row['kind']:10} {row['name']}")
        
        print("\n   Frontend App:")
        frontend_symbols = portal.query(
            f"SELECT name, kind FROM _ci_symbols WHERE project_id = '{frontend_id}' ORDER BY name"
        )
        for row in frontend_symbols.data:
            print(f"      {row['kind']:10} {row['name']}")
        
        # Get TypeScript types from frontend project
        print("\n📐 TypeScript Types (Frontend):")
        types = portal.query(
            f"SELECT name, kind FROM _ci_types WHERE project_id = '{frontend_id}'"
        )
        for row in types.data:
            print(f"   {row['kind']:10} {row['name']}")
        
        # Cross-project query: All async functions
        print("\n⚡ Async Functions Across All Projects:")
        async_funcs = portal.query(
            """
            SELECT p.project_name, s.name, s.kind
            FROM _ci_symbols s
            JOIN _ci_projects p ON s.project_id = p.project_id
            WHERE s.is_async = 1
            ORDER BY p.project_name, s.name
            """
        )
        for row in async_funcs.data:
            print(f"   {row['project_name']:20} {row['kind']:10} {row['name']}")
        
        # Update project version
        print("\n🔄 Updating Backend Project Version...")
        graph.update_project(backend_id, version="1.1.0", git_commit="abc123")
        updated = graph.get_project_by_id(backend_id)
        print(f"   New version: {updated['version']}")
        print(f"   Git commit: {updated['git_commit']}")
        
        # Project statistics
        print("\n📊 Project Statistics:")
        for proj in projects:
            proj_id = proj['project_id']
            file_count = portal._db.query_value(
                f"SELECT count() FROM _ci_files WHERE project_id = '{proj_id}'"
            )
            symbol_count = portal._db.query_value(
                f"SELECT count() FROM _ci_symbols WHERE project_id = '{proj_id}'"
            )
            print(f"   {proj['project_name']:20} {file_count} files, {symbol_count} symbols")
        
        portal.close()
    
    print("\n✨ Project management demo complete!")


if __name__ == "__main__":
    main()
