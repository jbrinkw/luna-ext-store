#!/bin/bash
set -e

# Obsidian Vault Sync Service
# Syncs the Obsidian vault from OBSIDIAN_VAULT_LINK to extensions/obsidian_sync/vault/
# Supports both local directory paths and Git repository URLs

# Check if OBSIDIAN_VAULT_LINK is set
if [ -z "$OBSIDIAN_VAULT_LINK" ]; then
    echo "Error: OBSIDIAN_VAULT_LINK environment variable not set"
    exit 1
fi

# Check if rsync is installed, install if missing
if ! command -v rsync &> /dev/null; then
    echo "rsync not found, attempting to install..."
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update -qq && sudo apt-get install -y rsync || {
            echo "Error: Failed to install rsync. Please install it manually: sudo apt-get install rsync"
            exit 1
        }
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS
        sudo yum install -y rsync || {
            echo "Error: Failed to install rsync. Please install it manually: sudo yum install rsync"
            exit 1
        }
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        sudo pacman -Sy --noconfirm rsync || {
            echo "Error: Failed to install rsync. Please install it manually: sudo pacman -S rsync"
            exit 1
        }
    else
        echo "Error: rsync is not installed and package manager not detected."
        echo "Please install rsync manually for your distribution."
        exit 1
    fi
    echo "rsync installed successfully"
fi

# Get the target vault directory (relative to this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VAULT_TARGET="$SCRIPT_DIR/../vault"
VAULT_SOURCE_DIR="$SCRIPT_DIR/../vault_source"

# Determine if OBSIDIAN_VAULT_LINK is a Git URL or local path
if [[ "$OBSIDIAN_VAULT_LINK" =~ ^(https?://|git@) ]]; then
    # It's a Git URL - clone/update to local directory
    echo "Detected Git repository URL: $OBSIDIAN_VAULT_LINK"
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        echo "Error: git is not installed. Please install git to use Git repository URLs."
        exit 1
    fi
    
    # Handle authentication for HTTPS URLs
    GIT_URL="$OBSIDIAN_VAULT_LINK"
    if [[ "$OBSIDIAN_VAULT_LINK" =~ ^https:// ]] && [ -n "$OBSIDIAN_VAULT_GIT_TOKEN" ]; then
        # Embed token in HTTPS URL for authentication
        # Format: https://token@github.com/user/repo.git
        if [[ "$OBSIDIAN_VAULT_LINK" =~ ^https://([^/@]+@)?([^/]+)/(.+)$ ]]; then
            GIT_URL="https://${OBSIDIAN_VAULT_GIT_TOKEN}@${BASH_REMATCH[2]}/${BASH_REMATCH[3]}"
            echo "Using Git token for authentication"
        fi
    elif [[ "$OBSIDIAN_VAULT_LINK" =~ ^https:// ]] && [[ ! "$OBSIDIAN_VAULT_LINK" =~ @ ]]; then
        # HTTPS URL without embedded credentials - check for token or suggest SSH
        if [ -z "$OBSIDIAN_VAULT_GIT_TOKEN" ]; then
            echo "Warning: HTTPS URL detected but no OBSIDIAN_VAULT_GIT_TOKEN set."
            echo "For private repositories, either:"
            echo "  1. Set OBSIDIAN_VAULT_GIT_TOKEN environment variable (GitHub personal access token)"
            echo "  2. Use SSH URL format: git@github.com:user/repo.git (requires SSH keys)"
            echo "  3. Embed token in URL: https://token@github.com/user/repo.git"
        fi
    fi
    
    if [ -d "$VAULT_SOURCE_DIR/.git" ]; then
        # Repository already exists, pull updates
        echo "Updating existing repository..."
        cd "$VAULT_SOURCE_DIR"
        
        # Update remote URL if token was provided
        if [ -n "$OBSIDIAN_VAULT_GIT_TOKEN" ] && [[ "$OBSIDIAN_VAULT_LINK" =~ ^https:// ]]; then
            git remote set-url origin "$GIT_URL" 2>/dev/null || true
        fi
        
        git pull || {
            echo "Warning: git pull failed, attempting to reset and pull"
            git fetch origin || {
                echo "Error: Failed to fetch from repository. Check authentication."
                exit 1
            }
            git reset --hard origin/$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
        }
    else
        # Clone the repository
        echo "Cloning repository to $VAULT_SOURCE_DIR..."
        rm -rf "$VAULT_SOURCE_DIR"
        git clone "$GIT_URL" "$VAULT_SOURCE_DIR" || {
            echo "Error: Failed to clone repository: $OBSIDIAN_VAULT_LINK"
            echo "For private repositories, ensure:"
            echo "  - OBSIDIAN_VAULT_GIT_TOKEN is set (for HTTPS)"
            echo "  - SSH keys are configured (for git@ URLs)"
            exit 1
        }
    fi
    
    VAULT_SOURCE="$VAULT_SOURCE_DIR"
else
    # It's a local directory path
    VAULT_SOURCE="$OBSIDIAN_VAULT_LINK"
    
    # Check if source vault exists
    if [ ! -d "$VAULT_SOURCE" ]; then
        echo "Error: Vault directory not found: $VAULT_SOURCE"
        exit 1
    fi
fi

echo "Starting Obsidian Vault Sync Service"
echo "Source: $VAULT_SOURCE"
echo "Target: $VAULT_TARGET"

# Create target directory if it doesn't exist
mkdir -p "$VAULT_TARGET"

# Sync function
sync_vault() {
    # If using Git, update the repository first
    if [[ "$OBSIDIAN_VAULT_LINK" =~ ^(https?://|git@) ]] && [ -d "$VAULT_SOURCE_DIR/.git" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Updating Git repository..."
        cd "$VAULT_SOURCE_DIR"
        
        # Update remote URL if token was provided (in case it changed)
        if [ -n "$OBSIDIAN_VAULT_GIT_TOKEN" ] && [[ "$OBSIDIAN_VAULT_LINK" =~ ^https:// ]]; then
            GIT_URL="$OBSIDIAN_VAULT_LINK"
            if [[ "$OBSIDIAN_VAULT_LINK" =~ ^https://([^/@]+@)?([^/]+)/(.+)$ ]]; then
                GIT_URL="https://${OBSIDIAN_VAULT_GIT_TOKEN}@${BASH_REMATCH[2]}/${BASH_REMATCH[3]}"
            fi
            git remote set-url origin "$GIT_URL" 2>/dev/null || true
        fi
        
        git pull || {
            echo "Warning: git pull failed, continuing with existing state"
        }
    fi
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Syncing vault..."
    
    # Use rsync for efficient sync
    # -a: archive mode (preserves permissions, timestamps, etc.)
    # -v: verbose
    # --delete: remove files in target that don't exist in source
    # --exclude: ignore Obsidian's config and cache, and Git files
    rsync -av --delete \
        --exclude='.obsidian/' \
        --exclude='.trash/' \
        --exclude='.DS_Store' \
        --exclude='.git/' \
        --exclude='.gitignore' \
        "$VAULT_SOURCE/" "$VAULT_TARGET/"
    
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
