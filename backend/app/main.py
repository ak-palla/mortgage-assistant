"""
FastAPI application for Mortgage Assistant.
Handles chat endpoints with SSE streaming and lead capture.
"""

import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import AsyncGenerator
import uvicorn

from app.models import ChatRequest, ChatResponse, NewSessionResponse, LeadRequest, LeadResponse
from app.state import conversation_state
from app.agent import process_chat_with_tools, handle_tool_calls, client, TOOLS, execute_tool, validate_tool_arguments
from app.tracing import trace_groq_call


def convert_strings_to_numbers(data: dict) -> dict:
    """Convert string numbers to actual numbers/integers in tool arguments."""
    converted = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Try to convert to int first, then float
            try:
                if '.' in value:
                    converted[key] = float(value)
                else:
                    converted[key] = int(value)
            except ValueError:
                converted[key] = value  # Keep as string if conversion fails
        elif isinstance(value, dict):
            converted[key] = convert_strings_to_numbers(value)
        else:
            converted[key] = value
    return converted


def format_tool_results_response(tool_results: list) -> str:
    """
    Format tool results into a natural language response when LLM returns empty content.
    
    Args:
        tool_results: List of tool execution results
    
    Returns:
        Formatted response string
    """
    if not tool_results:
        return ""
    
    response_parts = []
    
    for tool_result in tool_results:
        tool_name = tool_result.get("tool_name", "")
        result = tool_result.get("result", {})
        
        if "error" in result:
            continue  # Skip errors, they're handled elsewhere
        
        if tool_name == "calculate_emi":
            emi = result.get("emi", 0)
            total_amount = result.get("total_amount", 0)
            total_interest = result.get("total_interest", 0)
            loan_amount = result.get("loan_amount", 0)
            tenure_years = result.get("tenure_years", 0)
            
            response_parts.append(
                f"For a loan of {loan_amount:,.0f} AED at 4.5% interest over {tenure_years} years:\n\n"
                f"• Monthly EMI: {emi:,.2f} AED\n"
                f"• Total amount payable: {total_amount:,.2f} AED\n"
                f"• Total interest: {total_interest:,.2f} AED"
            )
        
        elif tool_name == "check_ltv":
            ltv_ratio = result.get("ltv_ratio", 0)
            is_valid = result.get("is_valid", False)
            min_down_payment = result.get("min_down_payment_required", 0)
            
            if is_valid:
                response_parts.append(f"Your LTV ratio is {ltv_ratio:.1f}%, which meets UAE expat requirements (maximum 80%).")
            else:
                response_parts.append(
                    f"Your LTV ratio is {ltv_ratio:.1f}%, which exceeds the 80% limit for expats. "
                    f"You'll need a minimum down payment of {min_down_payment:,.0f} AED."
                )
        
        elif tool_name == "calculate_upfront_costs":
            total_costs = result.get("total_upfront_costs", 0)
            property_price = result.get("property_price", 0)
            
            response_parts.append(
                f"For a property worth {property_price:,.0f} AED, the upfront costs are approximately {total_costs:,.0f} AED "
                f"(7% of property price: 4% transfer fee, 2% agency fee, 1% miscellaneous)."
            )
        
        elif tool_name == "buy_vs_rent_analysis":
            recommendation = result.get("recommendation", "")
            reasoning = result.get("reasoning", [])
            emi = result.get("emi", 0)
            
            response_parts.append(f"Based on your situation, I recommend: **{recommendation}**\n\n")
            if reasoning:
                response_parts.append("\n".join([f"• {r}" for r in reasoning]))
            if emi:
                response_parts.append(f"\n\nYour estimated monthly EMI would be {emi:,.2f} AED.")
    
    return "\n\n".join(response_parts) if response_parts else ""


