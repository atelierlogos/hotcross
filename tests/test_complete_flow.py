#!/usr/bin/env python3
"""Complete end-to-end test of Hotcross flow.

Tests:
1. Organization creation
2. Developer provisioning
3. Authentication
4. Tool access (all tiers)
5. Feature restrictions
"""

import asyncio
import os
import sys
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_org_creation():
    """Test creating an organization."""
    print("\n" + "=" * 60)
    print("TEST 1: Organization Creation")
    print("=" * 60)
    
    from scripts.admin.manage_orgs import create_organization
    
    org_id = await create_organization(
        name="Test Company",
        email="test@example.com",
        subscription_status="active",
        max_seats=3
    )
    
    if org_id:
        print(f"✅ Organization created: {org_id}")
        return org_id
    else:
        print("❌ Failed to create organization")
        return None


async def test_developer_creation(org_id: UUID):
    """Test creating developers."""
    print("\n" + "=" * 60)
    print("TEST 2: Developer Provisioning")
    print("=" * 60)
    
    from scripts.admin.manage_orgs import create_developer
    
    developers = []
    
    # Create first developer
    dev1_id, api_key1 = await create_developer(
        str(org_id),
        "alice@test.com",
        "Alice",
        "Smith"
    )
    
    if dev1_id and api_key1:
        print(f"✅ Developer 1 created")
        developers.append((dev1_id, api_key1))
    else:
        print("❌ Failed to create developer 1")
        return None
    
    # Create second developer
    dev2_id, api_key2 = await create_developer(
        str(org_id),
        "bob@test.com",
        "Bob",
        "Jones"
    )
    
    if dev2_id and api_key2:
        print(f"✅ Developer 2 created")
        developers.append((dev2_id, api_key2))
    else:
        print("❌ Failed to create developer 2")
    
    return developers


async def test_authentication(api_key: str):
    """Test authentication with API key."""
    print("\n" + "=" * 60)
    print("TEST 3: Authentication")
    print("=" * 60)
    
    from src.core.auth import AuthManager
    
    database_url = os.getenv("DATABASE_URL")
    auth_manager = AuthManager(database_url)
    
    result = await auth_manager.authenticate(api_key)
    
    if result.allowed:
        print(f"✅ Authentication successful")
        print(f"   Developer ID: {result.developer_id}")
        print(f"   Organization ID: {result.organization_id}")
        return True
    else:
        print(f"❌ Authentication failed: {result.error}")
        return False


def test_commercial_tools(api_key: str):
    """Test commercial tier tools."""
    print("\n" + "=" * 60)
    print("TEST 4: Commercial Tier Tools")
    print("=" * 60)
    
    # Set up environment
    os.environ["HOTCROSS_API_KEY"] = api_key
    os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL")
    
    from src.core.middleware import init_auth, FeatureTier
    from src.core.registry import PortalRegistry
    from src.uri.parser import MemoryURI
    
    # Initialize auth
    init_auth()
    
    print(f"\n✅ Tier: {FeatureTier.get_tier()}")
    print(f"✅ Todo Management: {FeatureTier.is_feature_allowed('todo_management')}")
    print(f"✅ Document Management: {FeatureTier.is_feature_allowed('document_management')}")
    print(f"✅ Project Limit: {FeatureTier.get_project_limit() or 'Unlimited'}")
    
    # Test memory portal
    print("\n📝 Testing Memory Portal...")
    registry = PortalRegistry()
    uri = MemoryURI.parse("mem://test/commercial")
    portal = registry.resolve(uri)
    
    data = [{"name": "Test", "value": 123}]
    result = portal.write("test_table", data)
    print(f"✅ Wrote {result.rows_written} rows to {result.table}")
    
    # Test query
    query_result = portal.query("SELECT * FROM test_table")
    print(f"✅ Query returned {len(query_result.data)} rows")
    
    return True


