#!/bin/bash
# Quick Chat Extension UI Launcher
# Accepts port as $1 and launches Streamlit app

PORT=${1:-5200}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Launch Streamlit with the specified port
# Bind to localhost only for security
# Disable CORS and XSRF for local iframe embedding
exec streamlit run app.py \
    --server.port=$PORT \
    --server.address=127.0.0.1 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false \
    --server.fileWatcherType=none

