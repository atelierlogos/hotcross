# Feature Comparison

## Pricing Tiers

### Free (Self-Hosted)
- **Price:** $0
- **Use Case:** Personal, non-commercial projects
- **Setup:** Set `HOTCROSS_SELF_HOSTED=true`

### Commercial
- **Price:** $75/developer/month
- **Use Case:** Professional and commercial use
- **Setup:** Get API key from [booking page](https://cal.com/team/atelierlogos/get-a-hotcross-api-key)

## Feature Matrix

| Category | Feature | Free | Commercial |
|----------|---------|------|------------|
| **Memory Portals** | Write data | ✅ | ✅ |
| | Query with SQL | ✅ | ✅ |
| | Delete data | ✅ | ✅ |
| | View schema | ✅ | ✅ |
| | List tables | ✅ | ✅ |
| | Drop tables | ✅ | ✅ |
| | List portals | ✅ | ✅ |
| **Code Intelligence** | Index files | ✅ | ✅ |
| | Index directories | ✅ | ✅ |
| | Find symbols | ✅ | ✅ |
| | Get file symbols | ✅ | ✅ |
| | Get imports | ✅ | ✅ |
| | Get exports | ✅ | ✅ |
| | Get dependencies | ✅ | ✅ |
| | Find references | ✅ | ✅ |
| | Get statistics | ✅ | ✅ |
| | Raw SQL queries | ✅ | ✅ |
| **Project Management** | Create project | ⚠️ 1 max | ✅ Unlimited |
| | Get project | ✅ | ✅ |
| | List projects | ✅ | ✅ |
| | Update project | ✅ | ✅ |
| | Delete project | ✅ | ✅ |
| **Document Management** | Index documents | ❌ | ✅ |
| | Get document | ❌ | ✅ |
| | List documents | ❌ | ✅ |
| | Search documents | ❌ | ✅ |
| **Session Management** | Create session | ✅ | ✅ |
| | Add message | ✅ | ✅ |
| | Get session | ✅ | ✅ |
| | Get messages | ✅ | ✅ |
| | List sessions | ✅ | ✅ |
| | Archive session | ✅ | ✅ |
| **Todo Management** | Create todo | ❌ | ✅ |
| | Update todo | ❌ | ✅ |
| | Get todo | ❌ | ✅ |
| | List todos | ❌ | ✅ |
| | Delete todo | ❌ | ✅ |
| **Support** | Community | ✅ | ✅ |
| | Priority support | ❌ | ✅ |
| **Commercial Use** | Permitted | ❌ | ✅ |

## Tool Count

- **Free Tier:** 28 tools
- **Commercial Tier:** 37 tools

## Upgrade Benefits

When you upgrade to Commercial, you get:

1. **Unlimited Projects** - No more 1-project limit
2. **Todo Management** - Full task tracking system (5 tools)
3. **Document Management** - Index and search documentation (4 tools)
4. **Priority Support** - Direct access to our team
5. **Commercial License** - Use Hotcross in your business

## Getting Started

### Free Tier
```json
{
  "mcpServers": {
    "hotcross": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/atelierlogos/hotcross", "hotcross"],
      "env": {
        "HOTCROSS_SELF_HOSTED": "true"
      }
    }
  }
}
```

### Commercial Tier
```json
{
  "mcpServers": {
    "hotcross": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/atelierlogos/hotcross", "hotcross"],
      "env": {
        "DATABASE_URL": "postgresql://...",
        "HOTCROSS_API_KEY": "hc_live_..."
      }
    }
  }
}
```

[Get your API key →](https://cal.com/team/atelierlogos/get-a-hotcross-api-key)
