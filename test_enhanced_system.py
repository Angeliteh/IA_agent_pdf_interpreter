"""
Test script for the enhanced PDF Chat system with constant PDF injection
Tests the improved flow: PDF → Constant Injection → Token Monitoring → Response
"""
import asyncio
import sys
import os
from pdf_chat_session import PDFChatSession, create_session

class EnhancedSystemTester:
    """Test the enhanced PDF chat system"""
    
    def __init__(self):
        self.test_pdf_path = "JEFES, JEFAS Y ENCARGADOS.pdf"
    
    async def test_constant_pdf_injection(self):
        """Test that PDF content is injected in every message"""
        print("🔄 Testing Constant PDF Injection")
        print("=" * 60)
        
        # Create session and load PDF
        session = create_session("test_constant_injection")
        
        if not session.load_pdf(self.test_pdf_path):
            print("❌ Failed to load PDF")
            return False
        
        # Test questions designed to verify PDF context persistence
        test_questions = [
            "¿Cuál es el número de oficio?",
            "Ahora háblame del clima de hoy",  # Distraction question
            "¿Recuerdas el número de oficio del documento?",  # Memory test
            "¿Qué fecha se menciona en el documento?",
            "Cuéntame sobre los gatos",  # Another distraction
            "¿Cuál era la fecha original del taller en el documento?"  # Final memory test
        ]
        
        print(f"🎯 Testing {len(test_questions)} questions for context persistence...")
        
        context_maintained = 0
        total_questions = 0
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Question {i}/{len(test_questions)} ---")
            print(f"❓ {question}")
            
            result = await session.chat(question)
            
            if not result['success']:
                print(f"❌ Question {i} failed: {result['error']}")
                return False
            
            response = result['response']
            token_info = result['token_info']
            
            print(f"🤖 Response: {response[:100]}...")
            print(f"📊 Tokens: {token_info['total_exchange_tokens']:,} (Session total: {token_info['session_total_tokens']:,})")
            
            # Check if PDF context is maintained
            pdf_keywords = ["oficio", "SEPF", "septiembre", "taller", "SEED"]
            keywords_found = sum(1 for keyword in pdf_keywords if keyword.lower() in response.lower())
            
            total_questions += 1
            if keywords_found >= 1:  # At least one PDF keyword found
                context_maintained += 1
                print(f"✅ PDF context detected: {keywords_found}/{len(pdf_keywords)} keywords")
            else:
                print(f"⚠️ PDF context weak: {keywords_found}/{len(pdf_keywords)} keywords")
        
        success_rate = (context_maintained / total_questions) * 100
        print(f"\n📈 Context Persistence Rate: {success_rate:.1f}% ({context_maintained}/{total_questions})")
        
        # Show session summary
        summary = session.get_session_summary()
        print(f"\n📋 Session Summary:")
        print(f"   - Duration: {summary['duration_minutes']:.1f} minutes")
        print(f"   - Messages: {summary['conversation_info']['message_count']}")
        print(f"   - Total tokens: {summary['conversation_info']['total_tokens_used']:,}")
        print(f"   - Avg tokens/exchange: {summary['conversation_info']['average_tokens_per_exchange']:.0f}")
        
        return success_rate >= 80  # 80% success rate threshold
    
    async def test_token_monitoring(self):
        """Test token monitoring and usage tracking"""
        print("\n🔍 Testing Token Monitoring")
        print("=" * 60)
        
        session = create_session("test_token_monitoring")
        
        if not session.load_pdf(self.test_pdf_path):
            print("❌ Failed to load PDF")
            return False
        
        # Test with progressively longer messages
        test_messages = [
            "Resumen corto",
            "Dame un resumen más detallado del documento con todos los puntos importantes",
            "Ahora necesito que me expliques paso a paso todo el contenido del documento, incluyendo fechas, números de oficio, destinatarios, y cualquier información relevante que puedas encontrar en el texto completo"
        ]
        
        print("📊 Testing token usage with different message lengths...")
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Message {i}/{len(test_messages)} ---")
            print(f"📝 Message length: {len(message)} characters")
            
            result = await session.chat(message)
            
            if not result['success']:
                print(f"❌ Message {i} failed")
                return False
            
            token_info = result['token_info']
            
            print(f"📊 Token breakdown:")
            print(f"   - Message: {token_info['message_tokens']:,}")
            print(f"   - PDF: {token_info['pdf_tokens']:,}")
            print(f"   - History: {token_info['history_tokens']:,}")
            print(f"   - Response: {token_info['response_tokens']:,}")
            print(f"   - Total exchange: {token_info['total_exchange_tokens']:,}")
            print(f"   - Session total: {token_info['session_total_tokens']:,}")
            print(f"   - Gemini usage: {token_info['percentage_used']:.3f}%")
            
            # Verify token monitoring is working
            if token_info['total_tokens'] <= 0:
                print("❌ Token monitoring not working")
                return False
        
        print("\n✅ Token monitoring working correctly")
        return True
    
    async def test_session_management(self):
        """Test session management features"""
        print("\n🗂️ Testing Session Management")
        print("=" * 60)
        
        # Create multiple sessions
        session1 = create_session("test_session_1")
        session2 = create_session("test_session_2")
        
        # Load PDF in first session
        if not session1.load_pdf(self.test_pdf_path):
            print("❌ Failed to load PDF in session 1")
            return False
        
        # Test session isolation
        result1 = await session1.chat("¿Cuál es el número de oficio?")
        
        # Session 2 should not have PDF loaded
        result2 = await session2.chat("¿Cuál es el número de oficio?")
        
        if result1['success'] and not result2['success']:
            print("✅ Session isolation working correctly")
        else:
            print("❌ Session isolation failed")
            return False
        
        # Test session summary
        summary1 = session1.get_session_summary()
        summary2 = session2.get_session_summary()
        
        print(f"📋 Session 1 - PDF loaded: {summary1['pdf_info']['loaded']}")
        print(f"📋 Session 2 - PDF loaded: {summary2['pdf_info']['loaded']}")
        
        # Test conversation clearing
        original_message_count = len(session1.conversation_history)
        session1.clear_conversation()
        new_message_count = len(session1.conversation_history)
        
        if original_message_count > 0 and new_message_count == 0:
            print("✅ Conversation clearing working")
        else:
            print("❌ Conversation clearing failed")
            return False
        
        return True
    
    async def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n⚠️ Testing Error Handling")
        print("=" * 60)
        
        session = create_session("test_error_handling")
        
        # Test chat without PDF loaded
        result = await session.chat("Test message")
        
        if not result['success'] and 'No PDF loaded' in result['error']:
            print("✅ Proper error handling for missing PDF")
        else:
            print("❌ Error handling for missing PDF failed")
            return False
        
        # Test loading non-existent PDF
        if not session.load_pdf("non_existent_file.pdf"):
            print("✅ Proper error handling for missing file")
        else:
            print("❌ Should have failed to load non-existent file")
            return False
        
        return True

