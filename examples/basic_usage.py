#!/usr/bin/env python3
"""Basic usage example for Memory Portals.

This example demonstrates how to use the Memory Portals library directly
without going through the MCP server interface.
"""

import tempfile
from pathlib import Path

from src.core.portal import MemoryPortal
from src.core.registry import PortalRegistry
from src.uri.parser import MemoryURI


def main():
    """Demonstrate basic Memory Portals usage."""

    # Create a temporary directory for our example
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        print("=" * 60)
        print("Memory Portals - Basic Usage Example")
        print("=" * 60)

        # 1. Create a portal directly
        print("\n1. Creating a portal directly...")
        portal = MemoryPortal(
            namespace="example",
            portal_id="conversations",
            db_path=base_path / "example" / "conversations.db",
            name="Conversation History",
            description="Stores conversation messages",
        )

        # 2. Write some data
        print("\n2. Writing conversation data...")
        messages = [
            {"id": 1, "role": "user", "content": "Hello, how are you?", "timestamp": "2024-01-15T10:00:00Z"},
            {"id": 2, "role": "assistant", "content": "I'm doing well, thank you!", "timestamp": "2024-01-15T10:00:05Z"},
            {"id": 3, "role": "user", "content": "What can you help me with?", "timestamp": "2024-01-15T10:00:10Z"},
            {"id": 4, "role": "assistant", "content": "I can help with many tasks!", "timestamp": "2024-01-15T10:00:15Z"},
        ]
        result = portal.write("messages", messages)
        print(f"   Wrote {result.rows_written} messages")

        # 3. Query the data
        print("\n3. Querying messages...")
        query_result = portal.query("SELECT * FROM messages ORDER BY id")
        print(f"   Found {query_result.row_count} messages:")
        for row in query_result.data:
            print(f"   - [{row['role']}] {row['content'][:40]}...")

        # 4. Query with filter
        print("\n4. Querying only user messages...")
        user_messages = portal.query("SELECT * FROM messages WHERE role = 'user'")
        print(f"   Found {user_messages.row_count} user messages")

        # 5. Get portal statistics
        print("\n5. Portal statistics...")
        stats = portal.get_stats()
        print(f"   Total tables: {stats.total_tables}")
        print(f"   Total rows: {stats.total_rows}")
        print(f"   Table stats: {stats.table_stats}")

        # 6. Get table schema
        print("\n6. Table schema...")
        schema = portal.get_table_schema("messages")
        print(f"   Table: {schema.name}")
        print("   Columns:")
        for col in schema.columns:
            print(f"   - {col.name}: {col.type}")

        # 7. Delete some data
        print("\n7. Deleting a message...")
        delete_result = portal.delete("messages", where={"id": 4})
        print(f"   Deleted {delete_result.rows_deleted} row(s)")

        # Verify deletion
        remaining = portal.query("SELECT COUNT(*) as cnt FROM messages")
        print(f"   Remaining messages: {remaining.data[0]['cnt']}")

        # 8. Using the registry
        print("\n8. Using the portal registry...")
        registry = PortalRegistry(base_path=base_path)

        # Register a new portal
        tool_outputs = registry.register(
            namespace="example",
            portal_id="tool_outputs",
            name="Tool Outputs",
            description="Stores outputs from various tools",
        )

        # Write some tool output data
        tool_outputs.write("search_results", [
            {"query": "python tutorials", "result_count": 1500, "top_result": "docs.python.org"},
            {"query": "mcp protocol", "result_count": 42, "top_result": "modelcontextprotocol.io"},
        ])

        # List all portals
        portals = registry.list_portals()
        print(f"   Registered portals: {len(portals)}")
        for p in portals:
            print(f"   - {p['uri']}: {p['name']}")

        # 9. URI parsing
        print("\n9. URI parsing...")
        uri = MemoryURI.parse("mem://example/conversations/messages?limit=10")
        print(f"   Namespace: {uri.namespace}")
        print(f"   Portal ID: {uri.portal_id}")
        print(f"   Table: {uri.table}")
        print(f"   Query params: {uri.query_params}")
        print(f"   Full URI: {uri.full_uri}")

        # 10. Resolve URI to portal
        print("\n10. Resolving URI to portal...")
        resolved = registry.resolve("mem://example/tool_outputs")
        print(f"   Resolved to: {resolved.name}")

        # Cleanup
        portal.close()
        registry.close_all()

        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    main()
