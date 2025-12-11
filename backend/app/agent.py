"""
Groq AI agent with function calling support.
Handles conversation with mortgage advisor persona and tool execution.
"""

import os
import json
from typing import List, Dict, Any, Optional
from groq import Groq
from app.tools import (
    calculate_emi,
    check_ltv,
    calculate_upfront_costs,
    buy_vs_rent_analysis
)
from app.tracing import trace_groq_call, trace_conversation_turn


# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# System prompt for the mortgage advisor
SYSTEM_PROMPT = """You are a friendly and empathetic mortgage advisor helping expats in the UAE navigate the property market. 
Your goal is to act like a "Smart Friend," not a calculator.

Key principles:
- Be conversational and natural, not robotic
- Ask questions unobtrusively to gather information (income, property price, down payment, tenure, stay duration)
- Show empathy for the user's concerns about hidden fees and being "locked in"
- MANDATORY: When the user asks about ANY calculation (EMI, payments, costs, LTV, buy vs rent), you MUST use the appropriate tool - NEVER calculate manually
- When you need to calculate numbers, AUTOMATICALLY use the available tools - never mention function calls or tool names in your response
- Never calculate numbers yourself - always use tools for accuracy
- IMPORTANT: When calling tools, provide numeric parameters as NUMBERS (not strings). For example: {"property_price": 3000000} not {"property_price": "3000000"}
- Present calculation results naturally in your conversation
- Warn users about upfront costs (7% of property price)
- Guide them through the buy vs rent decision naturally
- At the end of a helpful conversation, naturally suggest they provide contact details for personalized assistance
- CRITICAL: After tool execution, you MUST always provide a conversational response explaining the results. Never leave the user without a response.

CRITICAL RULES FOR TOOL USAGE:
- If user asks about EMI, monthly payments, or loan calculations → USE calculate_emi tool
- If user mentions property price and down payment → USE check_ltv tool
- If user asks about upfront costs or hidden fees → USE calculate_upfront_costs tool
- If user asks about buying vs renting → USE buy_vs_rent_analysis tool
- ONLY call tools when you have ALL required parameters with valid, non-zero values
- If ANY required parameter is missing or unknown, ask the user for it FIRST before calling any tools
- NEVER call tools with default values (like 0) or placeholder values - this produces invalid results
- For deterministic, fact-based analysis (like buy vs rent), you MUST have complete data
- Check what information you have, identify what's missing for the tool you want to use, ask for missing parameters, THEN call the tool
- Never show function call syntax like <function=...> in your responses
- Just call the tools silently and present the results conversationally
- ALWAYS respond with a message after tool execution - explain the results in a friendly, helpful way"""


# Define tools (functions) available to the agent
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_emi",
            "description": "Calculate Equated Monthly Installment (EMI) for a mortgage loan. ALWAYS use this tool when the user asks about monthly payments, EMI, loan installments, or mortgage payments. Use this for ANY calculation involving loan amounts, interest rates, and tenure - never calculate manually.",
            "parameters": {
                "type": "object",
                "properties": {
                    "loan_amount": {
                        "type": "number",
                        "description": "Principal loan amount in AED"
                    },
                    "interest_rate": {
                        "type": "number",
                        "description": "Annual interest rate (e.g., 4.5 for 4.5%). Default is 4.5% for UAE market."
                    },
                    "tenure_years": {
                        "type": "integer",
                        "description": "Loan tenure in years (maximum 25 years)"
                    }
                },
                "required": ["loan_amount", "tenure_years"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_ltv",
            "description": "Check Loan-to-Value (LTV) ratio and validate if the loan meets UAE expat requirements (max 80% LTV). Use this when user mentions property price and down payment. DO NOT call if property_price is missing, unknown, or zero - ask the user first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_price": {
                        "type": "number",
                        "description": "Total property price in AED (must be positive, non-zero)"
                    },
                    "down_payment": {
                        "type": "number",
                        "description": "Down payment amount in AED"
                    }
                },
                "required": ["property_price", "down_payment"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_upfront_costs",
            "description": "Calculate upfront costs for property purchase in UAE (7% total: 4% transfer fee, 2% agency fee, 1% misc). Always warn users about these hidden costs. DO NOT call if property_price is missing, unknown, or zero - ask the user first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_price": {
                        "type": "number",
                        "description": "Total property price in AED (must be positive, non-zero)"
                    }
                },
                "required": ["property_price"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buy_vs_rent_analysis",
            "description": "Analyze whether buying or renting is better based on user's situation. Use this for buy vs rent recommendations. DO NOT call if property_price is missing, unknown, or zero - ask the user first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "monthly_rent": {
                        "type": "number",
                        "description": "Current monthly rent in AED (provide as number, not string, must be positive)"
                    },
                    "property_price": {
                        "type": "number",
                        "description": "Property price in AED (provide as number, not string, must be positive and non-zero)"
                    },
                    "stay_years": {
                        "type": "integer",
                        "description": "How long the user plans to stay in the property (years, provide as integer, not string)"
                    },
                    "income": {
                        "type": "number",
                        "description": "Monthly income in AED (provide as number, not string, must be positive)"
                    },
                    "down_payment": {
                        "type": "number",
                        "description": "Available down payment in AED (provide as number, not string, must be positive)"
                    },
                    "interest_rate": {
                        "type": "number",
                        "description": "Annual interest rate (default 4.5%, provide as number, not string)"
                    }
                },
                "required": ["monthly_rent", "property_price", "stay_years", "income", "down_payment"]
            }
        }
    }
]


