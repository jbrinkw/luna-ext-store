# Notes Extension

Obsidian-style note-taking system with project hierarchy, dated entries, and markdown support.

## Features

- **Project Hierarchy**: Organize notes in parent-child project relationships using frontmatter
- **Dated Entries**: Create and query dated note entries in MM/DD/YY format
- **Project Pages**: Maintain both main project pages and associated Notes.md files
- **Section Support**: Organize note content under markdown sections
- **Date Range Queries**: Search for notes within specific date ranges

## Tools

### NOTES_GET_project_hierarchy
Return a simplified project hierarchy showing root projects and their immediate children.

**Example**: "show my project hierarchy"

**Response Format**:
```
Eco AI
- Roadmap
- Research

Luna Personal Assistant
- ChefByte
- CoachByte
```

### NOTES_GET_project_text
Retrieve the content of both the main project page and the associated Notes.md file for a project.

**Example**: "show the text for project Eco AI"

**Parameters**:
- `project_id`: Project ID or display name
- `base_dir`: Optional override for vault location

**Response**: Returns both root page text and note page text

### NOTES_GET_notes_by_date_range
Query dated note entries within a specific date range across all Notes.md files.

**Example**: "find my notes between 06/01/24 and 06/15/24"

**Parameters**:
- `start_date`: Start date in MM/DD/YY format
- `end_date`: End date in MM/DD/YY format
- `base_dir`: Optional override for vault location

**Response**: Returns entries sorted by date (newest first) with file paths and content

### NOTES_UPDATE_project_note
Append content to today's dated entry for a project. Creates file/entry if needed.

**Example**: "add 'ship MVP' under 'Milestones' for project Eco AI"

**Parameters**:
- `project_id`: Project ID or display name
- `content`: Text to append
- `section_id`: Optional markdown section header (e.g., "Milestones", "Tasks")
- `base_dir`: Optional override for vault location

**Behavior**:
- Creates Notes.md file if it doesn't exist
- Creates today's date entry if not present
- Creates specified section if not present
- Appends content under the section or at the end of the entry

## Configuration

### Environment Variables (Optional)

```
OBSIDIAN_VAULT_DIR=/path/to/your/vault
# or
NOTES_BASE_DIR=/path/to/your/notes
```

If not set, defaults to the `Obsidian Vault` directory within the extension.

## Project Structure

### Project Frontmatter

Projects are identified by frontmatter in markdown files:

```yaml
---
project_id: My Project
project_parent: Parent Project  # optional
---
```

### Notes Files

Each project can have an associated `Notes.md` file with:

```yaml
---
note_project_id: My Project
---
```

### Dated Entries Format

```markdown
6/1/24

## Tasks
- Complete feature X
- Review PR #123

## Milestones
Ship MVP

6/2/24

## Tasks
- New task for today
```

## Example Workflows

### Creating a Note Entry
```
User: "Add 'Review architecture docs' under Tasks for project Luna"
Assistant: Creates/updates today's entry in Luna/Notes.md under the Tasks section
```

### Querying Recent Notes
```
User: "Show me my notes from the past week"
Assistant: Queries notes from (today - 7 days) to today and returns all entries
```

### Viewing Project Content
```
User: "Show me everything about the Eco AI project"
Assistant: Returns both the main project page and all note entries
```

## Dependencies

- `pydantic`
- `python-dotenv` (optional)

Install via: `pip install pydantic python-dotenv`

## Notes

- Date format is strictly MM/DD/YY (e.g., 6/1/24, 12/25/24)
- Project hierarchy is built from markdown frontmatter
- The extension handles both display names and project IDs for lookups
- Section headers use markdown format (##, ###, etc.)
- All timestamps are generated automatically for today's date

