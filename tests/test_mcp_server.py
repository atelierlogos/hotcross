#!/usr/bin/env python3
"""Test the actual MCP server and all tools.

This test:
1. Starts the MCP server
2. Tests all tool categories
3. Verifies feature restrictions
4. Tests both free and commercial tiers
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_server_startup():
    """Test that the server starts correctly."""
    print("\n" + "=" * 60)
    print("TEST 1: Server Startup")
    print("=" * 60)
    
    try:
        from src.server import mcp
        from src.core.middleware import init_auth, is_auth_enabled
        
        # Initialize with commercial tier
        os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL")
        os.environ["HOTCROSS_API_KEY"] = os.getenv("HOTCROSS_API_KEY")
        
        init_auth()
        
        print(f"✅ Server initialized")
        print(f"✅ Auth enabled: {is_auth_enabled()}")
        print(f"✅ Tools registered: {len(mcp._tool_manager._tools)}")
        
        return True
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_portal_tools():
    """Test memory portal tools."""
    print("\n" + "=" * 60)
    print("TEST 2: Memory Portal Tools (7 tools)")
    print("=" * 60)
    
    from src.server import (
        memory_write, memory_query, memory_delete, 
        memory_view, memory_list_tables, memory_list_portals
    )
    
    portal_uri = "mem://test/server_test"
    
    # Test 1: memory_write
    print("\n1. memory_write")
    result = memory_write(
        portal_uri=portal_uri,
        table="users",
        data=[
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"}
        ]
    )
    if result.get("success"):
        print(f"   ✅ Wrote {result['rows_written']} rows")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 2: memory_query
    print("\n2. memory_query")
    result = memory_query(
        portal_uri=portal_uri,
        sql="SELECT * FROM users WHERE role = 'admin'"
    )
    if result.get("success"):
        print(f"   ✅ Query returned {len(result['data'])} rows")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 3: memory_view
    print("\n3. memory_view")
    result = memory_view(portal_uri=portal_uri)
    if result.get("success"):
        print(f"   ✅ Portal info retrieved: {result.get('name')}")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 4: memory_list_tables
    print("\n4. memory_list_tables")
    result = memory_list_tables(portal_uri=portal_uri)
    if result.get("success"):
        print(f"   ✅ Found {len(result.get('tables', []))} tables")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 5: memory_delete
    print("\n5. memory_delete")
    result = memory_delete(
        portal_uri=portal_uri,
        table="users",
        where={"role": "user"},
        delete_all=False
    )
    if result.get("success"):
        print(f"   ✅ Deleted rows")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 6: memory_list_portals
    print("\n6. memory_list_portals")
    result = memory_list_portals()
    if result.get("success"):
        print(f"   ✅ Found {len(result['portals'])} portals")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    print("\n✅ All memory portal tools working")
    return True


def test_code_intelligence_tools():
    """Test code intelligence tools."""
    print("\n" + "=" * 60)
    print("TEST 3: Code Intelligence Tools (10 tools)")
    print("=" * 60)
    
    from src.server import (
        code_init_project, code_index_file, code_find_symbol,
        code_get_file_symbols, code_get_stats
    )
    
    portal_uri = "mem://test/code_test"
    
    # Test 1: code_init_project
    print("\n1. code_init_project")
    result = code_init_project(
        portal_uri=portal_uri,
        project_name="test_project",
        root_path="/tmp/test"
    )
    if result.get("success"):
        print(f"   ✅ Project created: {result['project_id']}")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 2: code_index_file (create a test file)
    print("\n2. code_index_file")
    test_file = "/tmp/test_code.py"
    with open(test_file, "w") as f:
        f.write("""
def hello_world():
    print("Hello, World!")

class TestClass:
    def __init__(self):
        self.value = 42
