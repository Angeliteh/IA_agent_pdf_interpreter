"""
Pydantic models for PDF Chat Bot API
Defines request/response schemas for all endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    ERROR = "error"

# Base Models
class APIResponse(BaseModel):
    """Base response model for all API endpoints"""
    success: bool
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(APIResponse):
    """Error response model"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# Session Models
class SessionCreate(BaseModel):
    """Request model for creating a new session"""
    session_name: Optional[str] = Field(None, description="Optional name for the session")
    timeout_minutes: Optional[int] = Field(30, description="Session timeout in minutes")

class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    session_name: Optional[str]
    status: SessionStatus
    created_at: datetime
    last_activity: datetime
    duration_minutes: float
    has_pdf: bool
    message_count: int
    total_tokens_used: int

class SessionResponse(APIResponse):
    """Response model for session operations"""
    session: Optional[SessionInfo] = None

class SessionListResponse(APIResponse):
    """Response model for listing sessions"""
    sessions: List[SessionInfo] = []
    total_count: int = 0

# PDF Models
class PDFInfo(BaseModel):
    """PDF information model"""
    filename: str
    file_size: int
    num_pages: int
    content_length: int
    estimated_tokens: int
    extraction_method: str  # "text" or "ocr"
    uploaded_at: datetime

class PDFUploadResponse(APIResponse):
    """Response model for PDF upload"""
    pdf_info: Optional[PDFInfo] = None

# Chat Models
class ChatMessage(BaseModel):
    """Individual chat message model"""
    role: MessageRole
    content: str
    timestamp: datetime
    token_count: Optional[int] = None

class ChatRequest(BaseModel):
    """Request model for sending a chat message"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")

class TokenInfo(BaseModel):
    """Token usage information"""
    message_tokens: int
    pdf_tokens: int
    history_tokens: int
    response_tokens: int
    total_exchange_tokens: int
    session_total_tokens: int
    gemini_usage_percentage: float

class ChatResponse(APIResponse):
    """Response model for chat messages"""
    response: Optional[str] = None
    token_info: Optional[TokenInfo] = None
    session_info: Optional[SessionInfo] = None

class ChatHistoryResponse(APIResponse):
    """Response model for chat history"""
    messages: List[ChatMessage] = []
    total_messages: int = 0
    session_info: Optional[SessionInfo] = None

# Statistics Models
class SessionStats(BaseModel):
    """Detailed session statistics"""
    session_id: str
    session_info: SessionInfo
    pdf_info: Optional[PDFInfo]
    token_usage: Dict[str, Any]
    conversation_stats: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]

class SessionStatsResponse(APIResponse):
    """Response model for session statistics"""
    stats: Optional[SessionStats] = None

class SystemHealth(BaseModel):
    """System health information"""
    status: str
    timestamp: datetime
    active_sessions: int
    total_sessions_created: int
    gemini_api_status: bool
    ocr_api_status: bool
    system_info: Dict[str, Any]

class HealthResponse(APIResponse):
    """Response model for system health"""
    health: Optional[SystemHealth] = None

# File Upload Models
class FileUploadInfo(BaseModel):
    """File upload information"""
    filename: str
    content_type: str
    file_size: int

# Validation Models
class SessionValidation(BaseModel):
    """Session validation result"""
    is_valid: bool
    exists: bool
    is_expired: bool
    has_pdf: bool
    error_message: Optional[str] = None

# Configuration Models
class APIConfig(BaseModel):
    """API configuration model"""
    version: str = "1.0.0"
    title: str = "PDF Chat Bot API"
    description: str = "REST API for PDF document chat with AI"
    max_file_size_mb: int = 10
    allowed_file_types: List[str] = [".pdf"]
    session_timeout_minutes: int = 30
    max_sessions_per_ip: int = 10
    rate_limit_per_minute: int = 60

# Error Codes
class ErrorCodes:
    """Standard error codes for the API"""
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    PDF_NOT_LOADED = "PDF_NOT_LOADED"
    PDF_UPLOAD_FAILED = "PDF_UPLOAD_FAILED"
    PDF_TOO_LARGE = "PDF_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    CHAT_FAILED = "CHAT_FAILED"
    TOKEN_LIMIT_EXCEEDED = "TOKEN_LIMIT_EXCEEDED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    GEMINI_API_ERROR = "GEMINI_API_ERROR"
    OCR_API_ERROR = "OCR_API_ERROR"

# Response Examples for Documentation
class ResponseExamples:
    """Example responses for API documentation"""
    
    SESSION_CREATED = {
        "success": True,
        "message": "Session created successfully",
        "timestamp": "2024-01-15T10:30:00Z",
        "session": {
            "session_id": "pdf_chat_20240115_103000",
            "session_name": "Document Analysis",
            "status": "active",
            "created_at": "2024-01-15T10:30:00Z",
            "last_activity": "2024-01-15T10:30:00Z",
            "duration_minutes": 0.0,
            "has_pdf": False,
            "message_count": 0,
            "total_tokens_used": 0
        }
    }
    
    PDF_UPLOADED = {
        "success": True,
        "message": "PDF uploaded and processed successfully",
        "timestamp": "2024-01-15T10:31:00Z",
        "pdf_info": {
            "filename": "document.pdf",
            "file_size": 233203,
            "num_pages": 1,
            "content_length": 1660,
            "estimated_tokens": 415,
            "extraction_method": "ocr",
            "uploaded_at": "2024-01-15T10:31:00Z"
        }
    }
    
    CHAT_RESPONSE = {
        "success": True,
        "message": "Message processed successfully",
        "timestamp": "2024-01-15T10:32:00Z",
        "response": "El número de oficio es SEPF/C.O./1999/25-26.",
        "token_info": {
            "message_tokens": 10,
            "pdf_tokens": 415,
            "history_tokens": 0,
            "response_tokens": 11,
            "total_exchange_tokens": 436,
            "session_total_tokens": 436,
            "gemini_usage_percentage": 0.044
        },
        "session_info": {
            "session_id": "pdf_chat_20240115_103000",
            "status": "active",
            "message_count": 2,
            "total_tokens_used": 436
        }
    }
    
    ERROR_RESPONSE = {
        "success": False,
        "message": "Session not found",
        "timestamp": "2024-01-15T10:33:00Z",
        "error_code": "SESSION_NOT_FOUND",
        "details": {
            "session_id": "invalid_session_id",
            "suggestion": "Create a new session using POST /api/v1/sessions"
        }
    }

# Request Examples
class RequestExamples:
    """Example requests for API documentation"""
    
    CREATE_SESSION = {
        "session_name": "Document Analysis Session",
        "timeout_minutes": 60
    }
    
    CHAT_MESSAGE = {
        "message": "¿Cuál es el número de oficio del documento?"
    }
