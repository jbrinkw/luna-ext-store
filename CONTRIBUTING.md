# Contributing to Luna Extension Store

Thank you for your interest in contributing to the Luna Extension Store! This guide will help you add new extensions or improve existing ones.

## Table of Contents

- [Types of Extensions](#types-of-extensions)
- [Extension Structure](#extension-structure)
- [Adding an Embedded Extension](#adding-an-embedded-extension)
- [Adding an External Extension](#adding-an-external-extension)
- [Tool Guidelines](#tool-guidelines)
- [Documentation Requirements](#documentation-requirements)
- [Submission Process](#submission-process)

## Types of Extensions

### Embedded Extensions
Small, self-contained extensions where the complete source code lives in this repository under `embedded/`.

**Best for:**
- Simple tool collections (< 10 tools)
- Lightweight integrations
- Extensions with minimal dependencies
- Single-file or few-file implementations

### External Extensions
Large or complex extensions hosted in their own repositories.

**Best for:**
- Complex integrations (10+ tools)
- Extensions with UI components
- Extensions with background services
- Extensions requiring frequent independent updates
- Third-party contributed extensions

## Extension Structure

### Embedded Extension Layout
```
embedded/your_extension/
├── config.json              # Required: Extension metadata
├── readme.md               # Required: Documentation
├── requirements.txt        # Optional: Python dependencies
├── tools/
│   ├── tool_config.json   # Required: Tool configurations
│   └── your_tools.py      # Required: Tool implementations
└── [additional files]     # Optional: Supporting files
```

### config.json Format
```json
{
  "version": "10-19-25",
  "name": "Extension Display Name",
  "description": "Brief one-line description",
  "required_secrets": ["SECRET_KEY_1", "SECRET_KEY_2"],
  "auto_update": false
}
```

**Fields:**
- `version`: Date in MM-DD-YY format
- `name`: Human-readable extension name
- `description`: One-line summary (< 120 chars)
- `required_secrets`: Array of env var names needed
- `auto_update`: Always false (not implemented in MVP)

### tools/tool_config.json Format
```json
{
  "DOMAIN_ACTION_tool_name": {
    "enabled_in_mcp": true,
    "passthrough": false
  }
}
```

**Fields per tool:**
- `enabled_in_mcp`: Expose to MCP server (boolean)
- `passthrough`: For passthrough_agent (boolean)

## Adding an Embedded Extension

### Step 1: Create Directory Structure
```bash
mkdir -p embedded/your_extension/tools
cd embedded/your_extension
```

### Step 2: Create config.json
Use the template above, filling in your extension's details.

### Step 3: Implement Tools

Create `tools/your_tools.py`:

```python
from pydantic import BaseModel, Field
from typing import Tuple

SYSTEM_PROMPT = """
Description of what your extension does.
Guide the LLM on how to use your tools.
"""

# Pydantic models for validation
class YourToolArgs(BaseModel):
    param1: str = Field(...)
    param2: int = Field(default=10)

# Tool implementation
def DOMAIN_ACTION_your_tool(param1: str, param2: int = 10) -> Tuple[bool, str]:
    """One-sentence summary of what this tool does.
    
    Example Prompt: natural language example of how to invoke
    Example Response: {"result": "example output"}
    Example Args: {"param1": "string", "param2": 10}
    
    Notes: Optional additional details.
    """
    try:
        # Validate inputs
        args = YourToolArgs(param1=param1, param2=param2)
        
        # Your logic here
        result = f"Processed {args.param1} with {args.param2}"
        
        return (True, f'{{"result": "{result}"}}')
    except Exception as e:
        return (False, f"Error: {str(e)}")

# Export tools
TOOLS = [
    DOMAIN_ACTION_your_tool,
]
```

### Step 4: Create tool_config.json
List each tool with its configuration flags.

### Step 5: Write readme.md
See [Documentation Requirements](#documentation-requirements) below.

### Step 6: Add requirements.txt
List Python packages:
```
pydantic>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### Step 7: Update registry.json
Add your extension to the `extensions` array:

```json
{
  "id": "your_extension",
  "name": "Your Extension",
  "type": "embedded",
  "path": "embedded/your_extension",
  "version": "10-19-25",
  "description": "Brief description",
  "author": "Your Name",
  "category": "productivity",
  "has_ui": false,
  "tool_count": 3,
  "service_count": 0,
  "required_secrets": ["YOUR_API_KEY"],
  "tags": ["tag1", "tag2", "tag3"]
}
```

### Step 8: Submit Pull Request
See [Submission Process](#submission-process) below.

## Adding an External Extension

### Step 1: Create Extension Repository
Set up your extension in its own GitHub repository following the same structure as embedded extensions.

### Step 2: Create Metadata File
Create `external/your_extension.json` in this repository:

```json
{
  "id": "your_extension",
  "name": "Your Extension",
  "type": "external",
  "source": "github:username/repo-name",
  "version": "10-19-25",
  "description": "Brief description",
  "author": "Your Name",
  "category": "productivity",
  "has_ui": false,
  "tool_count": 15,
  "service_count": 1,
  "required_secrets": ["YOUR_API_KEY"],
  "tags": ["tag1", "tag2"],
  "preview_url": "https://github.com/username/repo-name"
}
```

### Step 3: Update registry.json
Add your extension to the `extensions` array using the same metadata as your JSON file.

### Step 4: Submit Pull Request
See [Submission Process](#submission-process) below.

## Tool Guidelines

### Naming Convention
Follow the pattern: `DOMAIN_{GET|UPDATE|ACTION}_VerbNoun`

**Examples:**
- `NOTES_GET_project_hierarchy` - Retrieve data
- `NOTES_UPDATE_project_note` - Modify data
- `HA_ACTION_turn_entity_on` - Perform action

**Prefix meanings:**
- `GET`: Retrieve/query operations (read-only)
- `UPDATE`: Modify/write operations
- `ACTION`: Commands/actions with side effects

### Docstring Requirements
Every tool must have a docstring with these sections:

```python
def YOUR_TOOL(param: str) -> Tuple[bool, str]:
    """One-sentence summary.
    
    Example Prompt: natural language command
    Example Response: {"key": "value"}
    Example Args: {"param": "string"}
    
    Notes: Optional additional context.
    """
```

### Return Format
All tools must return `Tuple[bool, str]`:
- `bool`: Success flag (True/False)
- `str`: JSON string result or error message

```python
# Success
return (True, '{"result": "data"}')

# Failure
return (False, "Error: something went wrong")
```

### Input Validation
Use Pydantic models to validate inputs:

```python
class MyToolArgs(BaseModel):
    required_param: str = Field(...)
    optional_param: int = Field(default=10)

def MY_TOOL(required_param: str, optional_param: int = 10) -> Tuple[bool, str]:
    try:
        args = MyToolArgs(required_param=required_param, optional_param=optional_param)
        # Use args.required_param, args.optional_param
    except Exception as e:
        return (False, f"Validation error: {e}")
```

## Documentation Requirements

### readme.md Structure

Your extension's `readme.md` should include:

1. **Title and Brief Description**
   ```markdown
   # Extension Name
   
   One-line description of what the extension does.
   ```

2. **Features**
   Bulleted list of key capabilities

3. **Tools**
   Document each tool with:
   - Name
   - Purpose
   - Example usage
   - Parameters
   - Response format

4. **Configuration**
   - Required environment variables
   - How to obtain API keys/tokens
   - Any setup steps

5. **Dependencies**
   - List required packages
   - Installation command

6. **Example Workflows**
   Show real-world usage patterns

7. **Notes/Caveats**
   Important details or limitations

### Example Template

```markdown
# Your Extension

Brief description.

## Features

- Feature 1
- Feature 2
- Feature 3

## Tools

### DOMAIN_ACTION_tool_name
Description of what it does.

**Example**: "natural language command"

**Parameters**:
- `param1`: Description
- `param2`: Optional parameter

**Response**: Description of return value

## Configuration

### Required Environment Variables

\`\`\`
YOUR_API_KEY=your-key-here
YOUR_URL=https://api.example.com
\`\`\`

### Setup Instructions

1. Step 1
2. Step 2
3. Step 3

## Dependencies

\`\`\`
pip install package1 package2
\`\`\`

## Example Workflows

### Workflow 1
\`\`\`
User: "command"
Assistant: [action taken]
\`\`\`

## Notes

Important details or limitations.
```

## Submission Process

### 1. Fork the Repository
```bash
git clone https://github.com/your-username/luna-ext-store.git
cd luna-ext-store
```

### 2. Create Feature Branch
```bash
git checkout -b add-your-extension
```

### 3. Make Changes
- Add your extension files
- Update `registry.json`
- Test thoroughly

### 4. Commit Changes
```bash
git add .
git commit -m "Add [extension-name] extension"
```

### 5. Push and Create PR
```bash
git push origin add-your-extension
```

Then create a Pull Request on GitHub with:
- Clear title: "Add [Extension Name] extension"
- Description of what the extension does
- Any special setup or testing notes

### 6. Review Process
Maintainers will review for:
- Code quality and style
- Documentation completeness
- Security considerations
- Proper error handling
- Tool naming conventions

## Categories

Choose the most appropriate category:
- **productivity**: Task management, notes, organization
- **smart-home**: Home automation, IoT
- **utilities**: General helpers and tools
- **communication**: Messaging, notifications
- **development**: Developer tools

## Version Format

Use `MM-DD-YY` format for versions (e.g., `10-19-25`).

Update version when making changes to your extension.

## Security Guidelines

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Validate all user inputs
- Handle errors gracefully
- Use HTTPS for API calls
- Document required secrets in `required_secrets` array

## Testing

Before submitting:
1. Test all tools with various inputs
2. Verify error handling
3. Check documentation accuracy
4. Ensure dependencies are correct
5. Test in a fresh Luna installation

## Questions?

Open an issue in this repository for:
- Questions about contributing
- Clarification on guidelines
- Feature requests
- Bug reports

## Code of Conduct

Be respectful, collaborative, and constructive. We're building tools to help people!

