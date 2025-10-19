# Luna Extension Store

Official extension repository for the Luna personal assistant system.

## Overview

This repository serves as the central extension store for Luna, containing both small embedded extensions (code included) and metadata for larger external extensions hosted in separate repositories.

## Structure

```
luna-ext-store/
├── registry.json           # Master catalog of all extensions
├── embedded/              # Small extensions (code included)
│   ├── generalbyte/
│   ├── home_assistant/
│   ├── notes/
│   └── todo_list/
└── external/              # Large extensions (metadata only)
    └── grocy.json
```

## Available Extensions

### Embedded Extensions

#### GeneralByte
**Category**: Utilities  
**Tools**: 3  
**Secrets**: `HA_URL`, `HA_TOKEN`, `TAVILY_API_KEY`

Minimal utilities including:
- Phone notifications via Home Assistant
- Tavily web search
- Weather information (Open-Meteo)

#### Home Assistant
**Category**: Smart Home  
**Tools**: 5  
**Secrets**: `HA_URL`, `HA_TOKEN`

Complete Home Assistant integration for controlling:
- Lights, switches, fans
- Media players
- TV remote control
- Entity status monitoring

#### Notes
**Category**: Productivity  
**Tools**: 4  
**Secrets**: None

Obsidian-style note management with:
- Project hierarchy
- Dated entries (MM/DD/YY format)
- Markdown support
- Section organization

#### Todo List
**Category**: Productivity  
**Tools**: 7  
**Secrets**: `TODOIST_API_TOKEN`

Full Todoist integration with:
- Task CRUD operations
- Project and section management
- Advanced filtering
- Priority and due date support

### External Extensions

#### Grocy
**Category**: Productivity  
**Repository**: [jbrinkw/luna-ext-grocy](https://github.com/jbrinkw/luna-ext-grocy)  
**Secrets**: `GROCY_URL`, `GROCY_API_KEY`

Grocy grocery and household management integration for:
- Inventory tracking
- Shopping lists
- Recipe management
- Meal planning

## Extension Types

### Embedded Extensions
Small extensions where the complete source code is included in this repository under `embedded/`. These are ideal for:
- Simple tool collections
- Lightweight integrations
- Extensions with minimal dependencies
- Quick-start extensions for common use cases

Each embedded extension contains:
- `config.json` - Extension metadata
- `tools/` - Tool implementations and configuration
- `readme.md` - Extension documentation

### External Extensions
Large or complex extensions hosted in separate repositories. Only metadata JSON files are stored here under `external/`. These are ideal for:
- Complex integrations with many dependencies
- Extensions with UI components
- Extensions with background services
- Third-party contributed extensions

## Registry Format

The `registry.json` file is the master catalog that Luna Hub UI fetches to display available extensions. It contains:

- Extension metadata (id, name, version, description)
- Installation sources (embedded path or GitHub URL)
- Required secrets
- Tool and service counts
- Categories and tags

## Installation in Luna

### For Embedded Extensions
```
Source format: github:user/luna-ext-store:embedded/extension_name
Target: extension_name
```

Example: To install the notes extension, Luna's apply_updates.py will:
1. Clone this repository to a temp directory
2. Copy `embedded/notes/` to `extensions/notes/`
3. Install dependencies from `requirements.txt`

### For External Extensions
```
Source format: github:user/repo-name
Target: extension_name
```

Example: To install grocy, Luna will:
1. Clone the external repository directly to `extensions/grocy/`
2. Install dependencies

## Extension Structure (Embedded)

Each embedded extension follows this structure:

```
extension_name/
├── config.json              # Extension metadata
├── readme.md               # Documentation
├── requirements.txt        # Python dependencies (optional)
├── tools/
│   ├── tool_config.json   # Tool configurations
│   └── *_tools.py         # Tool implementations
└── [other files]          # Extension-specific files
```

### config.json
```json
{
  "version": "MM-DD-YY",
  "name": "Extension Name",
  "description": "Brief description",
  "required_secrets": ["SECRET_1", "SECRET_2"],
  "auto_update": false
}
```

### tools/tool_config.json
```json
{
  "DOMAIN_ACTION_tool_name": {
    "enabled_in_mcp": true,
    "passthrough": false
  }
}
```

## Tool Naming Convention

Tools follow the pattern: `DOMAIN_{GET|UPDATE|ACTION}_VerbNoun`

Examples:
- `NOTES_GET_project_hierarchy`
- `NOTES_UPDATE_project_note`
- `HA_ACTION_turn_entity_on`
- `TODOLIST_GET_list_tasks`

## Contributing

To add a new extension to this store:

### For Small Extensions (Embedded)
1. Create directory under `embedded/your-extension/`
2. Add `config.json`, `readme.md`, and `tools/`
3. Update `registry.json` with your extension metadata
4. Submit a pull request

### For Large Extensions (External)
1. Create your extension in a separate repository
2. Add metadata JSON file to `external/your-extension.json`
3. Update `registry.json` with your extension entry
4. Submit a pull request

## Categories

- **Productivity**: Task management, notes, organization
- **Smart Home**: Home automation, IoT devices
- **Utilities**: General-purpose helper tools
- **Communication**: Messaging, notifications
- **Development**: Developer tools and integrations

## Version Format

Extensions use `MM-DD-YY` format for versions (e.g., `10-19-25` for October 19, 2025).

## License

Each extension may have its own license. Refer to individual extension directories for license information.

## Support

For issues with specific extensions:
- **Embedded extensions**: Open an issue in this repository
- **External extensions**: Open an issue in the external extension's repository

For general Luna system issues, refer to the main Luna repository.

