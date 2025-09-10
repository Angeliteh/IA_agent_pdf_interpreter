"""
Test script for the complete PDF Chat system
Tests the full flow: PDF → Text → AI → Response
"""
import asyncio
import sys
import os
from pdf_processor import get_pdf_processor
from llm_client import get_gemini_client

class PDFChatTester:
    """Test the complete PDF chat system"""
    
    def __init__(self):
        self.pdf_processor = get_pdf_processor()
        self.llm_client = get_gemini_client()
        self.current_pdf_content = None
        self.conversation_history = []
    
    def load_pdf(self, pdf_path: str) -> bool:
        """Load and process a PDF file"""
        print(f"🔄 Loading PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF not found: {pdf_path}")
            return False
        
        try:
            # Get PDF info
            info = self.pdf_processor.get_pdf_info(pdf_path)
            print(f"📄 PDF Info:")
            print(f"   - Size: {info['file_size']:,} bytes")
            print(f"   - Pages: {info['num_pages']}")
            print(f"   - Type: {'Scanned' if info['is_scanned'] else 'Text-based'}")
            
            # Extract text
            text, method = self.pdf_processor.extract_text(pdf_path)
            
            if not text:
                print("❌ Could not extract text from PDF")
                return False
            
            self.current_pdf_content = text
            print(f"✅ Text extracted using: {method}")
            print(f"📝 Content length: {len(text)} characters")
            print(f"📋 First 150 characters:")
            print("-" * 50)
            print(text[:150] + "..." if len(text) > 150 else text)
            print("-" * 50)
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading PDF: {e}")
            return False
    
    async def chat(self, message: str) -> str:
        """Send a message to the AI with PDF context"""
        print(f"\n💬 User: {message}")
        print("🤖 AI is thinking...")
        
        try:
            # Send message with PDF context and conversation history
            response = await self.llm_client.chat(
                message=message,
                pdf_content=self.current_pdf_content,
                conversation_history=self.conversation_history
            )
            
            # Add to conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': message
            })
            self.conversation_history.append({
                'role': 'assistant', 
                'content': response
            })
            
            print(f"🤖 AI: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error in chat: {e}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def show_conversation_summary(self):
        """Show conversation summary"""
        if not self.conversation_history:
            print("📝 No conversation history yet")
            return
        
        print(f"\n📊 Conversation Summary:")
        print(f"   - Messages: {len(self.conversation_history)}")
        print(f"   - PDF loaded: {'Yes' if self.current_pdf_content else 'No'}")
        if self.current_pdf_content:
            print(f"   - PDF content: {len(self.current_pdf_content)} characters")

async def test_basic_flow():
    """Test the basic PDF → AI flow"""
    print("🚀 Testing Basic PDF Chat Flow")
    print("=" * 60)
    
    tester = PDFChatTester()
    
    # Step 1: Load PDF
    pdf_path = "JEFES, JEFAS Y ENCARGADOS.pdf"
    if not tester.load_pdf(pdf_path):
        return False
    
    # Step 2: Test basic questions
    test_questions = [
        "¿Puedes hacer un resumen de este documento?",
        "¿Cuál es el asunto del oficio?",
        "¿Qué fecha se menciona para el taller?",
        "¿Qué recomendaciones se dan para la capacitación?"
    ]
    
    print(f"\n🎯 Testing {len(test_questions)} questions...")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Question {i}/{len(test_questions)} ---")
        response = await tester.chat(question)
        
        if "Error" in response:
            print(f"❌ Question {i} failed")
            return False
        
        print("✅ Question answered successfully")
    
    # Step 3: Show summary
    tester.show_conversation_summary()
    
    return True

async def test_conversation_flow():
    """Test conversation with follow-up questions"""
    print("\n🔄 Testing Conversation Flow")
    print("=" * 60)
    
    tester = PDFChatTester()
    
    # Load PDF
    pdf_path = "JEFES, JEFAS Y ENCARGADOS.pdf"
    if not tester.load_pdf(pdf_path):
        return False
    
    # Conversation flow
    conversation = [
        "¿De qué trata este documento?",
        "¿Puedes darme más detalles sobre el taller mencionado?",
        "¿Qué cambió en la fecha?",
        "¿Hay alguna recomendación importante que deba saber?"
    ]
    
    print(f"\n💭 Testing conversation with {len(conversation)} messages...")
    
    for i, message in enumerate(conversation, 1):
        print(f"\n--- Message {i}/{len(conversation)} ---")
        response = await tester.chat(message)
        
        if "Error" in response:
            print(f"❌ Conversation failed at message {i}")
            return False
    
    print("\n✅ Conversation flow completed successfully")
    tester.show_conversation_summary()
    
    return True

async def interactive_test():
    """Interactive test mode"""
    print("\n🎮 Interactive Test Mode")
    print("=" * 60)
    print("Type your questions (or 'quit' to exit)")
    
    tester = PDFChatTester()
    
    # Load PDF
    pdf_path = "JEFES, JEFAS Y ENCARGADOS.pdf"
    if not tester.load_pdf(pdf_path):
        return False
    
    print("\n💡 PDF loaded! You can now ask questions about it.")
    print("Examples:")
    print("- ¿De qué trata este documento?")
    print("- ¿Cuáles son los puntos principales?")
    print("- ¿Hay fechas importantes?")
    
    while True:
        try:
            user_input = input("\n🗣️  You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'salir']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            await tester.chat(user_input)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    tester.show_conversation_summary()
    return True

async def main():
    """Run all tests"""
    print("🚀 PDF Chat System - Full Integration Test")
    print("=" * 70)
    
    # Test 1: Basic flow
    success1 = await test_basic_flow()
    
    if not success1:
        print("❌ Basic flow test failed")
        return 1
    
    # Test 2: Conversation flow
    success2 = await test_conversation_flow()
    
    if not success2:
        print("❌ Conversation flow test failed")
        return 1
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎉 ALL TESTS PASSED!")
    print("✅ PDF processing works")
    print("✅ AI integration works") 
    print("✅ Conversation flow works")
    print("✅ System is ready for API development")
    
    # Ask if user wants interactive mode
    print("\n🎮 Want to try interactive mode? (y/n)")
    try:
        choice = input().strip().lower()
        if choice in ['y', 'yes', 'si', 's']:
            await interactive_test()
    except KeyboardInterrupt:
        pass
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