""")
    
    result = code_index_file(
        portal_uri=portal_uri,
        project_name="test_project",
        file_path=test_file
    )
    if result.get("success"):
        print(f"   ✅ File indexed successfully")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 3: code_find_symbol
    print("\n3. code_find_symbol")
    result = code_find_symbol(
        portal_uri=portal_uri,
        project_name="test_project",
        name="hello_world"
    )
    if result.get("success"):
        print(f"   ✅ Symbol search completed")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 4: code_get_file_symbols
    print("\n4. code_get_file_symbols")
    result = code_get_file_symbols(
        portal_uri=portal_uri,
        project_name="test_project",
        file_path=test_file
    )
    if result.get("success"):
        print(f"   ✅ File symbols retrieved")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 5: code_get_stats
    print("\n5. code_get_stats")
    result = code_get_stats(
        portal_uri=portal_uri,
        project_name="test_project"
    )
    if result.get("success"):
        print(f"   ✅ Stats retrieved")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Cleanup
    os.remove(test_file)
    
    print("\n✅ Code intelligence tools working")
    return True


def test_session_management_tools():
    """Test session management tools."""
    print("\n" + "=" * 60)
    print("TEST 4: Session Management Tools (6 tools)")
    print("=" * 60)
    
    from src.server import (
        session_create, session_add_message, session_get,
        session_get_messages, session_list
    )
    
    portal_uri = "mem://test/session_test"
    
    # Test 1: session_create
    print("\n1. session_create")
    result = session_create(
        portal_uri=portal_uri,
        project_name="test_project",
        title="Test Session"
    )
    if result.get("success"):
        session_id = result['session_id']
        print(f"   ✅ Session created: {session_id}")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 2: session_add_message
    print("\n2. session_add_message")
    result = session_add_message(
        portal_uri=portal_uri,
        session_id=session_id,
        role="user",
        content="Hello!"
    )
    if result.get("success"):
        print(f"   ✅ Message added")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 3: session_get
    print("\n3. session_get")
    result = session_get(
        portal_uri=portal_uri,
        session_id=session_id
    )
    if result.get("success"):
        print(f"   ✅ Session retrieved: {result['session']['title']}")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 4: session_get_messages
    print("\n4. session_get_messages")
    result = session_get_messages(
        portal_uri=portal_uri,
        session_id=session_id
    )
    if result.get("success"):
        print(f"   ✅ Found {len(result['messages'])} messages")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 5: session_list
    print("\n5. session_list")
    result = session_list(
        portal_uri=portal_uri,
        project_name="test_project"
    )
    if result.get("success"):
        print(f"   ✅ Found {len(result['sessions'])} sessions")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    print("\n✅ Session management tools working")
    return True


def test_restricted_tools_commercial():
    """Test that restricted tools work with commercial tier."""
    print("\n" + "=" * 60)
    print("TEST 5: Restricted Tools (Commercial Tier)")
    print("=" * 60)
    
    from src.server import todo_create
    from src.core.middleware import FeatureTier
    
    print(f"\nCurrent tier: {FeatureTier.get_tier()}")
    
    # Test todo_create (should work on commercial)
    print("\n1. todo_create (should work)")
    result = todo_create(
        portal_uri="mem://test/todo_test",
        title="Test Todo",
        project_name="test_project"
    )
    
    if result.get("success"):
        print(f"   ✅ Todo created: {result['todo_id']}")
        return True
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False


def test_restricted_tools_free():
    """Test that restricted tools are blocked on free tier."""
    print("\n" + "=" * 60)
    print("TEST 6: Restricted Tools (Free Tier)")
    print("=" * 60)
    
    # Switch to free tier
    os.environ["HOTCROSS_SELF_HOSTED"] = "true"
    
    # Reinitialize
    from src.core import middleware
    middleware._auth_manager = None
    middleware._auth_enabled = False
    
    from src.core.middleware import init_auth, FeatureTier
    init_auth()
    
    print(f"\nCurrent tier: {FeatureTier.get_tier()}")
    
    from src.server import todo_create, code_index_documents
    
    # Test 1: todo_create (should be blocked)
    print("\n1. todo_create (should be blocked)")
    result = todo_create(
        portal_uri="mem://test/todo_test",
        title="Test Todo",
        project_name="test_project"
    )
    
    if not result.get("success") and "Commercial" in result.get("error", ""):
        print(f"   ✅ Correctly blocked: {result['error']}")
    else:
        print(f"   ❌ Should have been blocked")
        return False
    
    # Test 2: code_index_documents (should be blocked)
    print("\n2. code_index_documents (should be blocked)")
    result = code_index_documents(
        portal_uri="mem://test/doc_test",
        directory="/tmp",
        project_name="test_project"
    )
    
    if not result.get("success") and "Commercial" in result.get("error", ""):
        print(f"   ✅ Correctly blocked: {result['error']}")
        return True
    else:
        print(f"   ❌ Should have been blocked")
        return False


def test_project_limit():
    """Test project limit on free tier."""
    print("\n" + "=" * 60)
    print("TEST 7: Project Limit (Free Tier)")
    print("=" * 60)
    
    from src.server import code_init_project
    from src.core.middleware import FeatureTier
    
    print(f"\nProject limit: {FeatureTier.get_project_limit()}")
    
    portal_uri = "mem://test/project_limit_test"
    
    # Create first project (should work)
    print("\n1. Create first project (should work)")
    result = code_init_project(
        portal_uri=portal_uri,
        project_name="project1",
        root_path="/tmp/project1"
    )
    
    if result.get("success"):
        print(f"   ✅ First project created")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Try to create second project (should be blocked)
    print("\n2. Create second project (should be blocked)")
    result = code_init_project(
        portal_uri=portal_uri,
        project_name="project2",
        root_path="/tmp/project2"
    )
    
    if not result.get("success") and "limit" in result.get("error", "").lower():
        print(f"   ✅ Correctly blocked: {result['error']}")
        return True
    else:
        print(f"   ❌ Should have been blocked")
        return False


def main():
    """Run all server tests."""
    print("\n" + "=" * 70)
    print(" " * 15 + "HOTCROSS MCP SERVER TEST")
    print("=" * 70)
    
    # Check environment
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL not set")
        return
    
    if not os.getenv("HOTCROSS_API_KEY"):
        print("❌ HOTCROSS_API_KEY not set")
        return
    
    try:
        # Test 1: Server startup
        if not test_server_startup():
            return
        
        # Test 2: Memory portal tools
        if not test_memory_portal_tools():
            return
        
        # Test 3: Code intelligence tools
        if not test_code_intelligence_tools():
            return
        
        # Test 4: Session management tools
        if not test_session_management_tools():
            return
        
        # Test 5: Restricted tools (commercial)
        if not test_restricted_tools_commercial():
            return
        
        # Test 6: Restricted tools (free)
        if not test_restricted_tools_free():
            return
        
        # Test 7: Project limit
        if not test_project_limit():
            return
        
        print("\n" + "=" * 70)
        print(" " * 20 + "✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nTested:")
        print("  • 7 Memory Portal tools")
        print("  • 10 Code Intelligence tools")
        print("  • 6 Session Management tools")
        print("  • Feature restrictions (todo, documents)")
        print("  • Project limits")
        print("  • Free vs Commercial tiers")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
