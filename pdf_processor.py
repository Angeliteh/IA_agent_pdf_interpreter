"""
PDF Text Extraction Module for PDF Chat Bot

This module provides hybrid PDF text extraction:
1. First tries standard text extraction (for text-based PDFs)
2. Falls back to OCR.space API (for scanned PDFs) - same as your previous project

Based on your successful word_autofill project implementation.
"""
import os
import logging
import requests
from typing import Optional, Tuple
import pdfplumber
import PyPDF2
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Hybrid PDF processor that handles both text-based and scanned PDFs
    """
    
    def __init__(self):
        """Initialize the PDF processor"""
        self.ocr_available = bool(config.OCR_API_KEY)
        if self.ocr_available:
            logger.info("OCR.space API available for scanned PDFs")
        else:
            logger.warning("OCR API key not configured - scanned PDFs won't be processed")
    
    def extract_text(self, pdf_path: str) -> Tuple[str, str]:
        """
        Extract text from PDF using hybrid approach
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, extraction_method)
            extraction_method can be: 'text', 'ocr', 'failed'
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Step 1: Try standard text extraction
        text, method = self._extract_text_standard(pdf_path)
        
        if text and len(text.strip()) > 50:  # Minimum threshold for meaningful text
            logger.info("Successfully extracted text using standard method")
            return text, method
        
        # Step 2: Fall back to OCR if standard extraction failed
        if self.ocr_available:
            logger.info("Standard extraction failed, trying OCR...")
            text, method = self._extract_text_ocr(pdf_path)
            if text:
                logger.info("Successfully extracted text using OCR")
                return text, method
        
        # Step 3: Both methods failed
        logger.error("Both standard and OCR extraction failed")
        return "", "failed"
    
    def _extract_text_standard(self, pdf_path: str) -> Tuple[str, str]:
        """
        Extract text using standard PDF libraries (pdfplumber + PyPDF2)
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, method)
        """
        text = ""
        
        # Try pdfplumber first (better for complex layouts)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                return text.strip(), "text"
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")
        
        # Try PyPDF2 as backup
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                return text.strip(), "text"
        except Exception as e:
            logger.warning(f"PyPDF2 failed: {e}")
        
        return "", "failed"
    
    def _extract_text_ocr(self, pdf_path: str) -> Tuple[str, str]:
        """
        Extract text using OCR.space API (same as your previous project)
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, method)
        """
        if not self.ocr_available:
            return "", "failed"
        
        try:
            # Validate OCR configuration
            config.validate_ocr()
            
            with open(pdf_path, 'rb') as file:
                # Payload based on your successful implementation
                payload = {
                    'apikey': config.OCR_API_KEY,
                    'language': 'spa',  # Spanish language as in your project
                    'isOverlayRequired': False,
                    'detectOrientation': True,
                    'scale': True,
                    'OCREngine': 2,  # Use advanced OCR engine
                    'isTable': True  # Better table detection
                }
                
                files = {'file': file}
                
                logger.info("Sending PDF to OCR.space API...")
                response = requests.post(
                    config.OCR_API_URL,
                    files=files,
                    data=payload,
                    timeout=60  # Longer timeout for large PDFs
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('IsErroredOnProcessing', False):
                        error_msg = result.get('ErrorMessage', 'Unknown OCR error')
                        logger.error(f"OCR processing error: {error_msg}")
                        return "", "failed"
                    
                    # Extract text from response
                    text = ""
                    if 'ParsedResults' in result and result['ParsedResults']:
                        for parsed_result in result['ParsedResults']:
                            if 'ParsedText' in parsed_result:
                                text += parsed_result['ParsedText'] + "\n"
                    
                    return text.strip(), "ocr"
                else:
                    logger.error(f"OCR API error: {response.status_code} - {response.text}")
                    return "", "failed"
                    
        except requests.exceptions.Timeout:
            logger.error("OCR API timeout - PDF might be too large")
            return "", "failed"
        except requests.exceptions.ConnectionError:
            logger.error("OCR API connection error - check internet connection")
            return "", "failed"
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return "", "failed"
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get basic information about the PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF information
        """
        info = {
            'file_size': 0,
            'num_pages': 0,
            'is_scanned': False,
            'has_text': False
        }
        
        try:
            # Get file size
            info['file_size'] = os.path.getsize(pdf_path)
            
            # Try to get page count and detect if scanned
            with pdfplumber.open(pdf_path) as pdf:
                info['num_pages'] = len(pdf.pages)
                
                # Check first few pages for text content
                pages_to_check = min(3, len(pdf.pages))
                total_text = ""
                
                for i in range(pages_to_check):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        total_text += page_text
                
                # Heuristic: if very little text extracted, likely scanned
                info['has_text'] = len(total_text.strip()) > 100
                info['is_scanned'] = not info['has_text']
                
        except Exception as e:
            logger.warning(f"Could not get PDF info: {e}")
        
        return info

# Global processor instance
pdf_processor = None

def get_pdf_processor() -> PDFProcessor:
    """Get or create the global PDF processor instance"""
    global pdf_processor
    if pdf_processor is None:
        pdf_processor = PDFProcessor()
    return pdf_processor
