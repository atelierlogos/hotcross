# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Hotcross, please report it by emailing **james@atelierlogos.studio** (or your preferred contact method). Please do not open a public issue.

We take all security reports seriously and will respond within 48 hours.

### What to Include

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)

## Security Features

### Authentication

Hotcross uses API key authentication backed by PostgreSQL:

- **API Key Format**: `hc_live_*` prefix for production keys
- **Key Storage**: SHA-256 hashed in PostgreSQL database
- **Validation**: All 37 MCP tools require valid API key
- **Subscription Check**: Keys must have `active` or `trialing` subscription status
- **Revocation**: Keys can be revoked via `api_key_revoked_at` timestamp
- **Usage Tracking**: Last used timestamp updated on each request

### Environment Variables

**Required:**
- `DATABASE_URL` - PostgreSQL connection string for authentication
- `HOTCROSS_API_KEY` - API key for accessing MCP tools

**Security Best Practices:**
- Never commit `.env` files to version control (already in `.gitignore`)
- Use strong PostgreSQL passwords
- Rotate API keys regularly
- Use environment-specific keys (dev vs production)

### Database Security

**PostgreSQL (Authentication):**
- Stores customer data and API key hashes
- Connection via `asyncpg` with connection pooling
- SQL injection protection via parameterized queries

**ChDB (Data Storage):**
- Local embedded database for portal data
- File-based storage in `.db` files
- No network exposure by default

### Network Security

- MCP server runs locally via stdio transport
- No HTTP endpoints exposed by default
- Communication through Claude Desktop or MCP Inspector only

## Known Limitations

1. **API Keys in Environment**: Keys are passed via environment variables, which may be visible in process listings
2. **Local Storage**: ChDB files are stored unencrypted on disk
3. **No Rate Limiting**: Currently no built-in rate limiting on tool calls
4. **Sync Auth in Async Context**: Authentication uses sync wrappers around async operations

## Security Roadmap

- [ ] Add rate limiting per customer
- [ ] Implement API key rotation mechanism
- [ ] Add audit logging for all authenticated operations
- [ ] Support for encrypted ChDB storage
- [ ] Add IP allowlisting for API keys
- [ ] Implement webhook signatures for external integrations

## Dependencies

Hotcross relies on several third-party packages. We monitor for security updates:

- `fastmcp` - MCP server framework
- `asyncpg` - PostgreSQL async driver
- `chdb` - Embedded ClickHouse database
- `tree-sitter` - Code parsing
- `pydantic` - Data validation

Run `uv pip list --outdated` regularly to check for updates.

## Compliance

- **Data Residency**: All data stored locally in ChDB files
- **GDPR**: Customer data can be deleted via `code_delete_project` tool
- **Logging**: Authentication failures logged but API keys never logged

## Contact

For security concerns, contact: **security@hotcross.dev**

For general issues, use GitHub Issues: https://github.com/yourusername/hotcross/issues
