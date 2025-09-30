"""
PDF Chat Bot API - FastAPI Server
REST API for PDF document chat with AI using Gemini
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Local imports
from api_models import *
from pdf_chat_session import PDFChatSession, create_session, get_session, cleanup_expired_sessions, get_all_sessions
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
app_state = {
    "sessions_created": 0,
    "startup_time": None,
    "last_cleanup": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    app_state["startup_time"] = datetime.now()
    logger.info("🚀 PDF Chat Bot API starting up...")
    
    # Validate configuration
    try:
        config.validate()
        logger.info("✅ Configuration validated")
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        raise
    
    # Test API connections
    try:
        from llm_client import get_gemini_client
        client = get_gemini_client()
        if client.test_connection():
            logger.info("✅ Gemini API connection successful")
        else:
            logger.warning("⚠️ Gemini API connection failed")
    except Exception as e:
        logger.error(f"❌ Gemini API test failed: {e}")
    
    logger.info("🎉 PDF Chat Bot API ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 PDF Chat Bot API shutting down...")
    # Cleanup sessions
    cleanup_expired_sessions(0)  # Clean all sessions
    logger.info("👋 Shutdown complete")

# Create FastAPI app with enhanced documentation
app = FastAPI(
    title="PDF Chat Bot API",
    description="""
    ## 🤖 PDF Chat Bot API

    REST API for PDF document chat with AI using Gemini 2.0 Flash.

    ### 🚀 Features
    - **PDF Processing**: Upload and extract text from PDFs (OCR support)
    - **AI Chat**: Intelligent conversation about PDF content
    - **Session Management**: Robust session handling with timeouts
    - **Token Monitoring**: Real-time token usage tracking
    - **Constant Context**: PDF content injected in every message

    ### 📱 Perfect for Mobile Apps
    - **Flutter Ready**: CORS enabled, mobile-friendly responses
    - **RESTful Design**: Standard HTTP methods and status codes
    - **JSON Responses**: Consistent response format
    - **Error Handling**: Comprehensive error codes and messages

    ### 🔧 Usage Flow
    1. **Create Session**: `POST /api/v1/sessions`
    2. **Upload PDF**: `POST /api/v1/sessions/{id}/pdf`
    3. **Start Chatting**: `POST /api/v1/sessions/{id}/chat`
    4. **Monitor Usage**: `GET /api/v1/sessions/{id}/stats`

    ### 📚 Documentation
    - **Interactive Docs**: Available at `/docs` (Swagger UI)
    - **Alternative Docs**: Available at `/redoc` (ReDoc)
    - **Health Check**: Available at `/api/v1/health`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    contact={
        "name": "PDF Chat Bot API",
        "url": "https://github.com/your-repo/pdf-chat-bot",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    tags_metadata=[
        {
            "name": "sessions",
            "description": "Session management operations. Create, retrieve, and delete chat sessions.",
        },
        {
            "name": "pdf",
            "description": "PDF operations. Upload, retrieve info, and remove PDFs from sessions.",
        },
        {
            "name": "chat",
            "description": "Chat operations. Send messages, get responses, and manage conversation history.",
        },
        {
            "name": "monitoring",
            "description": "Monitoring and statistics. Get session stats and system health.",
        },
        {
            "name": "system",
            "description": "System operations. Health checks and API information.",
        }
    ]
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web interface
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency for session validation
async def get_valid_session(session_id: str) -> PDFChatSession:
    """Validate and return session"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Session not found",
                "error_code": ErrorCodes.SESSION_NOT_FOUND,
                "details": {"session_id": session_id}
            }
        )
    
    if session.is_session_expired():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={
                "success": False,
                "message": "Session expired",
                "error_code": ErrorCodes.SESSION_EXPIRED,
                "details": {"session_id": session_id}
            }
        )
    
    return session

# Web Interface
@app.get("/", response_class=FileResponse, tags=["web"])
async def web_interface():
    """
    ## Web Interface

    Serve the enhanced web interface for the PDF Chat Bot.
    """
    return FileResponse("static/index_v2.html")

@app.get("/v1", response_class=FileResponse, tags=["web"])
async def web_interface_v1():
    """
    ## Web Interface v1

    Serve the original web interface for the PDF Chat Bot.
    """
    return FileResponse("static/index.html")

# API Root endpoint
@app.get("/api", response_model=APIResponse, tags=["system"])
async def api_root():
    """
    ## API Root Endpoint

    Welcome endpoint that confirms the API is running.

    **Perfect for**: Initial connectivity tests from mobile apps.
    """
    return APIResponse(
        success=True,
        message="PDF Chat Bot API is running",
    )

# Health check
@app.get("/api/v1/health", response_model=HealthResponse, tags=["monitoring"])
async def health_check():
    """
    ## System Health Check

    Comprehensive health check including:
    - API status
    - Gemini API connectivity
    - OCR API availability
    - Active sessions count
    - System uptime

    **Perfect for**: Monitoring and debugging from mobile apps.
    """
    try:
        # Test Gemini API
        from llm_client import get_gemini_client
        gemini_status = get_gemini_client().test_connection()
        
        # Test OCR API (basic check)
        ocr_status = bool(config.OCR_API_KEY)
        
        # Get system info
        active_sessions = len(get_all_sessions())
        uptime = (datetime.now() - app_state["startup_time"]).total_seconds() / 60
        
        health = SystemHealth(
            status="healthy" if gemini_status else "degraded",
            timestamp=datetime.now(),
            active_sessions=active_sessions,
            total_sessions_created=app_state["sessions_created"],
            gemini_api_status=gemini_status,
            ocr_api_status=ocr_status,
            system_info={
                "uptime_minutes": round(uptime, 2),
                "last_cleanup": app_state.get("last_cleanup"),
                "memory_usage": "N/A"  # Could add psutil for memory info
            }
        )
        
        return HealthResponse(
            success=True,
            message="System health check completed",
            health=health
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            success=False,
            message=f"Health check failed: {str(e)}",
            health=SystemHealth(
                status="unhealthy",
                timestamp=datetime.now(),
                active_sessions=0,
                total_sessions_created=app_state["sessions_created"],
                gemini_api_status=False,
                ocr_api_status=False,
                system_info={"error": str(e)}
            )
        )

# Session endpoints
@app.post("/api/v1/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, tags=["sessions"])
async def create_new_session(request: Optional[SessionCreate] = None):
    """
    ## Create New Chat Session

    Creates a new chat session for PDF interaction.

    **Returns**: Session ID and information
    **Next Step**: Upload a PDF to start chatting

    **Mobile App Usage**:
    ```dart
    final response = await http.post('/api/v1/sessions');
    final sessionId = response.data['session']['session_id'];
    ```
    """
    try:
        # Create session
        session = create_session()
        app_state["sessions_created"] += 1
        
        # Get session info
        summary = session.get_session_summary()
        session_name = request.session_name if request else None
        session_info = SessionInfo(
            session_id=session.session_id,
            session_name=session_name,
            status=SessionStatus.ACTIVE,
            created_at=session.created_at,
            last_activity=session.last_activity,
            duration_minutes=summary["duration_minutes"],
            has_pdf=summary["pdf_info"]["loaded"],
            message_count=summary["conversation_info"]["message_count"],
            total_tokens_used=summary["conversation_info"]["total_tokens_used"]
        )
        
        logger.info(f"Created new session: {session.session_id}")
        
        return SessionResponse(
            success=True,
            message="Session created successfully",
            session=session_info
        )
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to create session",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

@app.get("/api/v1/sessions/{session_id}", response_model=SessionResponse)
async def get_session_info(session: PDFChatSession = Depends(get_valid_session)):
    """Get session information"""
    try:
        summary = session.get_session_summary()
        session_info = SessionInfo(
            session_id=session.session_id,
            session_name=None,  # Could be stored in session if needed
            status=SessionStatus.ACTIVE,
            created_at=session.created_at,
            last_activity=session.last_activity,
            duration_minutes=summary["duration_minutes"],
            has_pdf=summary["pdf_info"]["loaded"],
            message_count=summary["conversation_info"]["message_count"],
            total_tokens_used=summary["conversation_info"]["total_tokens_used"]
        )
        
        return SessionResponse(
            success=True,
            message="Session information retrieved",
            session=session_info
        )
        
    except Exception as e:
        logger.error(f"Failed to get session info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve session information",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

@app.delete("/api/v1/sessions/{session_id}", response_model=APIResponse)
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        session = get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Session not found",
                    "error_code": ErrorCodes.SESSION_NOT_FOUND
                }
            )
        
        # Remove from active sessions
        from pdf_chat_session import active_sessions
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        logger.info(f"Deleted session: {session_id}")
        
        return APIResponse(
            success=True,
            message="Session deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to delete session",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

@app.get("/api/v1/sessions", response_model=SessionListResponse)
async def list_sessions():
    """List all active sessions"""
    try:
        # Cleanup expired sessions first
        cleanup_expired_sessions()
        app_state["last_cleanup"] = datetime.now()
        
        sessions = get_all_sessions()
        session_list = []
        
        for session in sessions.values():
            summary = session.get_session_summary()
            session_info = SessionInfo(
                session_id=session.session_id,
                session_name=None,
                status=SessionStatus.EXPIRED if session.is_session_expired() else SessionStatus.ACTIVE,
                created_at=session.created_at,
                last_activity=session.last_activity,
                duration_minutes=summary["duration_minutes"],
                has_pdf=summary["pdf_info"]["loaded"],
                message_count=summary["conversation_info"]["message_count"],
                total_tokens_used=summary["conversation_info"]["total_tokens_used"]
            )
            session_list.append(session_info)
        
        return SessionListResponse(
            success=True,
            message=f"Retrieved {len(session_list)} sessions",
            sessions=session_list,
            total_count=len(session_list)
        )
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to list sessions",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

# PDF endpoints
@app.post("/api/v1/sessions/{session_id}/pdf", response_model=PDFUploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    session: PDFChatSession = Depends(get_valid_session)
):
    """Upload and process PDF for a session"""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Invalid file type. Only PDF files are allowed.",
                    "error_code": ErrorCodes.INVALID_FILE_TYPE,
                    "details": {"filename": file.filename}
                }
            )

        # Check file size
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        if file_size_mb > config.MAX_PDF_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "success": False,
                    "message": f"File too large. Maximum size is {config.MAX_PDF_SIZE_MB}MB.",
                    "error_code": ErrorCodes.PDF_TOO_LARGE,
                    "details": {"file_size_mb": round(file_size_mb, 2)}
                }
            )

        # Save temporary file
        temp_path = f"/tmp/{session.session_id}_{file.filename}"
        with open(temp_path, "wb") as temp_file:
            temp_file.write(content)

        # Load PDF into session
        if not session.load_pdf(temp_path):
            # Clean up temp file
            os.remove(temp_path)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "success": False,
                    "message": "Failed to process PDF. File may be corrupted or unsupported.",
                    "error_code": ErrorCodes.PDF_UPLOAD_FAILED,
                    "details": {"filename": file.filename}
                }
            )

        # Clean up temp file
        os.remove(temp_path)

        # Get PDF info
        summary = session.get_session_summary()
        pdf_info = PDFInfo(
            filename=file.filename,
            file_size=len(content),
            num_pages=summary["pdf_info"]["num_pages"],
            content_length=summary["pdf_info"]["content_length"],
            estimated_tokens=summary["pdf_info"]["estimated_tokens"],
            extraction_method="ocr" if summary["pdf_info"]["is_scanned"] else "text",
            uploaded_at=datetime.now()
        )

        logger.info(f"PDF uploaded to session {session.session_id}: {file.filename}")

        return PDFUploadResponse(
            success=True,
            message="PDF uploaded and processed successfully",
            pdf_info=pdf_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF upload failed: {e}")
        # Clean up temp file if it exists
        temp_path = f"/tmp/{session.session_id}_{file.filename}"
        if os.path.exists(temp_path):
            os.remove(temp_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "PDF upload failed due to internal error",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

@app.get("/api/v1/sessions/{session_id}/pdf", response_model=PDFUploadResponse)
async def get_pdf_info(session: PDFChatSession = Depends(get_valid_session)):
    """Get information about the PDF loaded in a session"""
    try:
        if not session.pdf_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "No PDF loaded in this session",
                    "error_code": ErrorCodes.PDF_NOT_LOADED,
                    "details": {"session_id": session.session_id}
                }
            )

        summary = session.get_session_summary()
        pdf_info = PDFInfo(
            filename=session.pdf_filename or "unknown.pdf",
            file_size=summary["pdf_info"]["file_size"],
            num_pages=summary["pdf_info"]["num_pages"],
            content_length=summary["pdf_info"]["content_length"],
            estimated_tokens=summary["pdf_info"]["estimated_tokens"],
            extraction_method="ocr" if summary["pdf_info"]["is_scanned"] else "text",
            uploaded_at=session.created_at  # Approximation
        )

        return PDFUploadResponse(
            success=True,
            message="PDF information retrieved",
            pdf_info=pdf_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get PDF info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve PDF information",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

@app.delete("/api/v1/sessions/{session_id}/pdf", response_model=APIResponse, tags=["pdf"])
async def remove_pdf(session: PDFChatSession = Depends(get_valid_session)):
    """Remove PDF from a session"""
    try:
        if not session.pdf_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "No PDF loaded in this session",
                    "error_code": ErrorCodes.PDF_NOT_LOADED
                }
            )

        session.unload_pdf()
        logger.info(f"PDF removed from session: {session.session_id}")

        return APIResponse(
            success=True,
            message="PDF removed from session successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to remove PDF",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

# Multiple PDFs endpoints
@app.get("/api/v1/sessions/{session_id}/pdfs", response_model=Dict, tags=["pdf"])
async def list_pdfs(session: PDFChatSession = Depends(get_valid_session)):
    """
    ## List All PDFs in Session

    Get information about all PDFs loaded in the session.

    **Perfect for**: Showing user which documents are loaded
    """
    try:
        pdf_list = session.get_pdf_list()

        return {
            "success": True,
            "message": f"Retrieved {len(pdf_list)} PDFs",
            "pdfs": pdf_list,
            "total_pdfs": len(pdf_list),
            "total_tokens": sum(pdf['tokens'] for pdf in pdf_list)
        }

    except Exception as e:
        logger.error(f"Failed to list PDFs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to list PDFs",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

@app.post("/api/v1/sessions/{session_id}/pdfs/add", response_model=PDFUploadResponse, tags=["pdf"])
async def add_pdf_to_session(
    file: UploadFile = File(...),
    pdf_name: Optional[str] = None,
    session: PDFChatSession = Depends(get_valid_session)
):
    """
    ## Add Additional PDF to Session

    Add another PDF to an existing session (supports multiple PDFs).

    **Use Case**: Load related documents into the same conversation
    **Example**: Load multiple reports, memos, or related documents
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Invalid file type. Only PDF files are allowed.",
                    "error_code": ErrorCodes.INVALID_FILE_TYPE,
                    "details": {"filename": file.filename}
                }
            )

        # Check file size
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        if file_size_mb > config.MAX_PDF_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "success": False,
                    "message": f"File too large. Maximum size is {config.MAX_PDF_SIZE_MB}MB.",
                    "error_code": ErrorCodes.PDF_TOO_LARGE,
                    "details": {"file_size_mb": round(file_size_mb, 2)}
                }
            )

        # Use custom name or filename
        display_name = pdf_name or file.filename

        # Check if PDF with same name already exists
        if display_name in session.pdfs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": f"PDF with name '{display_name}' already exists in session",
                    "error_code": "PDF_NAME_EXISTS",
                    "details": {"pdf_name": display_name}
                }
            )

        # Save temporary file
        temp_path = f"/tmp/{session.session_id}_{display_name}"
        with open(temp_path, "wb") as temp_file:
            temp_file.write(content)

        # Load PDF into session
        if not session.load_pdf(temp_path, display_name):
            # Clean up temp file
            os.remove(temp_path)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "success": False,
                    "message": "Failed to process PDF. File may be corrupted or unsupported.",
                    "error_code": ErrorCodes.PDF_UPLOAD_FAILED,
                    "details": {"filename": display_name}
                }
            )

        # Clean up temp file
        os.remove(temp_path)

        # Get PDF info
        pdf_data = session.pdfs[display_name]
        pdf_info = PDFInfo(
            filename=display_name,
            file_size=len(content),
            num_pages=pdf_data['info']['num_pages'],
            content_length=len(pdf_data['content']),
            estimated_tokens=session.llm_client.estimate_tokens(pdf_data['content']),
            extraction_method=pdf_data['method'],
            uploaded_at=pdf_data['uploaded_at']
        )

        logger.info(f"Additional PDF added to session {session.session_id}: {display_name} (Total: {len(session.pdfs)})")

        return PDFUploadResponse(
            success=True,
            message=f"PDF added successfully. Session now has {len(session.pdfs)} PDFs.",
            pdf_info=pdf_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF addition failed: {e}")
        # Clean up temp file if it exists
        temp_path = f"/tmp/{session.session_id}_{pdf_name or file.filename}"
        if os.path.exists(temp_path):
            os.remove(temp_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "PDF addition failed due to internal error",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

@app.delete("/api/v1/sessions/{session_id}/pdfs/{pdf_name}", response_model=APIResponse, tags=["pdf"])
async def remove_specific_pdf(
    pdf_name: str,
    session: PDFChatSession = Depends(get_valid_session)
):
    """
    ## Remove Specific PDF from Session

    Remove a specific PDF while keeping others loaded.

    **Use Case**: Remove outdated or irrelevant documents from conversation
    """
    try:
        if not session.remove_pdf(pdf_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": f"PDF '{pdf_name}' not found in session",
                    "error_code": "PDF_NOT_FOUND",
                    "details": {"pdf_name": pdf_name}
                }
            )

        remaining_count = len(session.pdfs)
        logger.info(f"PDF '{pdf_name}' removed from session: {session.session_id}. Remaining: {remaining_count}")

        return APIResponse(
            success=True,
            message=f"PDF '{pdf_name}' removed successfully. {remaining_count} PDFs remaining."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to remove PDF",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to remove PDF",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

# Chat endpoints
@app.post("/api/v1/sessions/{session_id}/chat", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    session: PDFChatSession = Depends(get_valid_session)
):
    """Send a message to the AI and get a response"""
    try:
        if not session.pdf_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "No PDF loaded in this session. Please upload a PDF first.",
                    "error_code": ErrorCodes.PDF_NOT_LOADED,
                    "details": {"session_id": session.session_id}
                }
            )

        # Send message to AI
        result = await session.chat(request.message)

        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Chat processing failed",
                    "error_code": ErrorCodes.CHAT_FAILED,
                    "details": {"error": result.get('error', 'Unknown error')}
                }
            )

        # Build response
        token_info = TokenInfo(
            message_tokens=result['token_info']['message_tokens'],
            pdf_tokens=result['token_info']['pdf_tokens'],
            history_tokens=result['token_info']['history_tokens'],
            response_tokens=result['token_info']['response_tokens'],
            total_exchange_tokens=result['token_info']['total_exchange_tokens'],
            session_total_tokens=result['token_info']['session_total_tokens'],
            gemini_usage_percentage=result['token_info']['percentage_used']
        )

        session_info = SessionInfo(
            session_id=session.session_id,
            session_name=None,
            status=SessionStatus.ACTIVE,
            created_at=session.created_at,
            last_activity=session.last_activity,
            duration_minutes=result['session_info']['session_duration_minutes'],
            has_pdf=True,
            message_count=result['session_info']['conversation_length'],
            total_tokens_used=result['token_info']['session_total_tokens']
        )

        logger.info(f"Chat message processed for session {session.session_id}")

        return ChatResponse(
            success=True,
            message="Message processed successfully",
            response=result['response'],
            token_info=token_info,
            session_info=session_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Chat processing failed due to internal error",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

@app.get("/api/v1/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(session: PDFChatSession = Depends(get_valid_session)):
    """Get chat history for a session"""
    try:
        messages = []
        for msg in session.conversation_history:
            chat_message = ChatMessage(
                role=MessageRole(msg['role']),
                content=msg['content'],
                timestamp=datetime.fromisoformat(msg.get('timestamp', datetime.now().isoformat())),
                token_count=session.llm_client.estimate_tokens(msg['content'])
            )
            messages.append(chat_message)

        summary = session.get_session_summary()
        session_info = SessionInfo(
            session_id=session.session_id,
            session_name=None,
            status=SessionStatus.ACTIVE,
            created_at=session.created_at,
            last_activity=session.last_activity,
            duration_minutes=summary["duration_minutes"],
            has_pdf=summary["pdf_info"]["loaded"],
            message_count=summary["conversation_info"]["message_count"],
            total_tokens_used=summary["conversation_info"]["total_tokens_used"]
        )

        return ChatHistoryResponse(
            success=True,
            message=f"Retrieved {len(messages)} messages",
            messages=messages,
            total_messages=len(messages),
            session_info=session_info
        )

    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve chat history",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

@app.delete("/api/v1/sessions/{session_id}/history", response_model=APIResponse)
async def clear_chat_history(session: PDFChatSession = Depends(get_valid_session)):
    """Clear chat history for a session (keeps PDF loaded)"""
    try:
        session.clear_conversation()
        logger.info(f"Chat history cleared for session: {session.session_id}")

        return APIResponse(
            success=True,
            message="Chat history cleared successfully"
        )

    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to clear chat history",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

# Statistics endpoint
@app.get("/api/v1/sessions/{session_id}/stats", response_model=SessionStatsResponse)
async def get_session_stats(session: PDFChatSession = Depends(get_valid_session)):
    """Get detailed statistics for a session"""
    try:
        summary = session.get_session_summary()

        # Build detailed stats
        session_info = SessionInfo(
            session_id=session.session_id,
            session_name=None,
            status=SessionStatus.ACTIVE,
            created_at=session.created_at,
            last_activity=session.last_activity,
            duration_minutes=summary["duration_minutes"],
            has_pdf=summary["pdf_info"]["loaded"],
            message_count=summary["conversation_info"]["message_count"],
            total_tokens_used=summary["conversation_info"]["total_tokens_used"]
        )

        pdf_info = None
        if session.pdf_content:
            pdf_info = PDFInfo(
                filename=session.pdf_filename or "unknown.pdf",
                file_size=summary["pdf_info"]["file_size"],
                num_pages=summary["pdf_info"]["num_pages"],
                content_length=summary["pdf_info"]["content_length"],
                estimated_tokens=summary["pdf_info"]["estimated_tokens"],
                extraction_method="ocr" if summary["pdf_info"]["is_scanned"] else "text",
                uploaded_at=session.created_at
            )

        stats = SessionStats(
            session_id=session.session_id,
            session_info=session_info,
            pdf_info=pdf_info,
            token_usage=summary["conversation_info"],
            conversation_stats={
                "messages": summary["conversation_info"]["message_count"],
                "avg_tokens_per_exchange": summary["conversation_info"]["average_tokens_per_exchange"],
                "total_tokens": summary["conversation_info"]["total_tokens_used"]
            },
            recent_activity=summary["token_usage_history"]
        )

        return SessionStatsResponse(
            success=True,
            message="Session statistics retrieved",
            stats=stats
        )

    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve session statistics",
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "details": {"error": str(e)}
            }
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {
            "success": False,
            "message": str(exc.detail),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": ErrorCodes.INTERNAL_ERROR,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
