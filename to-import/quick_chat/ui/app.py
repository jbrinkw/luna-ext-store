"""Streamlit Chat Interface with Agent and MCP Server Selection.

A chat interface that supports:
1. Agent Mode: Discovers Luna agents and uses them with MCP server tools
2. MCP Mode: Select an MCP server and use standard LangChain ReAct agent

Supports full chat history and memory integration.
"""
import os
import sys
import json
import time
import asyncio
import inspect
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, get_type_hints

# Ensure project root importability
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import streamlit as st

try:
    from streamlit.web.server import server
    from tornado.web import RequestHandler
except Exception:  # pragma: no cover - optional health route wiring
    server = None
    RequestHandler = None

from pydantic import BaseModel, Field, ValidationError, create_model
from langchain_core.tools import StructuredTool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.callbacks.base import BaseCallbackHandler

from core.utils.extension_discovery import discover_extensions
from core.utils.db import fetch_all_memories
from core.utils.tool_discovery import get_mcp_enabled_tools_for_server
from core.utils.llm_selector import get_chat_model


# ============================================================================
# Pydantic Models
# ============================================================================

class ToolTrace(BaseModel):
    """Record of a tool execution."""
    tool: str
    args: Optional[Dict[str, Any]] = None
    output: str
    duration_secs: Optional[float] = None


class AgentResult(BaseModel):
    """Result from agent execution."""
    final: str
    content: str
    response_time_secs: float
    traces: List[ToolTrace] = Field(default_factory=list)


# ============================================================================
# Runtime Cache
# ============================================================================

RUN_TRACES: List[ToolTrace] = []


# ============================================================================
# Agent Discovery
# ============================================================================

def discover_agents() -> Dict[str, Any]:
    """Discover all available agents in core/agents/ and presets from master_config.json.

    Returns:
        Dict mapping agent_name -> agent_module with run_agent function
    """
    agents = {}
    agents_dir = PROJECT_ROOT / 'core' / 'agents'

    # Load built-in agents
    if agents_dir.exists():
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir() or agent_dir.name.startswith('_'):
                continue

            agent_file = agent_dir / 'agent.py'
            if not agent_file.exists():
                continue

            try:
                # Import the agent module
                spec = importlib.util.spec_from_file_location(
                    f"agent_{agent_dir.name}",
                    agent_file
                )
                if not spec or not spec.loader:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Check if it has run_agent function
                if hasattr(module, 'run_agent'):
                    agents[agent_dir.name] = module

            except Exception as e:
                st.sidebar.warning(f"Failed to load {agent_dir.name}: {str(e)}")
                continue

    # Load agent presets from master_config.json
    master_config_path = PROJECT_ROOT / "core" / "master_config.json"
    if master_config_path.exists():
        try:
            master_config = json.loads(master_config_path.read_text())
            agent_presets = master_config.get("agent_presets", {})

            for preset_name, preset_config in agent_presets.items():
                if not preset_config.get("enabled", True):
                    continue

                base_agent = preset_config.get("base_agent")
                if base_agent not in agents:
                    st.sidebar.warning(f"Preset {preset_name}: base agent {base_agent} not found")
                    continue

                # Register preset using the same module as its base agent
                agents[preset_name] = agents[base_agent]

        except Exception as e:
            st.sidebar.warning(f"Failed to load agent presets: {str(e)}")

    return agents


# ============================================================================
# Memory Loading
# ============================================================================

def load_memories() -> Optional[str]:
    """Fetch all memories from database and format as string.
    
    Returns:
        Formatted memory string or None if no memories
    """
    try:
        memories = fetch_all_memories()
        if not memories:
            return None
        
        # Format as numbered list of memory contents
        memory_lines = [f"{i+1}. {mem['content']}" for i, mem in enumerate(memories)]
        return "\n".join(memory_lines)
    except Exception as e:
        st.sidebar.warning(f"Failed to load memories: {str(e)}")
        return None


# ============================================================================
# MCP Server Discovery
# ============================================================================

