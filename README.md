# Luna Extension Store Specification v1.1

**Last Updated:** 2025-11-04

## 1. Overview

Central repository for Luna extensions and services. Three types:
- **Embedded Extensions**: Code included in `embedded/`, typically < 100KB
- **External Extensions**: Metadata only in `external/`, code in separate repos
- **External Services**: Docker infrastructure services in `services/`

**Repository Structure:**
```
luna-ext-store/
├── README.md
├── registry.json          # Master catalog
├── embedded/              # Small extensions (code included)
├── external/              # Large extensions (metadata only)
└── services/              # External service definitions
```

## 2. Extension Structure

### Directory Layout
```
extension_name/
├── config.json                 # Metadata (REQUIRED)
├── readme.md                   # Docs (REQUIRED)
├── requirements.txt            # Python deps (optional)
├── package.json                # Node deps (optional)
├── tools/                      # Tool implementations
│   ├── tool_config.json        # Tool settings (REQUIRED if tools exist)
│   └── *_tools.py              # Tool files
├── ui/                         # UI component
│   ├── start.sh                # Startup script (REQUIRED if ui/)
│   └── [UI files]
└── services/                   # Background services
    └── service_name/
        ├── service_config.json # Service metadata (REQUIRED)
        └── start.sh            # Startup script (REQUIRED)
```

### config.json Schema
```json
{
  "version": "11-04-25",              // MM-DD-YY format
  "name": "Extension Name",
  "description": "Brief description",
  "required_secrets": ["API_KEY"],    // Required env vars
  "auto_update": false,
  "ui": {
    "trailing_slash": true,           // Enforce trailing slash (default: true)
    "open_mode": "new_tab"            // "new_tab" | "modal" | "iframe"
  }
}
```

