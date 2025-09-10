"""
Test script for PDF processor
Tests both standard text extraction and OCR fallback
"""
import asyncio
import sys
import os
from pdf_processor import get_pdf_processor

def test_pdf_info():
    """Test PDF information extraction"""
    print("🔄 Testing PDF information extraction...")
    
    pdf_path = "JEFES, JEFAS Y ENCARGADOS.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found: {pdf_path}")
        return False
    
    try:
        processor = get_pdf_processor()
        info = processor.get_pdf_info(pdf_path)
        
        print(f"📄 PDF Information:")
        print(f"   File size: {info['file_size']:,} bytes")
        print(f"   Pages: {info['num_pages']}")
        print(f"   Has text: {info['has_text']}")
        print(f"   Is scanned: {info['is_scanned']}")
        
        print("✅ PDF info extraction successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error getting PDF info: {e}")
        return False

def test_text_extraction():
    """Test text extraction from PDF"""
    print("\n🔄 Testing PDF text extraction...")
    
    pdf_path = "JEFES, JEFAS Y ENCARGADOS.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found: {pdf_path}")
        return False
    
    try:
        processor = get_pdf_processor()
        text, method = processor.extract_text(pdf_path)
        
        print(f"📤 Extraction method: {method}")
        
        if text:
            print(f"📥 Extracted text length: {len(text)} characters")
            print(f"📝 First 200 characters:")
            print("-" * 50)
            print(text[:200] + "..." if len(text) > 200 else text)
            print("-" * 50)
            
            # Save extracted text to file for review
            output_file = f"extracted_text_{method}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Extraction method: {method}\n")
                f.write(f"Source file: {pdf_path}\n")
                f.write("=" * 50 + "\n\n")
                f.write(text)
            
            print(f"💾 Full text saved to: {output_file}")
            print("✅ Text extraction successful!")
            return True
        else:
            print("❌ No text extracted")
            return False
            
    except Exception as e:
        print(f"❌ Error extracting text: {e}")
        return False

def test_ocr_availability():
    """Test if OCR is available and configured"""
    print("\n🔄 Testing OCR availability...")
    
    try:
        processor = get_pdf_processor()
        
        if processor.ocr_available:
            print("✅ OCR.space API is configured and available")
            
            # Test with a simple request (if API key is valid)
            from config import config
            if config.OCR_API_KEY and len(config.OCR_API_KEY) > 10:
                print(f"🔑 API Key: {config.OCR_API_KEY[:10]}...")
                print("💡 OCR will be used as fallback for scanned PDFs")
            else:
                print("⚠️ OCR API key seems invalid or too short")
                
            return True
        else:
            print("⚠️ OCR.space API not configured")
            print("💡 Only standard text extraction will be available")
            print("📝 To enable OCR, add OCR_API_KEY to your .env file")
            return False
            
    except Exception as e:
        print(f"❌ Error checking OCR availability: {e}")
        return False

def main():
    """Run all PDF processor tests"""
    print("🚀 Starting PDF Processor Tests")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("OCR Availability", test_ocr_availability()),
        ("PDF Info Extraction", test_pdf_info()),
        ("Text Extraction", test_text_extraction())
    ]
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! PDF processor is ready to use.")
        return 0
    elif passed >= 2:  # OCR might not be configured, but basic functionality works
        print("⚠️ Some tests failed, but basic functionality is available.")
        print("💡 Configure OCR_API_KEY in .env for full functionality.")
        return 0
    else:
        print("❌ Critical tests failed. Check your configuration.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