def load_mcp_servers() -> Dict[str, Dict[str, Any]]:
    """Load MCP servers from master_config.json.
    
    Returns:
        Dict mapping server_name -> server_config
    """
    master_config_path = PROJECT_ROOT / 'core' / 'master_config.json'
    try:
        if master_config_path.exists():
            with open(master_config_path, 'r') as f:
                master_config = json.load(f)
                return master_config.get('mcp_servers', {})
    except Exception as e:
        st.sidebar.warning(f"Failed to load MCP servers: {str(e)}")
    
    return {}


def get_mcp_server_tools(server_name: str) -> List[Any]:
    """Get tools enabled for a specific MCP server.
    
    Uses the global session manager for remote MCP tools, so no initialization needed.
    
    Args:
        server_name: Name of the MCP server (e.g., "main", "smarthome")
        
    Returns:
        List of tool callables
    """
    try:
        # Simply call the tool discovery function - it will use the global session manager
        tools = get_mcp_enabled_tools_for_server(server_name=server_name)
        
        print(f"[QuickChat] Loaded {len(tools)} tools for server '{server_name}'", flush=True)
        for tool in tools:
            tool_name = getattr(tool, '__name__', 'unknown')
            print(f"[QuickChat]   - {tool_name}", flush=True)
        return tools
    except Exception as e:
        error_msg = f"Failed to load tools for {server_name}: {str(e)}"
        print(f"[QuickChat] ERROR: {error_msg}", flush=True)
        import traceback
        traceback.print_exc()
        st.error(error_msg)
        return []


# ============================================================================
# Tool Wrapping for LangChain
# ============================================================================

def wrap_tool_as_structured_tool(fn) -> StructuredTool:
    """Wrap a callable as a LangChain StructuredTool with Pydantic validation.
    
    Args:
        fn: Callable tool function
        
    Returns:
        StructuredTool instance
    """
    # Get docstring for description
    try:
        full_doc = inspect.getdoc(fn) or ""
    except Exception:
        full_doc = ""
    
    if full_doc.strip():
        description = full_doc.strip()
    else:
        description = fn.__name__
    
    # Build Pydantic schema for structured args
    sig = inspect.signature(fn)
    fields: Dict[str, Tuple[Any, Any]] = {}
    try:
        hints = get_type_hints(fn, globalns=getattr(fn, "__globals__", {}))
    except Exception:
        hints = {}
    
    for name, param in sig.parameters.items():
        ann = hints.get(name, (param.annotation if param.annotation is not inspect._empty else str))
        default = param.default if param.default is not inspect._empty else ...
        fields[name] = (ann, default)
    
    ArgsSchema = create_model(f"{fn.__name__}Args", **fields)
    
    def runner(**kwargs):
        """Runner with Pydantic validation and tracing."""
        try:
            t0 = time.perf_counter()
            
            # Pydantic validation
            try:
                validated_args = ArgsSchema(**kwargs)
                validated_kwargs = validated_args.model_dump()
            except ValidationError as ve:
                raise ValueError(f"Validation error: {ve}")
            
            result = fn(**validated_kwargs)
            
            # Normalize result to string
            if isinstance(result, BaseModel):
                try:
                    sres = json.dumps(result.model_dump(), ensure_ascii=False)
                except Exception:
                    sres = str(result)
            elif isinstance(result, (dict, list)):
                try:
                    sres = json.dumps(result, ensure_ascii=False)
                except Exception:
                    sres = str(result)
            else:
                sres = str(result)
            
            dur = time.perf_counter() - t0
            RUN_TRACES.append(ToolTrace(tool=fn.__name__, args=(kwargs or None), output=sres, duration_secs=dur))
            return sres
        
        except Exception as e:
            error_msg = f"Error running tool {fn.__name__}: {str(e)}"
            dur = time.perf_counter() - t0
            RUN_TRACES.append(ToolTrace(tool=fn.__name__, args=(kwargs or None), output=error_msg, duration_secs=dur))
            return error_msg
    
    return StructuredTool(name=fn.__name__, description=description, args_schema=ArgsSchema, func=runner)


# ============================================================================
# MCP ReAct Agent Runner
# ============================================================================

