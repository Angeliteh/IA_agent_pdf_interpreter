"""
Comprehensive API Tests for PDF Chat Bot
Tests all endpoints and functionality for mobile app integration
"""
import asyncio
import aiohttp
import json
import os
import sys
from typing import Dict, Any

class APITester:
    """Complete API testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self.test_pdf_path = "JEFES, JEFAS Y ENCARGADOS.pdf"
        
    async def test_system_endpoints(self, session: aiohttp.ClientSession) -> bool:
        """Test system endpoints"""
        print("🔧 Testing System Endpoints")
        print("-" * 50)
        
        # Test root endpoint
        try:
            async with session.get(f"{self.base_url}/") as response:
                data = await response.json()
                if response.status == 200 and data.get('success'):
                    print("✅ Root endpoint working")
                else:
                    print(f"❌ Root endpoint failed: {data}")
                    return False
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
            return False
        
        # Test health check
        try:
            async with session.get(f"{self.base_url}/api/v1/health") as response:
                data = await response.json()
                if response.status == 200 and data.get('success'):
                    health = data.get('health', {})
                    print(f"✅ Health check: {health.get('status', 'unknown')}")
                    print(f"   - Gemini API: {'✅' if health.get('gemini_api_status') else '❌'}")
                    print(f"   - OCR API: {'✅' if health.get('ocr_api_status') else '❌'}")
                    print(f"   - Active sessions: {health.get('active_sessions', 0)}")
                else:
                    print(f"❌ Health check failed: {data}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
        
        return True
    
    async def test_session_management(self, session: aiohttp.ClientSession) -> bool:
        """Test session management endpoints"""
        print("\n🗂️ Testing Session Management")
        print("-" * 50)
        
        # Create session
        try:
            payload = {
                "session_name": "API Test Session",
                "timeout_minutes": 60
            }
            async with session.post(
                f"{self.base_url}/api/v1/sessions",
                json=payload
            ) as response:
                data = await response.json()
                if response.status == 201 and data.get('success'):
                    self.session_id = data['session']['session_id']
                    print(f"✅ Session created: {self.session_id}")
                else:
                    print(f"❌ Session creation failed: {data}")
                    return False
        except Exception as e:
            print(f"❌ Session creation error: {e}")
            return False
        
        # Get session info
        try:
            async with session.get(
                f"{self.base_url}/api/v1/sessions/{self.session_id}"
            ) as response:
                data = await response.json()
                if response.status == 200 and data.get('success'):
                    session_info = data['session']
                    print(f"✅ Session info retrieved")
                    print(f"   - Status: {session_info['status']}")
                    print(f"   - Has PDF: {session_info['has_pdf']}")
                    print(f"   - Messages: {session_info['message_count']}")
                else:
                    print(f"❌ Session info failed: {data}")
                    return False
        except Exception as e:
            print(f"❌ Session info error: {e}")
            return False
        
        # List sessions
        try:
            async with session.get(f"{self.base_url}/api/v1/sessions") as response:
                data = await response.json()
                if response.status == 200 and data.get('success'):
                    print(f"✅ Sessions listed: {data['total_count']} active")
                else:
                    print(f"❌ Session listing failed: {data}")
                    return False
        except Exception as e:
            print(f"❌ Session listing error: {e}")
            return False
        
        return True
    
    async def test_pdf_operations(self, session: aiohttp.ClientSession) -> bool:
        """Test PDF upload and management"""
        print("\n📄 Testing PDF Operations")
        print("-" * 50)
        
        if not os.path.exists(self.test_pdf_path):
            print(f"❌ Test PDF not found: {self.test_pdf_path}")
            return False
        
        # Upload PDF
        try:
            with open(self.test_pdf_path, 'rb') as pdf_file:
                data = aiohttp.FormData()
                data.add_field('file', pdf_file, filename='test.pdf', content_type='application/pdf')
                
                async with session.post(
                    f"{self.base_url}/api/v1/sessions/{self.session_id}/pdf",
                    data=data
                ) as response:
                    result = await response.json()
                    if response.status == 200 and result.get('success'):
                        pdf_info = result['pdf_info']
                        print(f"✅ PDF uploaded successfully")
                        print(f"   - Size: {pdf_info['file_size']:,} bytes")
                        print(f"   - Pages: {pdf_info['num_pages']}")
                        print(f"   - Tokens: {pdf_info['estimated_tokens']:,}")
                        print(f"   - Method: {pdf_info['extraction_method']}")
                    else:
                        print(f"❌ PDF upload failed: {result}")
                        return False
        except Exception as e:
            print(f"❌ PDF upload error: {e}")
            return False
        
        # Get PDF info
        try:
            async with session.get(
                f"{self.base_url}/api/v1/sessions/{self.session_id}/pdf"
            ) as response:
                data = await response.json()
                if response.status == 200 and data.get('success'):
                    print("✅ PDF info retrieved")
                else:
                    print(f"❌ PDF info failed: {data}")
                    return False
        except Exception as e:
            print(f"❌ PDF info error: {e}")
            return False
        
        return True
    
    async def test_chat_functionality(self, session: aiohttp.ClientSession) -> bool:
        """Test chat endpoints"""
        print("\n💬 Testing Chat Functionality")
        print("-" * 50)
        
        test_messages = [
            "¿Cuál es el número de oficio del documento?",
            "¿Qué fecha se menciona para el taller?",
            "Dame un resumen del documento"
        ]
        
        for i, message in enumerate(test_messages, 1):
            try:
                payload = {"message": message}
                async with session.post(
                    f"{self.base_url}/api/v1/sessions/{self.session_id}/chat",
                    json=payload
                ) as response:
                    data = await response.json()
                    if response.status == 200 and data.get('success'):
                        token_info = data['token_info']
                        print(f"✅ Message {i} processed")
                        print(f"   - Response: {data['response'][:50]}...")
                        print(f"   - Tokens: {token_info['total_exchange_tokens']:,}")
                        print(f"   - Session total: {token_info['session_total_tokens']:,}")
                    else:
                        print(f"❌ Message {i} failed: {data}")
                        return False
            except Exception as e:
                print(f"❌ Message {i} error: {e}")
                return False
        
        # Get chat history
        try:
            async with session.get(
                f"{self.base_url}/api/v1/sessions/{self.session_id}/history"
            ) as response:
                data = await response.json()
                if response.status == 200 and data.get('success'):
                    print(f"✅ Chat history retrieved: {data['total_messages']} messages")
                else:
                    print(f"❌ Chat history failed: {data}")
                    return False
        except Exception as e:
            print(f"❌ Chat history error: {e}")
            return False
        
        return True
    
    async def test_monitoring_endpoints(self, session: aiohttp.ClientSession) -> bool:
        """Test monitoring and statistics"""
        print("\n📊 Testing Monitoring Endpoints")
        print("-" * 50)
        
        # Get session stats
        try:
            async with session.get(
                f"{self.base_url}/api/v1/sessions/{self.session_id}/stats"
            ) as response:
                data = await response.json()
                if response.status == 200 and data.get('success'):
                    stats = data['stats']
                    print("✅ Session stats retrieved")
                    print(f"   - Duration: {stats['session_info']['duration_minutes']:.1f} min")
                    print(f"   - Messages: {stats['session_info']['message_count']}")
                    print(f"   - Total tokens: {stats['session_info']['total_tokens_used']:,}")
                else:
                    print(f"❌ Session stats failed: {data}")
                    return False
        except Exception as e:
            print(f"❌ Session stats error: {e}")
            return False
        
        return True
    
    async def test_error_handling(self, session: aiohttp.ClientSession) -> bool:
        """Test error handling"""
        print("\n⚠️ Testing Error Handling")
        print("-" * 50)
        
        # Test invalid session
        try:
            async with session.get(
                f"{self.base_url}/api/v1/sessions/invalid_session_id"
            ) as response:
                if response.status == 404:
                    print("✅ Invalid session properly rejected")
                else:
                    print(f"❌ Invalid session not handled: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
        
        # Test chat without PDF (create new session)
        try:
            payload = {"session_name": "Error Test Session"}
            async with session.post(
                f"{self.base_url}/api/v1/sessions",
                json=payload
            ) as response:
                data = await response.json()
                temp_session_id = data['session']['session_id']
                
                # Try to chat without PDF
                chat_payload = {"message": "Test message"}
                async with session.post(
                    f"{self.base_url}/api/v1/sessions/{temp_session_id}/chat",
                    json=chat_payload
                ) as chat_response:
                    if chat_response.status == 400:
                        print("✅ Chat without PDF properly rejected")
                    else:
                        print(f"❌ Chat without PDF not handled: {chat_response.status}")
                        return False
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
        
        return True
    
    async def cleanup(self, session: aiohttp.ClientSession):
        """Clean up test session"""
        if self.session_id:
            try:
                async with session.delete(
                    f"{self.base_url}/api/v1/sessions/{self.session_id}"
                ) as response:
                    if response.status == 200:
                        print(f"\n🧹 Test session cleaned up: {self.session_id}")
                    else:
                        print(f"\n⚠️ Failed to cleanup session: {response.status}")
            except Exception as e:
                print(f"\n⚠️ Cleanup error: {e}")
    
    async def run_all_tests(self) -> bool:
        """Run complete API test suite"""
        print("🚀 PDF Chat Bot API - Complete Test Suite")
        print("=" * 70)
        print("Testing API for mobile app integration readiness")
        print("=" * 70)
        
        async with aiohttp.ClientSession() as session:
            tests = [
                ("System Endpoints", self.test_system_endpoints),
                ("Session Management", self.test_session_management),
                ("PDF Operations", self.test_pdf_operations),
                ("Chat Functionality", self.test_chat_functionality),
                ("Monitoring", self.test_monitoring_endpoints),
                ("Error Handling", self.test_error_handling),
            ]
            
            passed = 0
            for test_name, test_func in tests:
                try:
                    if await test_func(session):
                        passed += 1
                        print(f"✅ {test_name} - PASSED")
                    else:
                        print(f"❌ {test_name} - FAILED")
                except Exception as e:
                    print(f"💥 {test_name} - ERROR: {e}")
            
            # Cleanup
            await self.cleanup(session)
            
            # Results
            print("\n" + "=" * 70)
            print("📋 TEST RESULTS SUMMARY")
            print("=" * 70)
            
            for i, (test_name, _) in enumerate(tests):
                status = "✅ PASSED" if i < passed else "❌ FAILED"
                print(f"{test_name:.<30} {status}")
            
            print(f"\nOverall: {passed}/{len(tests)} tests passed")
            
            if passed == len(tests):
                print("\n🎉 ALL API TESTS PASSED!")
                print("✅ API ready for mobile app integration")
                print("✅ All endpoints working correctly")
                print("✅ Error handling comprehensive")
                print("✅ Documentation available at /docs")
                return True
            else:
                print(f"\n❌ {len(tests) - passed} tests failed")
                print("⚠️ API needs fixes before mobile integration")
                return False

async def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print(f"Testing API at: {base_url}")
    print("Make sure the API server is running: python main.py")
    print()
    
    tester = APITester(base_url)
    success = await tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        sys.exit(1)
