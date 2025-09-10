"""
Enhanced PDF Chat Session Manager
Provides robust session management with constant PDF injection and token monitoring
"""
import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pdf_processor import get_pdf_processor
from llm_client import get_gemini_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFChatSession:
    """
    Enhanced PDF Chat Session with constant PDF injection and token monitoring
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize a new PDF chat session
        
        Args:
            session_id: Optional session identifier
        """
        self.session_id = session_id or self._generate_session_id()
        self.pdf_processor = get_pdf_processor()
        self.llm_client = get_gemini_client()
        
        # Session state
        self.pdf_content = None
        self.pdf_filename = None
        self.pdf_info = {}
        self.conversation_history = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Token monitoring
        self.total_tokens_used = 0
        self.token_usage_history = []
        
        logger.info(f"Created new PDF chat session: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"pdf_chat_{timestamp}"
    
    def load_pdf(self, pdf_path: str) -> bool:
        """
        Load and process a PDF file for the session
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            True if PDF loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                return False
            
            logger.info(f"Loading PDF: {pdf_path}")
            
            # Get PDF information
            self.pdf_info = self.pdf_processor.get_pdf_info(pdf_path)
            self.pdf_filename = os.path.basename(pdf_path)
            
            # Extract text content
            text, method = self.pdf_processor.extract_text(pdf_path)
            
            if not text:
                logger.error("Could not extract text from PDF")
                return False
            
            self.pdf_content = text
            
            # Log PDF loading info
            logger.info(f"PDF loaded successfully:")
            logger.info(f"  - File: {self.pdf_filename}")
            logger.info(f"  - Size: {self.pdf_info['file_size']:,} bytes")
            logger.info(f"  - Pages: {self.pdf_info['num_pages']}")
            logger.info(f"  - Method: {method}")
            logger.info(f"  - Content length: {len(text)} characters")
            logger.info(f"  - Estimated tokens: {self.llm_client.estimate_tokens(text):,}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            return False
    
    async def chat(self, message: str) -> Dict[str, any]:
        """
        Send a message to the AI with constant PDF injection
        
        Args:
            message: User's message
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            if not self.pdf_content:
                return {
                    'success': False,
                    'error': 'No PDF loaded in this session',
                    'response': None,
                    'token_info': None
                }
            
            # Update activity timestamp
            self.last_activity = datetime.now()
            
            # Get token usage info before sending
            token_info = self.llm_client.get_token_usage_info(
                message, self.pdf_content, self.conversation_history
            )
            
            # Send message with constant PDF injection
            response = await self.llm_client.chat(
                message=message,
                pdf_content=self.pdf_content,  # ALWAYS inject PDF
                conversation_history=self.conversation_history
            )
            
            # Update conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': self.last_activity.isoformat()
            })
            
            self.conversation_history.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update token usage tracking
            response_tokens = self.llm_client.estimate_tokens(response)
            total_message_tokens = token_info['total_tokens'] + response_tokens
            self.total_tokens_used += total_message_tokens
            
            # Store token usage for this exchange
            token_usage_record = {
                'timestamp': self.last_activity.isoformat(),
                'message_tokens': token_info['message_tokens'],
                'response_tokens': response_tokens,
                'total_exchange_tokens': total_message_tokens,
                'cumulative_tokens': self.total_tokens_used
            }
            self.token_usage_history.append(token_usage_record)
            
            logger.info(f"Chat exchange completed - Tokens used: {total_message_tokens:,}")
            
            return {
                'success': True,
                'response': response,
                'token_info': {
                    **token_info,
                    'response_tokens': response_tokens,
                    'total_exchange_tokens': total_message_tokens,
                    'session_total_tokens': self.total_tokens_used
                },
                'session_info': {
                    'session_id': self.session_id,
                    'pdf_filename': self.pdf_filename,
                    'conversation_length': len(self.conversation_history),
                    'session_duration_minutes': (self.last_activity - self.created_at).total_seconds() / 60
                }
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"Lo siento, hubo un error al procesar tu mensaje: {str(e)}",
                'token_info': None
            }
    
    def get_session_summary(self) -> Dict[str, any]:
        """
        Get comprehensive session summary
        
        Returns:
            Dictionary with session information
        """
        duration = datetime.now() - self.created_at
        
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'duration_minutes': duration.total_seconds() / 60,
            'pdf_info': {
                'filename': self.pdf_filename,
                'loaded': bool(self.pdf_content),
                'content_length': len(self.pdf_content) if self.pdf_content else 0,
                'estimated_tokens': self.llm_client.estimate_tokens(self.pdf_content) if self.pdf_content else 0,
                **self.pdf_info
            },
            'conversation_info': {
                'message_count': len(self.conversation_history),
                'total_tokens_used': self.total_tokens_used,
                'average_tokens_per_exchange': self.total_tokens_used / max(len(self.conversation_history) // 2, 1)
            },
            'token_usage_history': self.token_usage_history[-10:]  # Last 10 exchanges
        }
    
    def is_session_expired(self, timeout_minutes: int = 30) -> bool:
        """
        Check if session has expired
        
        Args:
            timeout_minutes: Session timeout in minutes
            
        Returns:
            True if session is expired
        """
        timeout_delta = timedelta(minutes=timeout_minutes)
        return datetime.now() - self.last_activity > timeout_delta
    
    def clear_conversation(self):
        """Clear conversation history while keeping PDF loaded"""
        self.conversation_history = []
        self.token_usage_history = []
        self.total_tokens_used = 0
        logger.info(f"Conversation cleared for session: {self.session_id}")
    
    def unload_pdf(self):
        """Unload PDF and clear all session data"""
        self.pdf_content = None
        self.pdf_filename = None
        self.pdf_info = {}
        self.clear_conversation()
        logger.info(f"PDF unloaded from session: {self.session_id}")

# Global session manager
active_sessions = {}

def create_session(session_id: Optional[str] = None) -> PDFChatSession:
    """Create a new PDF chat session"""
    session = PDFChatSession(session_id)
    active_sessions[session.session_id] = session
    return session

def get_session(session_id: str) -> Optional[PDFChatSession]:
    """Get an existing session by ID"""
    return active_sessions.get(session_id)

def cleanup_expired_sessions(timeout_minutes: int = 30) -> int:
    """Clean up expired sessions"""
    expired_sessions = []
    
    for session_id, session in active_sessions.items():
        if session.is_session_expired(timeout_minutes):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del active_sessions[session_id]
        logger.info(f"Cleaned up expired session: {session_id}")
    
    return len(expired_sessions)

def get_all_sessions() -> Dict[str, PDFChatSession]:
    """Get all active sessions"""
    return active_sessions.copy()