async def run_mcp_react_agent(
    user_prompt: str,
    mcp_server_name: str,
    chat_history: Optional[str] = None,
    memory: Optional[str] = None
) -> AgentResult:
    """Run a standard LangChain ReAct agent with MCP server tools.
    
    Args:
        user_prompt: The user's prompt/query
        mcp_server_name: Name of the MCP server to use
        chat_history: Optional chat history context
        memory: Optional memory context
        
    Returns:
        AgentResult with final response and execution details
    """
    # Clear traces for this run
    del RUN_TRACES[:]
    
    # Load tools for the selected MCP server
    try:
        raw_tools = get_mcp_server_tools(mcp_server_name)
        if not raw_tools:
            msg = f"No tools found for MCP server '{mcp_server_name}'"
            return AgentResult(final=msg, content=msg, response_time_secs=0.0, traces=[])
        
        # Wrap tools as StructuredTools
        tools = [wrap_tool_as_structured_tool(tool) for tool in raw_tools]
    except Exception as e:
        msg = f"Error loading tools: {str(e)}"
        return AgentResult(final=msg, content=msg, response_time_secs=0.0, traces=[])
    
    # Build model with tools bound
    try:
        model = get_chat_model(
            role="domain",
            model=os.getenv("LLM_DEFAULT_MODEL", "gpt-4o-mini"),
            temperature=0.0
        )
        model_with_tools = model.bind_tools(tools)
    except Exception as e:
        msg = f"Error building agent with tools: {str(e)}"
        return AgentResult(final=msg, content=msg, response_time_secs=0.0, traces=[])
    
    # Prepare messages
    messages: List[Any] = []
    
    # System prompt
    sys_parts = [
        f"You are a helpful assistant with access to tools from the '{mcp_server_name}' MCP server.",
        "Use tools when appropriate to help the user."
    ]
    messages.append(SystemMessage(content="\n\n".join(sys_parts)))
    
    # Add context if available
    if chat_history or memory:
        context_parts = []
        if chat_history:
            context_parts.append(f"Chat history:\n{chat_history}")
        if memory:
            context_parts.append(f"Memory:\n{memory}")
        messages.append(SystemMessage(content="Conversation context to consider when responding.\n" + "\n\n".join(context_parts)))
    
    messages.append(HumanMessage(content=user_prompt))
    
    # Agent loop with tool calling
    t0 = time.perf_counter()
    max_iterations = 16
    
    try:
        for iteration in range(max_iterations):
            # Invoke model
            response = await model_with_tools.ainvoke(messages)
            messages.append(response)
            
            # Check if model wants to call tools
            tool_calls = getattr(response, "tool_calls", None) or []
            
            if not tool_calls:
                # No tool calls, we have final response
                break
            
            # Execute tool calls
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", "")
                
                # Find and execute tool
                tool_found = None
                for tool in tools:
                    if tool.name == tool_name:
                        tool_found = tool
                        break
                
                if tool_found:
                    try:
                        result = await tool_found.ainvoke(tool_args)
                        tool_result = str(result)
                    except Exception as e:
                        tool_result = f"Error executing tool {tool_name}: {str(e)}"
                else:
                    tool_result = f"Tool {tool_name} not found"
                
                # Add tool result to messages
                messages.append(ToolMessage(content=tool_result, tool_call_id=tool_id))
        
        elapsed = time.perf_counter() - t0
        
        # Extract final content from last AI message
        final_text = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                content = getattr(msg, "content", "")
                if isinstance(content, str) and content.strip():
                    final_text = content
                    break
        
        if not final_text:
            final_text = "No response generated"
    
    except Exception as e:
        elapsed = time.perf_counter() - t0
        final_text = f"Error during agent execution: {str(e)}"
    
    # Assemble response
    traces = list(RUN_TRACES)
    
    return AgentResult(
        final=final_text,
        content=final_text,
        response_time_secs=float(elapsed),
        traces=traces
    )


# ============================================================================
# Tool Loading
# ============================================================================

