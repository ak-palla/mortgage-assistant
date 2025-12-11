"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    session_id: str = Field(..., description="Conversation session ID")
    message: str = Field(..., min_length=1, description="User message")


class ChatResponse(BaseModel):
    """Response model for chat endpoint (non-streaming)."""
    session_id: str
    response: str


class NewSessionResponse(BaseModel):
    """Response model for new session creation."""
    session_id: str


class LeadRequest(BaseModel):
    """Request model for lead capture."""
    session_id: str
    name: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=1)


class LeadResponse(BaseModel):
    """Response model for lead capture."""
    success: bool
    message: str
