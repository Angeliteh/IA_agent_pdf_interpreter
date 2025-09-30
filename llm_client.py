"""
Gemini LLM Client for PDF Chat Bot
"""
import google.generativeai as genai
from typing import List, Dict, Optional
import logging
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google's Gemini API"""
    
    def __init__(self):
        """Initialize the Gemini client"""
        try:
            # Validate configuration
            config.validate()
            
            # Configure Gemini
            genai.configure(api_key=config.GEMINI_API_KEY)
            
            # Initialize the model
            self.model = genai.GenerativeModel(
                model_name=config.GEMINI_MODEL,
                generation_config=genai.types.GenerationConfig(
                    temperature=config.TEMPERATURE,
                    max_output_tokens=config.MAX_TOKENS,
                )
            )
            
            logger.info(f"Gemini client initialized with model: {config.GEMINI_MODEL}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def get_system_prompt(self, pdf_content: Optional[str] = None) -> str:
        """
        Generate the system prompt based on the requirements (supports multiple PDFs)
        """
        base_prompt = """Recibirás uno o más documentos PDF con información formal. Tu tarea es resumir y explicar el contenido en lenguaje claro, simple y humano.

Prioriza lo esencial y lo práctico, como si hablaras con alguien ocupado que no tiene tiempo de leer todo el documento.

Evita tecnicismos innecesarios y responde de forma concisa y comprensible.

También debes responder preguntas específicas sobre el contenido de los documentos.

Características de tus respuestas:
- Lenguaje claro y directo
- Resúmenes concisos pero completos
- Explicaciones como si hablaras con alguien ocupado
- Respuestas específicas cuando te pregunten sobre los documentos
- Si hay múltiples documentos, especifica de cuál estás hablando cuando sea relevante"""

        if pdf_content:
            # Detect if it's multiple PDFs by looking for "DOCUMENTO #" markers
            is_multiple_pdfs = pdf_content.count("DOCUMENTO #") > 1

            if is_multiple_pdfs:
                return f"""{base_prompt}

DOCUMENTOS PDF CARGADOS:
========================
{pdf_content}
========================

INSTRUCCIONES ESPECIALES:
- Tienes acceso a MÚLTIPLES documentos PDF
- Cada documento está claramente separado con su nombre y contenido
- Cuando respondas, puedes hacer referencia a información de cualquiera de los documentos
- Si la pregunta se refiere a un documento específico, menciona cuál
- Si la información está en varios documentos, puedes combinarla en tu respuesta
- Para resúmenes generales, incluye información relevante de todos los documentos

Ahora puedes responder preguntas sobre estos documentos o proporcionar resúmenes si te lo solicitan."""
            else:
                return f"""{base_prompt}

DOCUMENTO PDF CARGADO:
=====================
{pdf_content}
=====================

Ahora puedes responder preguntas sobre este documento o proporcionar un resumen si te lo solicitan."""

        return base_prompt
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count using the rule: 1 token ≈ 4 characters

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def get_token_usage_info(self, message: str, pdf_content: Optional[str] = None,
                           conversation_history: List[Dict[str, str]] = None) -> dict:
        """
        Calculate token usage information for monitoring

        Args:
            message: User's message
            pdf_content: Content of the PDF (if available)
            conversation_history: Previous messages in the conversation

        Returns:
            Dictionary with token usage information
        """
        message_tokens = self.estimate_tokens(message)
        pdf_tokens = self.estimate_tokens(pdf_content) if pdf_content else 0
        base_prompt_tokens = self.estimate_tokens(self.get_system_prompt())

        history_tokens = 0
        if conversation_history:
            history_text = str(conversation_history)
            history_tokens = self.estimate_tokens(history_text)

        total_tokens = message_tokens + pdf_tokens + base_prompt_tokens + history_tokens

        return {
            'message_tokens': message_tokens,
            'pdf_tokens': pdf_tokens,
            'base_prompt_tokens': base_prompt_tokens,
            'history_tokens': history_tokens,
            'total_tokens': total_tokens,
            'gemini_limit': 1_000_000,
            'percentage_used': (total_tokens / 1_000_000) * 100
        }

    async def chat(self, message: str, pdf_content: Optional[str] = None,
                   conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Send a message to Gemini and get a response with constant PDF injection

        Args:
            message: User's message
            pdf_content: Content of the PDF (if available) - INJECTED IN EVERY MESSAGE
            conversation_history: Previous messages in the conversation

        Returns:
            AI response as string
        """
        try:
            # Calculate token usage for monitoring
            token_info = self.get_token_usage_info(message, pdf_content, conversation_history)
            logger.info(f"Token usage: {token_info['total_tokens']:,} tokens ({token_info['percentage_used']:.3f}% of limit)")

            # Warning if approaching limits
            if token_info['percentage_used'] > 50:
                logger.warning(f"High token usage: {token_info['percentage_used']:.1f}% of Gemini limit")

            # Build the conversation context
            chat_history = []

            # Add conversation history
            if conversation_history:
                for msg in conversation_history:
                    chat_history.append({
                        'role': msg['role'],
                        'parts': [msg['content']]
                    })

            # Start chat session
            chat = self.model.start_chat(history=chat_history)

            # ALWAYS include PDF content if available (constant injection)
            if pdf_content:
                system_prompt_with_pdf = self.get_system_prompt(pdf_content)
                full_message = f"{system_prompt_with_pdf}\n\nUsuario: {message}"
                logger.info("PDF content injected into message for persistent context")
            else:
                full_message = message

            # Send message and get response
            response = chat.send_message(full_message)

            logger.info(f"Successfully generated response for message: {message[:50]}...")
            return response.text

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Lo siento, hubo un error al procesar tu mensaje: {str(e)}"
    
    def test_connection(self) -> bool:
        """
        Test the connection to Gemini API
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Simple test message
            test_response = self.model.generate_content("Responde solo con 'OK' si puedes leer este mensaje.")
            
            if test_response and test_response.text:
                logger.info("Gemini API connection test successful")
                return True
            else:
                logger.error("Gemini API connection test failed - no response")
                return False
                
        except Exception as e:
            logger.error(f"Gemini API connection test failed: {e}")
            return False

# Global client instance
gemini_client = None

def get_gemini_client() -> GeminiClient:
    """Get or create the global Gemini client instance"""
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient()
    return gemini_client
