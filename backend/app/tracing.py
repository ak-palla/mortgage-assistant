"""
LangSmith tracing setup for agent and tool calling.
Provides observability and proof of tool execution for assignment evaluation.
"""

import os
from functools import wraps
from typing import Any, Dict, Callable
import json

# Try to import LangSmith, but make it optional
try:
    from langsmith import traceable, Client
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    # Create a no-op decorator if LangSmith is not available
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Initialize LangSmith client if available
langsmith_client = None
if LANGSMITH_AVAILABLE and os.getenv("LANGSMITH_API_KEY"):
    try:
        langsmith_client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))
    except Exception:
        langsmith_client = None


def trace_tool_execution(tool_name: str):
    """
    Decorator to trace tool execution in LangSmith.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if LANGSMITH_AVAILABLE and langsmith_client:
                try:
                    # Use @traceable decorator for proper tracing
                    @traceable(name=f"tool_{tool_name}", run_type="tool")
                    def _execute():
                        return func(*args, **kwargs)
                    
                    return _execute()
                except Exception as e:
                    # Log error but continue execution
                    print(f"LangSmith tracing error for {tool_name}: {e}", flush=True)
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def trace_groq_call(messages: list, model: str, tools: list = None, **kwargs) -> Any:
    """
    Wrapper to trace Groq API calls.
    This function is called by the agent to log all LLM interactions.
    """
    from app.agent import client
    
    if not LANGSMITH_AVAILABLE:
        # Fallback to direct call if LangSmith not available
        return client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            **kwargs
        )
    
    # Use traceable decorator
    @traceable(name="groq_chat_completion", run_type="llm")
    def _make_call():
        return client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            **kwargs
        )
    
    return _make_call()


def trace_conversation_turn(session_id: str, user_message: str, agent_response: str, tool_results: list = None):
    """
    Trace a complete conversation turn including tool executions.
    
    Args:
        session_id: Conversation session ID
        user_message: User's input message
        agent_response: Agent's final response
        tool_results: List of tool execution results
    """
    if not LANGSMITH_AVAILABLE:
        return
    
    @traceable(name="agent_conversation", run_type="chain")
    def _trace():
        return {
            "session_id": session_id,
            "user_message": user_message,
            "agent_response": agent_response,
            "tools_used": tool_results or [],
            "tool_count": len(tool_results) if tool_results else 0
        }
    
    _trace()