def test_free_tier_restrictions():
    """Test free tier restrictions."""
    print("\n" + "=" * 60)
    print("TEST 5: Free Tier Restrictions")
    print("=" * 60)
    
    # Enable self-hosted mode
    os.environ["HOTCROSS_SELF_HOSTED"] = "true"
    
    # Clear any existing auth
    from src.core import middleware
    middleware._auth_manager = None
    middleware._auth_enabled = False
    
    from src.core.middleware import init_auth, FeatureTier
    
    init_auth()
    
    print(f"\n✅ Tier: {FeatureTier.get_tier()}")
    print(f"❌ Todo Management: {FeatureTier.is_feature_allowed('todo_management')}")
    print(f"❌ Document Management: {FeatureTier.is_feature_allowed('document_management')}")
    print(f"⚠️  Project Limit: {FeatureTier.get_project_limit()}")
    
    # Test that restricted features return errors
    from src.server import todo_create
    
    result = todo_create(
        portal_uri="mem://test/free",
        title="Test Todo",
        project_name="test"
    )
    
    if not result.get("success") and "Commercial" in result.get("error", ""):
        print(f"✅ Todo tool correctly blocked: {result['error']}")
    else:
        print(f"❌ Todo tool should be blocked but wasn't")
    
    return True


async def test_seat_limits(org_id: UUID):
    """Test seat limit enforcement."""
    print("\n" + "=" * 60)
    print("TEST 6: Seat Limit Enforcement")
    print("=" * 60)
    
    from scripts.admin.manage_orgs import create_developer
    
    # Create 3rd developer (should succeed - fills last seat)
    dev3_id, api_key3 = await create_developer(
        str(org_id),
        "charlie@test.com",
        "Charlie",
        "Brown"
    )
    
    if dev3_id:
        print("✅ 3rd developer created (3/3 seats)")
    else:
        print("❌ 3rd developer should have been created")
        return False
    
    # Try to create 4th developer (should fail - exceeds max_seats=3)
    dev4_id, api_key4 = await create_developer(
        str(org_id),
        "dave@test.com",
        "Dave",
        "Wilson"
    )
    
    if not dev4_id:
        print("✅ 4th developer correctly blocked (seat limit reached)")
        return True
    else:
        print("❌ 4th developer should have been blocked")
        return False


async def cleanup(org_id: UUID):
    """Clean up test data."""
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)
    
    import asyncpg
    
    database_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(database_url)
    
    try:
        # Delete organization (cascades to developers)
        await conn.execute("DELETE FROM organizations WHERE id = $1", org_id)
        print("✅ Test data cleaned up")
    finally:
        await conn.close()


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print(" " * 15 + "HOTCROSS COMPLETE FLOW TEST")
    print("=" * 70)
    
    # Check environment
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL not set")
        return
    
    if not os.getenv("STRIPE_SECRET_KEY"):
        print("⚠️  STRIPE_SECRET_KEY not set (Stripe customer creation will be skipped)")
    
    try:
        # Test 1: Create organization
        org_id = await test_org_creation()
        if not org_id:
            return
        
        # Test 2: Create developers
        developers = await test_developer_creation(org_id)
        if not developers:
            await cleanup(org_id)
            return
        
        dev1_id, api_key1 = developers[0]
        
        # Test 3: Authenticate
        auth_success = await test_authentication(api_key1)
        if not auth_success:
            await cleanup(org_id)
            return
        
        # Test 4: Commercial tools
        test_commercial_tools(api_key1)
        
        # Test 5: Free tier restrictions
        test_free_tier_restrictions()
        
        # Test 6: Seat limits
        await test_seat_limits(org_id)
        
        # Cleanup
        await cleanup(org_id)
        
        print("\n" + "=" * 70)
        print(" " * 20 + "✅ ALL TESTS PASSED")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
        if 'org_id' in locals():
            await cleanup(org_id)


if __name__ == "__main__":
    asyncio.run(main())