app = FastAPI(
    title="Mortgage Assistant API",
    description="AI-powered conversational mortgage advisor for UAE expats",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",  # Vercel frontend
        "https://*.railway.app",  # Railway domains (if needed)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mortgage-assistant"}


@app.post("/chat/new", response_model=NewSessionResponse)
async def create_new_session():
    """Create a new conversation session."""
    session_id = conversation_state.create_session()
    return NewSessionResponse(session_id=session_id)


async def stream_chat_response(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """
    Stream chat response with tool calling support.
    
    Args:
        session_id: Conversation session ID
        user_message: User's message
    """
    try:
        # Add user message to history
        conversation_state.add_message(session_id, "user", user_message)
        
        # Get conversation history
        messages = conversation_state.get_history(session_id)
        
        # Add system message if not present
        if not messages or messages[0].get("role") != "system":
            from app.agent import SYSTEM_PROMPT
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        
        full_response = ""
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        tool_results_list = []  # Collect tool results for tracing
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get response from Groq (non-streaming first to check for tool calls)
            # Trace the Groq API call
            completion = trace_groq_call(
                messages=messages,
                model="llama-3.3-70b-versatile",
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2048,
                stream=False
            )
            
            message = completion.choices[0].message
            assistant_content = message.content or ""
            
            # Debug: Log if tool calls are present
            print(f"DEBUG: Tool calls present: {bool(message.tool_calls)}", flush=True)
            if message.tool_calls:
                print(f"DEBUG: Number of tool calls: {len(message.tool_calls)}", flush=True)
            
            # Handle tool calls if present
            if message.tool_calls:
                # Send initial message if any
                if assistant_content:
                    yield f"data: {json.dumps({'type': 'content', 'content': assistant_content})}\n\n"
                    full_response += assistant_content
                
                # Filter and validate tool calls before execution
                valid_tool_calls = []
                invalid_tool_calls = []
                
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        # Convert string numbers to actual numbers (Groq sometimes returns strings)
                        arguments = convert_strings_to_numbers(arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # Validate before execution
                    is_valid, error_msg = validate_tool_arguments(tool_name, arguments)
                    
                    if is_valid:
                        valid_tool_calls.append((tool_call, tool_name, arguments))
                    else:
                        invalid_tool_calls.append((tool_call, tool_name, arguments, error_msg))
                        # Log invalid tool call for tracing
                        tool_results_list.append({
                            "tool_name": tool_name,
                            "arguments": arguments,
                            "result": {"error": error_msg, "skipped": True}
                        })
                
                # Build tool calls data for conversation history
                tool_calls_data = []
                
                # Execute valid tool calls
                for tool_call, tool_name, arguments in valid_tool_calls:
                    # Execute tool (already traced via decorator)
                    tool_result = execute_tool(tool_name, arguments)
                    
                    # Track tool result for tracing
                    tool_results_list.append({
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": tool_result
                    })
                    
                    tool_calls_data.append({
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": tool_call.function.arguments
                        }
                    })
                    
                    # Add tool result message
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })
                
                # Handle invalid tool calls - add them with error messages
                for tool_call, tool_name, arguments, error_msg in invalid_tool_calls:
                    tool_calls_data.append({
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": tool_call.function.arguments
                        }
                    })
                    
                    # Add error result for invalid tool call
                    error_result = {"error": error_msg, "skipped": True}
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(error_result)
                    })
                
                # Add assistant message with all tool calls (valid and invalid) to conversation history
                if tool_calls_data:
                    messages.append({
                        "role": "assistant",
                        "content": assistant_content,
                        "tool_calls": tool_calls_data
                    })
                
                # Continue loop to get final response after tool execution
                continue
            else:
                # No tool calls, stream the response
                if assistant_content:
                    # Simulate streaming by sending chunks
                    chunk_size = 10
                    for i in range(0, len(assistant_content), chunk_size):
                        chunk = assistant_content[i:i+chunk_size]
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                
                # Break out of loop
                break
        
        # If we have tool results but no response, format the tool results
        if not full_response and tool_results_list:
            formatted_response = format_tool_results_response(tool_results_list)
            if formatted_response:
                # Stream the formatted response
                chunk_size = 10
                for i in range(0, len(formatted_response), chunk_size):
                    chunk = formatted_response[i:i+chunk_size]
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
        
        # Save assistant response to history
        if full_response:
            conversation_state.add_message(session_id, "assistant", full_response)
            
            # Trace the complete conversation turn
            from app.tracing import trace_conversation_turn
            trace_conversation_turn(
                session_id=session_id,
                user_message=user_message,
                agent_response=full_response,
                tool_results=tool_results_list
            )
        elif tool_results_list:
            # Even if we couldn't format, save a basic message
            basic_response = "I've calculated the information you requested. Please let me know if you need any clarification."
            conversation_state.add_message(session_id, "assistant", basic_response)
            yield f"data: {json.dumps({'type': 'content', 'content': basic_response})}\n\n"
        
        # Send done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = f"Error processing chat: {str(e)}"
        print(f"Chat error: {error_details}", flush=True)  # Log to backend
        import sys
        sys.stderr.write(f"Chat error: {error_details}\n")
        sys.stderr.flush()
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with SSE streaming.
    
    Args:
        request: Chat request with session_id and message
    
    Returns:
        SSE stream of responses
    """
    # Validate session
    if not conversation_state.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    return StreamingResponse(
        stream_chat_response(request.session_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/leads", response_model=LeadResponse)
async def capture_lead(request: LeadRequest):
    """
    Capture lead information.
    
    Args:
        request: Lead information (session_id, name, email, phone)
    
    Returns:
        Success confirmation
    """
    # Validate session
    if not conversation_state.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Prepare lead data
    lead_data = {
        "session_id": request.session_id,
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "captured_at": conversation_state.conversations[request.session_id]["created_at"]
    }
    
    # Save to JSON file
    leads_file = "leads.json"
    leads = []
    
    # Read existing leads if file exists
    if os.path.exists(leads_file):
        try:
            with open(leads_file, "r") as f:
                leads = json.load(f)
        except (json.JSONDecodeError, IOError):
            leads = []
    
    # Append new lead
    leads.append(lead_data)
    
    # Write back to file
    try:
        with open(leads_file, "w") as f:
            json.dump(leads, f, indent=2)
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save lead: {str(e)}")
    
    return LeadResponse(
        success=True,
        message="Lead captured successfully"
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