# Tool execution mapping
TOOL_FUNCTIONS = {
    "calculate_emi": calculate_emi,
    "check_ltv": check_ltv,
    "calculate_upfront_costs": calculate_upfront_costs,
    "buy_vs_rent_analysis": buy_vs_rent_analysis
}


def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate tool arguments before execution.
    Checks if required parameters are present and have valid values.
    
    Args:
        tool_name: Name of the tool to validate
        arguments: Arguments for the tool function
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Parameters that must be positive (non-zero)
    positive_params = {
        "calculate_emi": ["loan_amount"],
        "check_ltv": ["property_price"],
        "calculate_upfront_costs": ["property_price"],
        "buy_vs_rent_analysis": ["property_price", "monthly_rent", "income", "down_payment", "stay_years"]
    }
    
    # Required parameters per tool
    required_params = {
        "calculate_emi": ["loan_amount", "tenure_years"],
        "check_ltv": ["property_price", "down_payment"],
        "calculate_upfront_costs": ["property_price"],
        "buy_vs_rent_analysis": ["monthly_rent", "property_price", "stay_years", "income", "down_payment"]
    }
    
    if tool_name not in required_params:
        return True, ""  # Unknown tool, let execute_tool handle it
    
    # Check required parameters are present
    missing = [param for param in required_params[tool_name] if param not in arguments]
    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"
    
    # Check positive parameters are valid (non-zero, positive)
    if tool_name in positive_params:
        invalid = []
        for param in positive_params[tool_name]:
            if param in arguments:
                value = arguments[param]
                if not isinstance(value, (int, float)) or value <= 0:
                    invalid.append(f"{param} (got {value}, must be positive)")
        
        if invalid:
            return False, f"Cannot execute tool: Invalid parameter values - {', '.join(invalid)}. Please ask the user for missing information before calling this tool."
    
    return True, ""


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool function.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments for the tool function
    
    Returns:
        Result from tool execution
    """
    if tool_name not in TOOL_FUNCTIONS:
        return {"error": f"Unknown tool: {tool_name}"}
    
    # Validate arguments before execution
    is_valid, error_msg = validate_tool_arguments(tool_name, arguments)
    if not is_valid:
        return {"error": error_msg}
    
    try:
        func = TOOL_FUNCTIONS[tool_name]
        result = func(**arguments)
        return result
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}


def process_chat_with_tools(messages: List[Dict[str, str]], stream: bool = True):
    """
    Process chat with Groq, handling function calling.
    
    Args:
        messages: Conversation history
        stream: Whether to stream the response
    
    Yields:
        Response chunks (for streaming) or complete response
    """
    # Add system message if not present
    if not messages or messages[0]["role"] != "system":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    
    if stream:
        # Streaming response
        with client.chat.completions.with_streaming_response.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=1024
        ) as response:
            for chunk in response.iter_lines():
                if chunk:
                    yield chunk
    else:
        # Non-streaming response
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=2048
        )
        
        return completion


def handle_tool_calls(completion) -> tuple[str, List[Dict[str, Any]]]:
    """
    Handle tool calls from Groq response.
    
    Args:
        completion: Groq completion object
    
    Returns:
        Tuple of (assistant_message, tool_results)
    """
    message = completion.choices[0].message
    assistant_message = message.content or ""
    tool_results = []
    
    # Check if there are tool calls
    if message.tool_calls:
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
            
            # Execute the tool
            result = execute_tool(tool_name, arguments)
            
            tool_results.append({
                "tool_call_id": tool_call.id,
                "tool_name": tool_name,
                "result": result
            })
    
    return assistant_message, tool_results
