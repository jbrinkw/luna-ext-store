#!/bin/bash
set -e

# Obsidian Vault Sync Service
# Syncs the Obsidian vault from OBSIDIAN_VAULT_LINK to extensions/obsidian_sync/vault/

# Check if OBSIDIAN_VAULT_LINK is set
if [ -z "$OBSIDIAN_VAULT_LINK" ]; then
    echo "Error: OBSIDIAN_VAULT_LINK environment variable not set"
    exit 1
fi

# Check if source vault exists
if [ ! -d "$OBSIDIAN_VAULT_LINK" ]; then
    echo "Error: Vault directory not found: $OBSIDIAN_VAULT_LINK"
    exit 1
fi

# Get the target vault directory (relative to this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VAULT_TARGET="$SCRIPT_DIR/../vault"

echo "Starting Obsidian Vault Sync Service"
echo "Source: $OBSIDIAN_VAULT_LINK"
echo "Target: $VAULT_TARGET"

# Create target directory if it doesn't exist
mkdir -p "$VAULT_TARGET"

# Sync function
sync_vault() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Syncing vault..."
    
    # Use rsync for efficient sync
    # -a: archive mode (preserves permissions, timestamps, etc.)
    # -v: verbose
    # --delete: remove files in target that don't exist in source
    # --exclude: ignore Obsidian's config and cache
    rsync -av --delete \
        --exclude='.obsidian/' \
        --exclude='.trash/' \
        --exclude='.DS_Store' \
        "$OBSIDIAN_VAULT_LINK/" "$VAULT_TARGET/"
    
    if [ $? -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync completed successfully"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync failed"
    fi
}

# Initial sync
sync_vault

# Continuous sync loop (every 5 minutes)
while true; do
    sleep 300  # 5 minutes
    sync_vault
done
