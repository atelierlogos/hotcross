-- Hotcross Database Schema
-- Organization-based pricing model

-- Organizations (the paying entity)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    stripe_customer_id TEXT UNIQUE,
    subscription_status TEXT NOT NULL DEFAULT 'incomplete',
    subscription_id TEXT,
    max_seats INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Developers (individual users within organizations)
CREATE TABLE IF NOT EXISTS developers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    api_key_hash TEXT UNIQUE NOT NULL,
    api_key_prefix TEXT NOT NULL,
    api_key_created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    api_key_revoked_at TIMESTAMP,
    api_key_last_used_at TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_developers_org_id ON developers(organization_id);
CREATE INDEX IF NOT EXISTS idx_developers_api_key_hash ON developers(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_developers_email ON developers(email);
CREATE INDEX IF NOT EXISTS idx_organizations_stripe_customer_id ON organizations(stripe_customer_id);

-- Optional: Usage tracking for analytics
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    developer_id UUID NOT NULL REFERENCES developers(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_developer_id ON usage_logs(developer_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_org_id ON usage_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp);

-- Comments
COMMENT ON TABLE organizations IS 'Organizations that subscribe to Hotcross';
COMMENT ON TABLE developers IS 'Individual developers within organizations';
COMMENT ON TABLE usage_logs IS 'Optional usage tracking for analytics and billing';
COMMENT ON COLUMN organizations.max_seats IS 'Maximum number of developers allowed in this organization';
COMMENT ON COLUMN developers.api_key_hash IS 'SHA-256 hash of the API key';
COMMENT ON COLUMN developers.is_active IS 'Whether this developer account is active';