def load_mcp_tools() -> Dict[str, Any]:
    """Load all MCP-enabled tools from enabled extensions only.
    
    Returns:
        Dict with tool metadata organized by extension
    """
    extensions = discover_extensions()
    tool_metadata = {}
    
    # Load master_config to check enabled state
    master_config_path = PROJECT_ROOT / 'core' / 'master_config.json'
    enabled_extensions = set()
    try:
        if master_config_path.exists():
            with open(master_config_path, 'r') as f:
                master_config = json.load(f)
                for ext_name, ext_config in master_config.get('extensions', {}).items():
                    if ext_config.get('enabled', True):
                        enabled_extensions.add(ext_name)
    except Exception:
        # If we can't load config, expose all extensions
        enabled_extensions = {ext.get('name') for ext in extensions}
    
    for ext in extensions:
        ext_name = ext.get('name', 'unknown')
        
        # Skip disabled extensions
        if ext_name not in enabled_extensions:
            continue
            
        tools = ext.get('tools', [])
        tool_configs = ext.get('tool_configs', {})
        
        for tool_fn in tools:
            tool_name = getattr(tool_fn, '__name__', '')
            tool_config = tool_configs.get(tool_name, {})
            
            # Only include MCP-enabled tools
            if not tool_config.get('enabled_in_mcp', False):
                continue
            
            # Get tool documentation
            tool_doc = getattr(tool_fn, '__doc__', '') or f"Tool: {tool_name}"
            
            tool_metadata[tool_name] = {
                'extension': ext_name,
                'description': tool_doc.strip().split('\n')[0],
                'enabled_in_mcp': True,
                'passthrough': tool_config.get('passthrough', False),
                'full_doc': tool_doc.strip()
            }
    
    return tool_metadata


# ============================================================================
# Streamlit UI
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "tool_metadata" not in st.session_state:
        st.session_state.tool_metadata = {}
    if "agents" not in st.session_state:
        st.session_state.agents = {}
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent = None
    if "mode" not in st.session_state:
        st.session_state.mode = "agent"  # "agent" or "mcp"
    if "mcp_servers" not in st.session_state:
        st.session_state.mcp_servers = {}
    if "selected_mcp_server" not in st.session_state:
        st.session_state.selected_mcp_server = None
    if "mcp_session_manager" not in st.session_state:
        st.session_state.mcp_session_manager = None


def refresh_tools_and_agents():
    """Refresh MCP tools, agents, and MCP servers."""
    with st.spinner("Loading agents, MCP servers, and tools..."):
        # Load tools
        st.session_state.tool_metadata = load_mcp_tools()
        
        # Discover agents
        st.session_state.agents = discover_agents()
        
        # Load MCP servers
        st.session_state.mcp_servers = load_mcp_servers()
        
        # Set default agent if not set
        if not st.session_state.selected_agent and st.session_state.agents:
            st.session_state.selected_agent = list(st.session_state.agents.keys())[0]
        
        # Set default MCP server if not set
        if not st.session_state.selected_mcp_server and st.session_state.mcp_servers:
            st.session_state.selected_mcp_server = list(st.session_state.mcp_servers.keys())[0]


def ensure_healthcheck_route() -> None:
    """Expose GET /healthz for Hub health probes."""
    if server is None or RequestHandler is None:
        return

    try:
        current_server = server.Server.get_current()
    except Exception:
        return

    if not current_server or not hasattr(current_server, "_http_server"):
        return

    if getattr(current_server, "_quick_chat_healthz_registered", False):
        return

    class _HealthzHandler(RequestHandler):
        def get(self):  # type: ignore[override]
            self.set_header("Cache-Control", "no-store")
            self.set_header("Content-Type", "text/plain; charset=utf-8")
            self.write("ok")

    try:
        current_server._http_server.add_handlers(  # type: ignore[attr-defined]
            r".*",
            [(r"/healthz", _HealthzHandler)],
        )
        setattr(current_server, "_quick_chat_healthz_registered", True)
    except Exception:
        # If we cannot register the handler we fail silently; the Hub will mark
        # the UI unhealthy, which is preferable to crashing user sessions.
        pass