**Luna-managed fields (auto-added, don't include):**
- `enabled`: boolean
- `source`: `"local"` | `"github:user/repo"` | `"github:user/repo:path"` | `"upload:file.zip"`

## 3. Tool Implementation

### File Structure
- **Naming**: `*_tools.py`
- **Exports**: `TOOLS` list (required), `SYSTEM_PROMPT` string (optional)

### Naming Convention
```
DOMAIN_{GET|UPDATE|ACTION}_VerbNoun
```

**Examples**: `NOTES_GET_project_hierarchy`, `HA_ACTION_turn_entity_on`, `TODOLIST_UPDATE_complete_task`

### Function Template
```python
import json
from typing import Optional

SYSTEM_PROMPT = "Context for LLM about these tools"

def DOMAIN_ACTION_description(param1: str, param2: int = 0) -> tuple[bool, str]:
    """
    Brief description.

    Example Prompt: "What users say to trigger this"

    Example Response:
    {
      "key": "value"
    }

    Example Args:
    {
      "param1": "example",
      "param2": 123
    }
    """
    try:
        result = {"status": "success", "data": "..."}
        return (True, json.dumps(result, ensure_ascii=False))
    except Exception as e:
        error = {"status": "error", "message": str(e)}
        return (False, json.dumps(error, ensure_ascii=False))

TOOLS = [DOMAIN_ACTION_description]
```

**Return format**: `(success: bool, json_string: str)`
**Critical**: Always use `json.dumps(..., ensure_ascii=False)`

### tool_config.json
```json
{
  "TOOL_NAME": {
    "enabled_in_mcp": true,     // Available in MCP servers
    "passthrough": false        // Auto-execute without approval
  }
}
```

**Passthrough**: `true` for safe/read-only ops, `false` for destructive actions

## 4. UI Components

### Structure
```
ui/
├── start.sh           # REQUIRED
├── package.json       # If Node.js
├── requirements.txt   # If Python
└── [source files]
```

### start.sh Template
```bash
#!/bin/bash
set -e
PORT=$1
if [ -z "$PORT" ]; then
    echo "Error: Port not provided"
    exit 1
fi

# Install deps
[ ! -d "node_modules" ] && npm install

# Start server
npm run dev -- --port $PORT --host 0.0.0.0
```

**Environment vars**: `$1` (port), `$PORT`, `$PATH` (includes `.venv/bin`), `$LUNA_PORTS` (JSON)

**Routing**: `https://domain.com/ext/extension_name/`
- Port range: 5200-5299 (deterministic by extension name)
- Caddy auto-proxies requests

## 5. Services

### Structure
```
services/service_name/
├── service_config.json    # REQUIRED
├── start.sh               # REQUIRED
└── [other files]
```

### service_config.json
```json
{
  "name": "backend",
  "requires_port": true,
  "health_check": "/healthz",
  "restart_on_failure": true
}
```

### start.sh Template
```bash
#!/bin/bash
set -e
PORT=$1
[ -f requirements.txt ] && pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**Environment vars**: Same as UI + all `.env` vars
**Routing**: `https://domain.com/api/extension_name/`
- Port range: 5300-5399 (deterministic by service name)
**Health checks**: Luna polls `http://localhost:<port>/<health_check>`, expects HTTP 200

## 6. External Services

### service.json Schema
```json
{
  "name": "postgres",
  "display_name": "PostgreSQL",
  "description": "Brief description",
  "category": "infrastructure",
  "version": "16-alpine",
  "repository": "https://hub.docker.com/_/postgres",
  "tags": ["database", "sql"],

  "config_form": [
    {
      "name": "DB_NAME",
      "type": "text|password|number|select|checkbox",
      "label": "Display Label",
      "default": "default_value",
      "help_text": "Description",
      "required": true,
      "options": ["opt1", "opt2"]  // For type="select"
    }
  ],

  "commands": {
    "install": "docker run -d --name postgres-luna -e POSTGRES_DB={{DB_NAME}} -p {{DB_PORT}}:5432 postgres:16-alpine",
    "start": "docker start postgres-luna",
    "stop": "docker stop postgres-luna",
    "restart": "docker restart postgres-luna",
    "uninstall": "docker rm -f postgres-luna && rm -rf external_services/postgres/data",
    "health_check": "docker exec postgres-luna pg_isready -U {{DB_USER}}"
  },

  "health_check_expected": "accepting connections",  // String match or exit code

  "provides_vars": ["DATABASE_URL", "POSTGRES_HOST", "POSTGRES_PORT"],

  "post_install_env": {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "{{DB_PORT}}",
    "DATABASE_URL": "postgresql://{{DB_USER}}:{{DB_PASSWORD}}@localhost:{{DB_PORT}}/{{DB_NAME}}"
  },

  "ui": {  // Optional
    "base_path": "/",
    "slug": "postgres-admin",
    "port": 8080,                   // Static port OR
    "config_field": "UI_PORT",      // Config field name
    "scheme": "http",
    "strip_prefix": false,
    "trailing_slash": true,
    "open_mode": "new_tab"
  }
}
```

**Template vars**: Use `{{FIELD_NAME}}` in commands and post_install_env

**Service UI routing**: `https://domain.com/ext_service/{slug}/`

### Runtime Artifacts
- `.luna/external_services.json` - Status registry
- `.luna/external_service_routes.json` - UI routing metadata
- `external_services/<name>/config.json` - User config (git-ignored)
- `external_services/<name>/data/` - Persistent data (git-ignored)

### API Endpoints
- `GET /api/external-services/available` - List available
- `GET /api/external-services/installed` - List installed
- `POST /api/external-services/{name}/install` - Install with config
- `POST /api/external-services/{name}/{start|stop|restart|uninstall}` - Control
- `POST /api/external-services/{name}/{enable|disable}` - Auto-start toggle

## 7. Installation & Queue System

### Installation Sources
| Type | Format | Example |
|------|--------|---------|
| Embedded | `github:user/repo:embedded/name` | `github:user/luna-ext-store:embedded/notes` |
| External | `github:user/repo` | `github:user/luna-ext-grocy` |
| Monorepo | `github:user/repo:path` | `github:user/mono:extensions/ext` |
| Upload | `upload:file.zip` | `upload:my-ext.zip` |

### Process
1. User requests install via Hub UI
2. Operation queued in `core/update_queue.json`
3. User triggers `/api/supervisor/restart`
4. `core/scripts/apply_updates.py` processes queue:
   - Delete operations
   - Install operations
   - Update operations
   - External service operations
   - Core updates
   - Dependency installation (pip/npm)
   - Config sync
5. Queue cleared, services restart

### Queue Operations
```json
{
  "operations": [
    {"type": "install", "target": "ext_name", "source": "github:user/repo"},
    {"type": "update", "target": "ext_name", "source": "github:user/repo"},
    {"type": "delete", "target": "ext_name"},
    {"type": "install_external_service", "name": "postgres", "config": {...}},
    {"type": "update_core", "target_version": "latest"}
  ],
  "master_config": {...}
}
```

## 8. Port Assignments

| Component | Range | Assignment |
|-----------|-------|------------|
| Extension UIs | 5200-5299 | Deterministic hash of extension name |
| Extension Services | 5300-5399 | Deterministic hash of service name |
| Core Services | Fixed | Agent API: 8080, MCP: 8766+, Auth: 8765, Hub UI: 5173 |
| External Services | User-defined | From service config |

**Algorithm**: `port = base_port + (hash(name) % range_size)`

**Persistence**: Stored in `master_config.json` under `port_assignments`

**Access in code**:
```bash
PORT=$1              # Script argument
PORT=$PORT           # Environment variable
LUNA_PORTS="{...}"   # JSON with all assignments
```

## 9. registry.json

Master catalog for Hub UI. Located at repo root.

```json
{
  "version": "1.1",
  "last_updated": "2025-11-04T12:00:00Z",
  "extensions": [
    {
      "id": "notes",
      "name": "Notes Manager",
      "type": "embedded|external",
      "category": "productivity",
      "description": "Brief description",
      "version": "11-04-25",
      "source": "github:user/repo:embedded/notes",
      "repository": "https://github.com/user/repo",
      "required_secrets": [],
      "tool_count": 4,
      "service_count": 0,
      "has_ui": false,
      "tags": ["notes", "markdown"],
      "readme_url": "https://raw.githubusercontent.com/..."
    }
  ],
  "external_services": [
    {
      "name": "postgres",
      "display_name": "PostgreSQL",
      "description": "Brief description",
      "category": "infrastructure",
      "version": "16-alpine",
      "repository": "https://hub.docker.com/_/postgres",
      "tags": ["database"],
      "provides_vars": ["DATABASE_URL", "POSTGRES_HOST"],
      "config_fields": 4,
      "has_ui": false,
      "service_definition_url": "https://raw.githubusercontent.com/.../service.json",
      // OR inline:
      "service_definition": {...}  // Full service.json content
    }
  ]
}
```

## 10. Extension vs External Service

| Feature | Extension | External Service |
|---------|-----------|------------------|
| Purpose | Add functionality | Provide infrastructure |
| Location | `extensions/` | Docker containers |
| Tools | Yes, exports TOOLS | No |
| UI | Optional (5200-5299) | Optional (user-defined port) |
| Services | Optional (5300-5399) | Main purpose |
| Env Vars | Requires secrets | Provides vars |
| Health Checks | Optional | Required |
| Auto-Restart | Optional | Supported |

## 11. Contributing

### Adding Embedded Extension
1. Create `embedded/your-ext/` with required files
2. Implement tools (section 3)
3. Test locally
4. Update `registry.json`
5. Submit PR

### Adding External Extension
1. Create separate repo
2. Implement extension
3. Add metadata to `external/your-ext.json`
4. Update `registry.json`
5. Submit PR

### Adding External Service
1. Create `services/your-service/service.json`
2. Test installation locally
3. Update `registry.json`
4. Submit PR

### Testing Checklist
- [ ] Valid `config.json`
- [ ] Documented required secrets
- [ ] Tools follow naming convention (DOMAIN_ACTION_description)
- [ ] Docstrings have Example Prompt/Response/Args
- [ ] `TOOLS` exported from `*_tools.py`
- [ ] Valid `tool_config.json`
- [ ] Executable `start.sh` scripts accept port argument
- [ ] Service health checks work
- [ ] Complete README
- [ ] Accurate `registry.json` entry
- [ ] Successful installation in Luna
- [ ] All tools functional
- [ ] UI accessible (if applicable)
- [ ] Services start and pass health checks
- [ ] No committed secrets

### Code Standards
**Python**: PEP 8, type hints, docstrings, `json.dumps(..., ensure_ascii=False)`, exception handling
**JavaScript**: ESLint, JSDoc comments, error handling
**Shell**: `set -e`, validate input, clear errors, test on Linux

### Documentation Requirements
**Extension README**: Name, description, installation, required secrets (how to obtain), tool list, example prompts, config options, troubleshooting, license

**Service README**: Description, config field explanations, provided env vars, port requirements, data persistence, health checks, uninstallation

## Appendix: Minimal Examples

### Tools Only
```
minimal/
├── config.json
├── readme.md
└── tools/
    ├── tool_config.json
    └── example_tools.py
```

```python
# example_tools.py
import json

SYSTEM_PROMPT = "You help with example tasks."

def EXAMPLE_GET_greeting(name: str = "World") -> tuple[bool, str]:
    """
    Return greeting message.
    Example Prompt: "Say hello"
    Example Response: {"status": "success", "message": "Hello, World!"}
    Example Args: {"name": "Alice"}
    """
    result = {"status": "success", "message": f"Hello, {name}!"}
    return (True, json.dumps(result, ensure_ascii=False))

TOOLS = [EXAMPLE_GET_greeting]
```

### With UI
Add `ui/start.sh`:
```bash
#!/bin/bash
set -e
PORT=$1
[ -z "$PORT" ] && echo "Error: Port not provided" && exit 1
[ ! -d "node_modules" ] && npm install
npm run dev -- --port $PORT --host 0.0.0.0
```

### With Service
Add `services/backend/service_config.json`:
```json
{"name": "backend", "requires_port": true, "health_check": "/health", "restart_on_failure": true}
```

Add `services/backend/start.sh`:
```bash
#!/bin/bash
set -e
PORT=$1
[ -z "$PORT" ] && echo "Error: Port not provided" && exit 1
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

**Resources**
- Luna Repo: https://github.com/user/luna-personal-assistant
- Extension Store: https://github.com/user/luna-ext-store
- MCP Protocol: https://modelcontextprotocol.io
- FastMCP: https://github.com/jlowin/fastmcp

**Support**: Open issues in respective repos, GitHub Discussions, Discord community
