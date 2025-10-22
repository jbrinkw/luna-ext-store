# Quick Chat Extension

A lightweight chat interface for Luna that provides quick access to all Luna agents with MCP tool support.

## Features

- **Agent Selection**: Choose from all available Luna agents
- **MCP Tools**: Automatically discovers and displays all MCP-enabled tools from active extensions
- **Chat History**: Maintains conversation context within the session
- **Memory Integration**: Loads and uses stored memories from the database
- **Tool Traces**: View detailed tool execution traces for debugging
- **Real-time Refresh**: Reload agents and tools without restarting

## Usage

1. Select an agent from the sidebar dropdown
2. View available MCP tools organized by extension
3. Type your message in the chat input
4. The selected agent will process your request using available tools
5. View tool execution traces in the expandable section below responses

## UI Components

- **Agent Selector**: Choose which Luna agent to use
- **Tool Browser**: Browse all available MCP tools by extension
- **Chat Interface**: Full-featured chat with message history
- **Refresh Button**: Reload agents and tools dynamically
- **Clear Chat**: Reset conversation history

## Technical Details

- Built with Streamlit
- Discovers agents from `core/agents/` directory
- Loads MCP-enabled tools from all active extensions
- UI-only embedded extension (ships no custom MCP tools)
- Integrates with Luna's memory system via database
- Async agent execution support
- Exposes health check endpoint for supervisor monitoring