def render_sidebar():
    """Render the sidebar with mode selector, agent/MCP server selector, tool list and controls."""
    st.sidebar.title("Luna Chat")
    
    # Mode selector
    st.sidebar.subheader("Mode")
    mode_options = {
        "agent": "Agent Mode",
        "mcp": "MCP Mode"
    }
    current_mode_idx = list(mode_options.keys()).index(st.session_state.mode)
    
    selected_mode = st.sidebar.radio(
        "Select Mode",
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        index=current_mode_idx,
        key="mode_selector"
    )
    
    if selected_mode != st.session_state.mode:
        st.session_state.mode = selected_mode
        st.rerun()
    
    st.sidebar.divider()
    
    # Agent or MCP Server selector based on mode
    if st.session_state.mode == "agent":
        # Agent selector
        st.sidebar.subheader("Agent")
        if st.session_state.agents:
            agent_names = list(st.session_state.agents.keys())
            current_idx = 0
            if st.session_state.selected_agent in agent_names:
                current_idx = agent_names.index(st.session_state.selected_agent)
            
            selected = st.sidebar.selectbox(
                "Select Active Agent",
                agent_names,
                index=current_idx,
                key="agent_selector"
            )
            
            if selected != st.session_state.selected_agent:
                st.session_state.selected_agent = selected
                st.rerun()
            
            # Show agent info
            st.sidebar.caption(f"Using: **{st.session_state.selected_agent}**")
        else:
            st.sidebar.warning("No agents found")
    
    else:  # MCP mode
        # MCP Server selector
        st.sidebar.subheader("MCP Server")
        if st.session_state.mcp_servers:
            server_names = list(st.session_state.mcp_servers.keys())
            current_idx = 0
            if st.session_state.selected_mcp_server in server_names:
                current_idx = server_names.index(st.session_state.selected_mcp_server)
            
            selected = st.sidebar.selectbox(
                "Select MCP Server",
                server_names,
                index=current_idx,
                key="mcp_server_selector"
            )
            
            if selected != st.session_state.selected_mcp_server:
                st.session_state.selected_mcp_server = selected
                st.rerun()
            
            # Show MCP server info
            server_config = st.session_state.mcp_servers.get(st.session_state.selected_mcp_server, {})
            st.sidebar.caption(f"Using: **{st.session_state.selected_mcp_server}**")
            st.sidebar.caption(f"Port: {server_config.get('port', 'N/A')}")
            st.sidebar.caption(f"Enabled: {server_config.get('enabled', False)}")
        else:
            st.sidebar.warning("No MCP servers found")
    
    st.sidebar.divider()
    
    # Refresh button
    if st.sidebar.button("Refresh All", use_container_width=True):
        refresh_tools_and_agents()
        success_msg = (
            f"Loaded {len(st.session_state.agents)} agents, "
            f"{len(st.session_state.mcp_servers)} MCP servers, and "
            f"{len(st.session_state.tool_metadata)} tools."
        )
        st.sidebar.success(success_msg)
    
    st.sidebar.divider()
    
    # Display tools by extension
    st.sidebar.subheader("MCP Tools")
    if not st.session_state.tool_metadata:
        st.sidebar.info("No MCP tools found. Click 'Refresh All' to load.")
    else:
        # Group by extension
        by_extension = {}
        for tool_name, metadata in st.session_state.tool_metadata.items():
            ext = metadata['extension']
            if ext not in by_extension:
                by_extension[ext] = []
            by_extension[ext].append((tool_name, metadata))
        
        # Display each extension
        for ext_name, tool_list in sorted(by_extension.items()):
            with st.sidebar.expander(f"{ext_name} ({len(tool_list)})", expanded=False):
                for tool_name, metadata in sorted(tool_list):
                    st.markdown(f"**`{tool_name}`**")
                    st.caption(metadata['description'][:100] + "..." if len(metadata['description']) > 100 else metadata['description'])
                    st.markdown("---")


