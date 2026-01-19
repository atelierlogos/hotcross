# Migration Guide: Customer-based to Organization-based Model

This guide helps you migrate from the old customer-based data model to the new organization-based model.

## What Changed

**Old Model:**
- `customers` table: 1 customer = 1 Stripe customer = 1 API key
- Per-developer pricing only

**New Model:**
- `organizations` table: 1 organization = 1 Stripe customer = multiple developers
- `developers` table: Each developer gets their own API key
- Supports both per-developer and per-organization pricing

## Migration Steps

### 1. Set up the new schema

```bash
# Connect to your PostgreSQL database
psql $DATABASE_URL -f scripts/schema.sql
```

This creates the new `organizations` and `developers` tables.

### 2. Migrate existing customers (if any)

If you have existing customers in the old schema, you can migrate them:

```sql
-- For each existing customer, create an organization and developer
INSERT INTO organizations (name, stripe_customer_id, subscription_status, max_seats)
SELECT 
    COALESCE(company, email) as name,
    stripe_customer_id,
    subscription_status,
    1 as max_seats
FROM customers;

-- Create developers from customers
INSERT INTO developers (
    organization_id,
    email,
    first_name,
    last_name,
    api_key_hash,
    api_key_prefix,
    api_key_created_at,
    api_key_revoked_at,
    api_key_last_used_at
)
SELECT 
    o.id as organization_id,
    c.email,
    c.first_name,
    c.last_name,
    c.api_key_hash,
    c.api_key_prefix,
    c.api_key_created_at,
    c.api_key_revoked_at,
    c.api_key_last_used_at
FROM customers c
JOIN organizations o ON c.stripe_customer_id = o.stripe_customer_id;

-- Drop old customers table (after verifying migration)
-- DROP TABLE customers;
```

### 3. Update your admin workflow

**Old way:**
```bash
python scripts/admin/create_customer.py create alice@acme.com Alice Smith "Acme Corp"
```

**New way:**
```bash
# Step 1: Create organization
python scripts/admin/manage_orgs.py create-org "Acme Corp" cus_stripe123 5

# Step 2: Create developers
python scripts/admin/manage_orgs.py create-dev <org_id> alice@acme.com Alice Smith
python scripts/admin/manage_orgs.py create-dev <org_id> bob@acme.com Bob Jones
```

### 4. Test authentication

```bash
# Set a developer's API key
export HOTCROSS_API_KEY="hc_live_..."
export DATABASE_URL="postgresql://..."

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run python -m src.server
```

## New Admin Commands

### Organizations

```bash
# Create organization
python scripts/admin/manage_orgs.py create-org "Acme Corp" [stripe_id] [max_seats]

# List all organizations
python scripts/admin/manage_orgs.py list-orgs

# Update subscription status
python scripts/admin/manage_orgs.py update-status <org_id> active

# Update seat limit
python scripts/admin/manage_orgs.py update-seats <org_id> 10
```

### Developers

```bash
# Create developer
python scripts/admin/manage_orgs.py create-dev <org_id> alice@acme.com Alice Smith

# List all developers
python scripts/admin/manage_orgs.py list-devs

# List developers in an org
python scripts/admin/manage_orgs.py list-devs <org_id>

# Revoke developer's API key
python scripts/admin/manage_orgs.py revoke-dev <developer_id>
```

## Pricing Models Supported

### Per-Organization (Recommended)
- Organization pays for N seats
- Each developer gets their own API key
- Example: $50/month for 5 developers

### Per-Developer
- Each developer is in their own 1-seat organization
- Individual subscriptions
- Example: $10/developer/month

### Hybrid
- Base fee per organization + per-seat pricing
- Track usage per developer for metering
- Example: $20/month base + $5/developer

## Breaking Changes

1. **API key validation** now checks:
   - Developer is active
   - API key not revoked
   - Organization subscription is active
   - Organization hasn't exceeded seat limit

2. **Middleware kwargs** changed:
   - Old: `_customer_id`
   - New: `_developer_id` and `_organization_id`

3. **Admin scripts** replaced:
   - Old: `scripts/admin/create_customer.py`
   - New: `scripts/admin/manage_orgs.py`

## Rollback

If you need to rollback:

1. Keep the old `customers` table (don't drop it)
2. Revert code changes to use old auth logic
3. Drop new tables: `DROP TABLE developers; DROP TABLE organizations;`
