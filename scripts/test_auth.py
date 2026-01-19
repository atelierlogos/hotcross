#!/usr/bin/env python3
"""Test script to verify authentication is working."""

import os
from src import server

# This will use the API key from environment
api_key = os.getenv("HOTCROSS_API_KEY")

if not api_key:
    print("❌ HOTCROSS_API_KEY environment variable not set!")
    print("   Set it with: export HOTCROSS_API_KEY='mp_live_...'")
    exit(1)

print(f"🔑 Testing with API key: {api_key[:15]}...")

# Test a simple write operation
result = server.memory_write(
    portal_uri="mem://test/auth-test",
    table="test_table",
    data=[{"id": 1, "message": "Auth test"}]
)

if result.get("success"):
    print("✅ Authentication successful!")
    print(f"   Wrote {result['rows_written']} row(s)")
    print(f"   Portal: {result['portal_uri']}")
else:
    print("❌ Authentication failed!")
    print(f"   Error: {result.get('error')}")