def render_chat():
    """Render the main chat interface."""
    # Header with current mode and selection
    st.title("Luna Chat")
    
    if st.session_state.mode == "agent":
        agent_name = st.session_state.selected_agent or "No Agent"
        st.caption(f"**Agent Mode** - Using **{agent_name}** agent")
    else:
        mcp_server = st.session_state.selected_mcp_server or "No MCP Server"
        st.caption(f"**MCP Mode** - Using **{mcp_server}** MCP server with LangChain ReAct agent")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "user":
                with st.chat_message("user"):
                    st.markdown(content)
            elif role == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(content)
                    
                    # Show traces if available
                    if "traces" in msg and msg["traces"]:
                        with st.expander("Tool Calls", expanded=False):
                            for trace in msg["traces"]:
                                st.json(trace)
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Build chat history context
        chat_history_lines = []
        for msg in st.session_state.messages[:-1]:  # Exclude current prompt
            if msg["role"] == "user":
                chat_history_lines.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                chat_history_lines.append(f"Assistant: {msg['content']}")
        
        chat_history_str = "\n".join(chat_history_lines) if chat_history_lines else None
        
        # Load memories from database
        memory_str = load_memories()
        
        # Handle based on mode
        if st.session_state.mode == "agent":
            # Agent Mode
            if not st.session_state.selected_agent or not st.session_state.agents:
                with st.chat_message("assistant"):
                    error_msg = "No agent available. Please select an agent from the sidebar."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                return
            
            # Get selected agent module
            agent_module = st.session_state.agents[st.session_state.selected_agent]
            
            # Process with agent
            with st.chat_message("assistant"):
                with st.spinner(f"{st.session_state.selected_agent} is thinking..."):
                    try:
                        # Run agent (async)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(
                                agent_module.run_agent(
                                    user_prompt=prompt,
                                    chat_history=chat_history_str,
                                    memory=memory_str,
                                    tool_root=None
                                )
                            )
                        finally:
                            loop.close()
                        
                        # Extract response
                        response_text = result.final if hasattr(result, 'final') else str(result)
                        traces = result.traces if hasattr(result, 'traces') else []
                        
                        # Display response
                        st.markdown(response_text)
                        
                        # Show timing if available
                        if hasattr(result, 'response_time_secs'):
                            st.caption(f"Response time: {result.response_time_secs:.2f}s")
                        
                        # Save to history
                        msg_data = {
                            "role": "assistant",
                            "content": response_text
                        }
                        
                        if traces:
                            msg_data["traces"] = [
                                {
                                    "tool": t.tool,
                                    "args": t.args,
                                    "output": t.output[:200] + "..." if len(t.output) > 200 else t.output,
                                    "duration": t.duration_secs
                                }
                                for t in traces
                            ]
                        
                        st.session_state.messages.append(msg_data)
                        
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
        
        else:
            # MCP Mode
            if not st.session_state.selected_mcp_server or not st.session_state.mcp_servers:
                with st.chat_message("assistant"):
                    error_msg = "No MCP server available. Please select an MCP server from the sidebar."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                return
            
            # Process with MCP ReAct agent
            with st.chat_message("assistant"):
                with st.spinner(f"MCP ReAct agent is thinking..."):
                    try:
                        # Run MCP ReAct agent (async)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(
                                run_mcp_react_agent(
                                    user_prompt=prompt,
                                    mcp_server_name=st.session_state.selected_mcp_server,
                                    chat_history=chat_history_str,
                                    memory=memory_str
                                )
                            )
                        finally:
                            loop.close()
                        
                        # Extract response
                        response_text = result.final
                        traces = result.traces
                        
                        # Display response
                        st.markdown(response_text)
                        
                        # Show timing
                        st.caption(f"Response time: {result.response_time_secs:.2f}s")
                        
                        # Save to history
                        msg_data = {
                            "role": "assistant",
                            "content": response_text
                        }
                        
                        if traces:
                            msg_data["traces"] = [
                                {
                                    "tool": t.tool,
                                    "args": t.args,
                                    "output": t.output[:200] + "..." if len(t.output) > 200 else t.output,
                                    "duration": t.duration_secs
                                }
                                for t in traces
                            ]
                        
                        st.session_state.messages.append(msg_data)
                        
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Luna Chat",
        page_icon="Luna",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    ensure_healthcheck_route()
    
    # Initialize
    init_session_state()
    
    # Auto-load on first run
    if not st.session_state.agents and "first_load" not in st.session_state:
        refresh_tools_and_agents()
        st.session_state.first_load = True
    
    # Render UI
    render_sidebar()
    render_chat()
    
    # Footer
    st.sidebar.divider()
    
    # Show memory count
    try:
        memories = fetch_all_memories()
        memory_count = len(memories) if memories else 0
        st.sidebar.caption(f"Memories: {memory_count}")
    except Exception:
        st.sidebar.caption("Memories: N/A")
    
    st.sidebar.caption(f"Messages: {len(st.session_state.messages)}")
    st.sidebar.caption(f"Agents: {len(st.session_state.agents)}")
    st.sidebar.caption(f"MCP Servers: {len(st.session_state.mcp_servers)}")
    st.sidebar.caption(f"Tools: {len(st.session_state.tool_metadata)}")
    
    if st.sidebar.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    main()
