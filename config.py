"""
Configuration settings for the PDF Chat Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = "gemini-2.0-flash-exp"  # Using Gemini 2.0 Flash

    # OCR API Configuration (OCR.space - same as your previous project)
    OCR_API_KEY = os.getenv("OCR_API_KEY")
    OCR_API_URL = "https://api.ocr.space/parse/image"

    # Application settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    
    # PDF processing settings
    MAX_PDF_SIZE_MB = 10
    ALLOWED_EXTENSIONS = {'.pdf'}
    
    # Session management
    SESSION_TIMEOUT_MINUTES = 30
    MAX_CONVERSATION_LENGTH = 20  # messages before suggesting new session
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required. Please set it in your .env file")
        return True

    @classmethod
    def validate_ocr(cls):
        """Validate OCR configuration"""
        if not cls.OCR_API_KEY:
            raise ValueError("OCR_API_KEY is required for PDF processing. Please set it in your .env file")
        return True

# Global config instance
config = Config()
