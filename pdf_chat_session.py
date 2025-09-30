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
        
        # Session state - EXTENDED for multiple PDFs
        self.pdfs = {}  # Dictionary: {filename: {content, info, uploaded_at}}
        self.combined_pdf_content = None  # Combined content for AI
        self.conversation_history = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

        # Legacy support (for backward compatibility)
        self.pdf_content = None
        self.pdf_filename = None
        self.pdf_info = {}
        
        # Token monitoring
        self.total_tokens_used = 0
        self.token_usage_history = []
        
        logger.info(f"Created new PDF chat session: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"pdf_chat_{timestamp}"
    
    def load_pdf(self, pdf_path: str, pdf_name: Optional[str] = None) -> bool:
        """
        Load and process a PDF file for the session (supports multiple PDFs)

        Args:
            pdf_path: Path to the PDF file
            pdf_name: Optional custom name for the PDF (defaults to filename)

        Returns:
            True if PDF loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                return False

            filename = pdf_name or os.path.basename(pdf_path)
            logger.info(f"Loading PDF: {filename} from {pdf_path}")

            # Get PDF information
            pdf_info = self.pdf_processor.get_pdf_info(pdf_path)

            # Extract text content
            text, method = self.pdf_processor.extract_text(pdf_path)

            if not text:
                logger.error("Could not extract text from PDF")
                return False

            # Store PDF in collection
            self.pdfs[filename] = {
                'content': text,
                'info': pdf_info,
                'method': method,
                'uploaded_at': datetime.now(),
                'path': pdf_path
            }

            # Update legacy fields for backward compatibility
            if len(self.pdfs) == 1:  # First PDF
                self.pdf_content = text
                self.pdf_filename = filename
                self.pdf_info = pdf_info

            # Rebuild combined content
            self._rebuild_combined_content()

            # Log PDF loading info
            logger.info(f"PDF loaded successfully:")
            logger.info(f"  - File: {filename}")
            logger.info(f"  - Size: {pdf_info['file_size']:,} bytes")
            logger.info(f"  - Pages: {pdf_info['num_pages']}")
            logger.info(f"  - Method: {method}")
            logger.info(f"  - Content length: {len(text)} characters")
            logger.info(f"  - Estimated tokens: {self.llm_client.estimate_tokens(text):,}")
            logger.info(f"  - Total PDFs in session: {len(self.pdfs)}")

            return True

        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            return False

    def _rebuild_combined_content(self):
        """Rebuild combined PDF content for AI processing"""
        if not self.pdfs:
            self.combined_pdf_content = None
            self.pdf_content = None  # Legacy
            return

        combined_parts = []
        for i, (filename, pdf_data) in enumerate(self.pdfs.items(), 1):
            combined_parts.append(f"""
DOCUMENTO #{i}: {filename}
===============================================
📄 Información del documento:
   - Páginas: {pdf_data['info']['num_pages']}
   - Método de extracción: {pdf_data['method']}
   - Fecha de carga: {pdf_data['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S')}
   - Tamaño: {pdf_data['info']['file_size']:,} bytes

📝 CONTENIDO COMPLETO:
-----------------------------------------------
{pdf_data['content']}
-----------------------------------------------
FIN DEL DOCUMENTO #{i}: {filename}
===============================================
""")

        self.combined_pdf_content = "\n".join(combined_parts)

        # Update legacy field
        self.pdf_content = self.combined_pdf_content

        logger.info(f"Combined content rebuilt: {len(self.combined_pdf_content)} characters from {len(self.pdfs)} PDFs")

    def get_pdf_list(self) -> List[Dict[str, any]]:
        """Get list of all PDFs in the session"""
        pdf_list = []
        for filename, pdf_data in self.pdfs.items():
            pdf_list.append({
                'filename': filename,
                'pages': pdf_data['info']['num_pages'],
                'size': pdf_data['info']['file_size'],
                'method': pdf_data['method'],
                'uploaded_at': pdf_data['uploaded_at'].isoformat(),
                'tokens': self.llm_client.estimate_tokens(pdf_data['content'])
            })
        return pdf_list

    def remove_pdf(self, filename: str) -> bool:
        """Remove a specific PDF from the session"""
        if filename not in self.pdfs:
            return False

        del self.pdfs[filename]
        self._rebuild_combined_content()

        # Update legacy fields
        if self.pdfs:
            first_pdf = next(iter(self.pdfs.values()))
            self.pdf_filename = next(iter(self.pdfs.keys()))
            self.pdf_info = first_pdf['info']
        else:
            self.pdf_filename = None
            self.pdf_info = {}

        logger.info(f"PDF removed: {filename}. Remaining PDFs: {len(self.pdfs)}")
        return True

    def has_pdfs(self) -> bool:
        """Check if session has any PDFs loaded"""
        return len(self.pdfs) > 0

    async def chat(self, message: str) -> Dict[str, any]:
        """
        Send a message to the AI with constant PDF injection
        
        Args:
            message: User's message
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            if not self.has_pdfs():
                return {
                    'success': False,
                    'error': 'No PDFs loaded in this session',
                    'response': None,
                    'token_info': None
                }
            
            # Update activity timestamp
            self.last_activity = datetime.now()
            
            # Get token usage info before sending
            token_info = self.llm_client.get_token_usage_info(
                message, self.pdf_content, self.conversation_history
            )
            
            # Send message with constant PDF injection (combined content)
            response = await self.llm_client.chat(
                message=message,
                pdf_content=self.combined_pdf_content,  # ALWAYS inject combined PDFs
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
                'pdfs_loaded': len(self.pdfs),
                'pdf_list': self.get_pdf_list(),
                'total_content_length': len(self.combined_pdf_content) if self.combined_pdf_content else 0,
                'total_estimated_tokens': self.llm_client.estimate_tokens(self.combined_pdf_content) if self.combined_pdf_content else 0,
                # Legacy fields for backward compatibility
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
        """Unload all PDFs and clear all session data"""
        self.pdfs = {}
        self.combined_pdf_content = None
        # Legacy fields
        self.pdf_content = None
        self.pdf_filename = None
        self.pdf_info = {}
        self.clear_conversation()
        logger.info(f"All PDFs unloaded from session: {self.session_id}")

    def unload_all_pdfs(self):
        """Alias for unload_pdf for clarity"""
        self.unload_pdf()

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
