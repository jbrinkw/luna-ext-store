# Obsidian Sync Extension

Syncs an Obsidian vault to the extension directory and provides note management tools.

## Features

- Automatic vault synchronization service
- Full note hierarchy access
- Note reading and updating capabilities
- Project-based organization

## Required Environment Variables

### OBSIDIAN_VAULT_LINK

The path to your Obsidian vault directory that should be synced.

**Example:**
```
OBSIDIAN_VAULT_LINK=/home/user/Documents/ObsidianVault
OBSIDIAN_VAULT_LINK=C:\Users\username\Documents\ObsidianVault
```

## Installation

1. Add the extension via Luna Hub UI
2. Configure `OBSIDIAN_VAULT_LINK` environment variable in `.env`
3. Restart Luna to activate the sync service

## Tools Available

### NOTES_GET_project_hierarchy
Retrieve the hierarchical structure of notes organized by project.

**Example Prompt:** "Show me my project structure"

### NOTES_GET_project_text
Read both the project hub page and its associated `Notes.md` file.

**Example Prompt:** "Show me the content of my Eco AI project"

### NOTES_GET_notes_by_date_range
Collect dated note entries between two MM/DD/YY dates across the vault.

**Example Prompt:** "Gather my notes between 06/01/25 and 06/07/25"

### NOTES_UPDATE_project_note
Update or create a note within a project.

**Example Prompt:** "Add this to today's work notes under Milestones"

## How It Works

The sync service runs in the background and:
1. Checks the vault directory specified in `OBSIDIAN_VAULT_LINK`
2. Syncs files to `extensions/obsidian_sync/vault/`
3. Maintains synchronization on a regular interval
4. Makes notes accessible via Luna's note tools

## Troubleshooting

### Vault not syncing

- Verify `OBSIDIAN_VAULT_LINK` points to a valid directory
- Check service logs: `.luna/logs/obsidian_sync.sync_service.log`
- Ensure proper read permissions on the vault directory

### Tools not finding notes

- Confirm the sync service is running
- Check that files are present in `extensions/obsidian_sync/vault/`
- Verify the vault structure matches expected format

## License

MIT License
