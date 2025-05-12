import os
import logging
from typing import TypedDict, Annotated, List, Dict, Any, Optional

from langchain_core.messages import SystemMessage, BaseMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition

# Import tools from your project's utils module 
from utils import tools
from prompt import system_message

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Model configuration with environment variable fallbacks
DEFAULT_MODEL = "o4-mini"
DEFAULT_TEMPERATURE = 1.0
DEFAULT_MAX_RETRIES = 2

# Initialize LLM with proper configuration handling
def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration with fallbacks to environment variables."""
    return {
        "model": os.getenv("LLM_MODEL", DEFAULT_MODEL),
        "temperature": float(os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE)),
        "max_tokens": None,
        "timeout": int(os.getenv("LLM_TIMEOUT", "600")) or None,
        "max_retries": int(os.getenv("LLM_MAX_RETRIES", DEFAULT_MAX_RETRIES)),
        "api_key": os.getenv("OPENAI_API_KEY")
    }

try:
    llm_config = get_llm_config()
    llm = ChatOpenAI(**llm_config)
    logger.info(f"Initialized LLM with model: {llm_config['model']}")
    
    # Bind system message and tools
    sys_msg = SystemMessage(content=system_message)
    llm = llm.bind_tools(tools)
except Exception as e:
    logger.error(f"Failed to initialize LLM: {str(e)}")
    raise RuntimeError(f"Agent initialization failed: {str(e)}")

class State(TypedDict):
    """State definition for the agent's graph."""
    messages: Annotated[List[BaseMessage], add_messages]

def reasoner(state: State) -> Dict[str, Any]:
    """
    Process the current state and generate a reasoned response.
    
    Args:
        state: Current state containing message history
        
    Returns:
        Updated state with new assistant messages
    """
    try:
        messages = [sys_msg] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": response}
    except Exception as e:
        logger.error(f"Reasoning error: {str(e)}")
        # Return a graceful error message that can be handled by the graph
        error_message = f"I encountered an error while processing: {str(e)}. Let me try a different approach."
        return {"messages": [SystemMessage(content=error_message)]}

# Graph definition
def create_agent_graph() -> Runnable:
    """Create and return the agent workflow graph."""
    graph_builder = StateGraph(State)
    
    # Add nodes
    graph_builder.add_node("reasoner", reasoner)
    graph_builder.add_node("tools", ToolNode(tools))
    
    # Connect nodes
    graph_builder.add_edge(START, "reasoner")
    graph_builder.add_conditional_edges("reasoner", tools_condition)
    graph_builder.add_edge("tools", "reasoner")
    
    # Compile graph
    return graph_builder.compile()

# Initialize the graph
graph = create_agent_graph()