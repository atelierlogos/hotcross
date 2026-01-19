#!/usr/bin/env python3
"""Demo showing feature tier restrictions.

This example demonstrates the difference between Free and Commercial tiers.
"""

import os

# Test Free tier (self-hosted)
print("=" * 60)
print("FREE TIER (Self-Hosted)")
print("=" * 60)

os.environ["HOTCROSS_SELF_HOSTED"] = "true"

from src.core.middleware import init_auth, FeatureTier

init_auth()

print(f"\n✅ Tier: {FeatureTier.get_tier()}")
print(f"✅ Memory Portals: Available")
print(f"✅ Code Intelligence: Available")
print(f"✅ Session Management: Available")
print(f"⚠️  Projects: {FeatureTier.get_project_limit()} project max")
print(f"❌ Todo Management: {'Available' if FeatureTier.is_feature_allowed('todo_management') else 'Requires Commercial'}")
print(f"❌ Document Management: {'Available' if FeatureTier.is_feature_allowed('document_management') else 'Requires Commercial'}")

print("\n" + "=" * 60)
print("COMMERCIAL TIER")
print("=" * 60)

# Simulate commercial tier by enabling auth
# (In real usage, this would be with DATABASE_URL + API key)
from src.core import middleware
middleware._auth_enabled = True

print(f"\n✅ Tier: {FeatureTier.get_tier()}")
print(f"✅ Memory Portals: Available")
print(f"✅ Code Intelligence: Available")
print(f"✅ Session Management: Available")
print(f"✅ Projects: {'Unlimited' if FeatureTier.get_project_limit() is None else FeatureTier.get_project_limit()}")
print(f"✅ Todo Management: {'Available' if FeatureTier.is_feature_allowed('todo_management') else 'Requires Commercial'}")
print(f"✅ Document Management: {'Available' if FeatureTier.is_feature_allowed('document_management') else 'Requires Commercial'}")

print("\n💡 Upgrade to Commercial for $75/developer/month")
print("   https://cal.com/team/atelierlogos/get-a-hotcross-api-key")
