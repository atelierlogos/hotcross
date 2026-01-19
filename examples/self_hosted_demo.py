#!/usr/bin/env python3
"""Demo of self-hosted mode (no authentication required).

This example shows how to use Hotcross in self-hosted mode for personal use.
"""

import os

# Enable self-hosted mode
os.environ["HOTCROSS_SELF_HOSTED"] = "true"

from src.core.middleware import init_auth, is_auth_enabled
from src.core.registry import PortalRegistry
from src.uri.parser import MemoryURI

# Initialize (no DATABASE_URL or API key needed!)
init_auth()

print(f"🏠 Self-hosted mode: {not is_auth_enabled()}")
print()

# Create a portal and write some data
registry = PortalRegistry()

# Write conversation data
portal_uri = "mem://conversation/demo"
uri = MemoryURI.parse(portal_uri)
portal = registry.resolve(uri)

messages = [
    {"role": "user", "content": "Hello!", "timestamp": "2024-01-01T10:00:00"},
    {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T10:00:01"},
]

result = portal.write("messages", messages)
print(f"✅ Wrote {result.rows_written} messages to {result.portal_uri}/{result.table}")

# Query the data
query_result = portal.query("SELECT * FROM messages ORDER BY timestamp")
print(f"\n📊 Query results:")
for row in query_result.data:
    print(f"   {row['role']}: {row['content']}")

print("\n💡 This works without any API key or database connection!")
print("   For commercial use, please obtain an API key.")