async def run_all_tests():
    """Run all enhanced system tests"""
    print("🚀 Enhanced PDF Chat System - Integration Tests")
    print("=" * 70)
    
    tester = EnhancedSystemTester()
    
    # Test 1: Constant PDF injection
    print("\n" + "🔄" * 20 + " TEST 1 " + "🔄" * 20)
    success1 = await tester.test_constant_pdf_injection()
    
    # Test 2: Token monitoring
    print("\n" + "📊" * 20 + " TEST 2 " + "📊" * 20)
    success2 = await tester.test_token_monitoring()
    
    # Test 3: Session management
    print("\n" + "🗂️" * 20 + " TEST 3 " + "🗂️" * 20)
    success3 = await tester.test_session_management()
    
    # Test 4: Error handling
    print("\n" + "⚠️" * 20 + " TEST 4 " + "⚠️" * 20)
    success4 = await tester.test_error_handling()
    
    # Final results
    print("\n" + "=" * 70)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    tests = [
        ("Constant PDF Injection", success1),
        ("Token Monitoring", success2),
        ("Session Management", success3),
        ("Error Handling", success4)
    ]
    
    passed = 0
    for test_name, success in tests:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL ENHANCED TESTS PASSED!")
        print("✅ Constant PDF injection working")
        print("✅ Token monitoring implemented")
        print("✅ Session management robust")
        print("✅ Error handling comprehensive")
        print("✅ System ready for API development")
        return True
    else:
        print(f"\n❌ {len(tests) - passed} tests failed")
        return False

async def interactive_enhanced_test():
    """Interactive test with enhanced features"""
    print("\n🎮 Enhanced Interactive Test Mode")
    print("=" * 60)
    print("Features: Constant PDF injection, Token monitoring, Session management")
    
    session = create_session("interactive_enhanced")
    
    if not session.load_pdf("JEFES, JEFAS Y ENCARGADOS.pdf"):
        print("❌ Failed to load PDF")
        return
    
    print("\n💡 Enhanced PDF chat ready!")
    print("Commands:")
    print("- Ask any question about the PDF")
    print("- Type 'summary' for session summary")
    print("- Type 'clear' to clear conversation")
    print("- Type 'quit' to exit")
    
    while True:
        try:
            user_input = input("\n🗣️  You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'salir']:
                break
            elif user_input.lower() == 'summary':
                summary = session.get_session_summary()
                print(f"\n📊 Session Summary:")
                print(f"   Duration: {summary['duration_minutes']:.1f} min")
                print(f"   Messages: {summary['conversation_info']['message_count']}")
                print(f"   Tokens used: {summary['conversation_info']['total_tokens_used']:,}")
                continue
            elif user_input.lower() == 'clear':
                session.clear_conversation()
                print("🧹 Conversation cleared!")
                continue
            elif not user_input:
                continue
            
            result = await session.chat(user_input)
            
            if result['success']:
                print(f"🤖 AI: {result['response']}")
                token_info = result['token_info']
                print(f"📊 Tokens: {token_info['total_exchange_tokens']:,} (Session: {token_info['session_total_tokens']:,})")
            else:
                print(f"❌ Error: {result['error']}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Enhanced session ended!")
    final_summary = session.get_session_summary()
    print(f"Final stats: {final_summary['conversation_info']['message_count']} messages, {final_summary['conversation_info']['total_tokens_used']:,} tokens")

async def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        await interactive_enhanced_test()
    else:
        success = await run_all_tests()
        
        if success:
            print("\n🎮 Want to try enhanced interactive mode? (y/n)")
            try:
                choice = input().strip().lower()
                if choice in ['y', 'yes', 'si', 's']:
                    await interactive_enhanced_test()
            except KeyboardInterrupt:
                pass
        
        return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error: {e}")
        sys.exit(1)
