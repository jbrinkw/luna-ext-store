# Quick Chat Extension

A lightweight chat interface for Luna that provides quick access to all Luna agents or MCP servers with a standard LangChain ReAct agent.

## Features

- **Dual Mode Support**:
  - **Agent Mode**: Choose from all available Luna agents
  - **MCP Mode**: Select an MCP server and use a standard LangChain ReAct agent
- **MCP Server Selection**: Choose from configured MCP servers (main, smarthome, etc.)
- **MCP Tools**: Automatically discovers and displays all MCP-enabled tools from active extensions
- **Chat History**: Maintains conversation context within the session
- **Memory Integration**: Loads and uses stored memories from the database
- **Tool Traces**: View detailed tool execution traces for debugging
- **Real-time Refresh**: Reload agents, MCP servers, and tools without restarting

## Usage

### Agent Mode
1. Select "Agent Mode" from the sidebar
2. Choose an agent from the dropdown
3. View available MCP tools organized by extension
4. Type your message in the chat input
5. The selected agent will process your request using available tools

### MCP Mode
1. Select "MCP Mode" from the sidebar
2. Choose an MCP server from the dropdown (e.g., "main", "smarthome")
3. View MCP server details (port, enabled status)
4. Type your message in the chat input
5. The LangChain ReAct agent will process your request using tools from the selected MCP server

## UI Components

- **Mode Selector**: Toggle between Agent Mode and MCP Mode
- **Agent Selector** (Agent Mode): Choose which Luna agent to use
- **MCP Server Selector** (MCP Mode): Choose which MCP server to use
- **Tool Browser**: Browse all available MCP tools by extension
- **Chat Interface**: Full-featured chat with message history
- **Refresh Button**: Reload agents, MCP servers, and tools dynamically
- **Clear Chat**: Reset conversation history
- **Statistics Footer**: Shows counts for memories, messages, agents, MCP servers, and tools

## Technical Details

- Built with Streamlit
- Discovers agents from `core/agents/` directory
- Loads MCP servers from `master_config.json`
- Uses `get_mcp_enabled_tools_for_server()` to load server-specific tools
- LangChain ReAct agent with `bind_tools()` for MCP mode
- Loads MCP-enabled tools from all active extensions
- UI-only embedded extension (ships no custom MCP tools)
- Integrates with Luna's memory system via database
- Async agent execution support
- Pydantic validation for tool arguments
- Exposes health check endpoint for supervisor monitoring
