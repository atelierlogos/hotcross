# Changelog

All notable changes to Hotcross will be documented in this file.

## [Unreleased]

### Added
- Organization-based authentication model
- Support for per-organization pricing with seat limits
- New admin script `manage_orgs.py` for managing organizations and developers
- Database schema with `organizations` and `developers` tables
- Seat limit enforcement in authentication
- Developer-level API key management
- Migration guide from customer-based to organization-based model
- Stripe customer auto-creation when creating organizations

### Changed
- Authentication now validates against organizations and developers
- Middleware now provides `_developer_id` and `_organization_id` instead of `_customer_id`
- Admin workflow now requires creating organization first, then developers
- API keys are now per-developer instead of per-customer

### Deprecated
- `scripts/admin/create_customer.py` - Use `manage_orgs.py` instead
- Customer-based data model

### Security
- Added seat limit checks to prevent unauthorized access
- Enhanced authentication with organization-level subscription validation
- Per-developer API key tracking and revocation

## [0.1.0] - Initial Release

### Added
- MCP server with 37 authenticated tools
- Memory portal management
- Code intelligence with tree-sitter
- Project and document management
- Session and todo management
- PostgreSQL-based authentication
- ChDB for local data storage
- `mem://` URI scheme
- Customer-based authentication model
