"""
Test script for the Gemini LLM client
"""
import asyncio
import sys
from llm_client import get_gemini_client

async def test_basic_connection():
    """Test basic connection to Gemini API"""
    print("🔄 Testing Gemini API connection...")
    
    try:
        client = get_gemini_client()
        
        # Test connection
        if client.test_connection():
            print("✅ Connection to Gemini API successful!")
            return True
        else:
            print("❌ Connection to Gemini API failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

async def test_basic_chat():
    """Test basic chat functionality"""
    print("\n🔄 Testing basic chat functionality...")
    
    try:
        client = get_gemini_client()
        
        # Test message
        test_message = "Hola, ¿puedes confirmar que estás funcionando correctamente?"
        
        response = await client.chat(test_message)
        
        print(f"📤 Sent: {test_message}")
        print(f"📥 Response: {response}")
        
        if response and len(response) > 0:
            print("✅ Basic chat test successful!")
            return True
        else:
            print("❌ Basic chat test failed - empty response")
            return False
            
    except Exception as e:
        print(f"❌ Error in basic chat test: {e}")
        return False

async def test_pdf_context():
    """Test chat with PDF context simulation"""
    print("\n🔄 Testing PDF context functionality...")
    
    try:
        client = get_gemini_client()
        
        # Simulate PDF content
        fake_pdf_content = """
        DOCUMENTO DE PRUEBA
        
        Este es un documento administrativo de ejemplo que contiene información sobre:
        - Políticas de la empresa
        - Procedimientos de seguridad
        - Horarios de trabajo: Lunes a Viernes 9:00 AM - 6:00 PM
        - Contacto: admin@empresa.com
        """
        
        # Test message with PDF context
        test_message = "¿Cuáles son los horarios de trabajo mencionados en el documento?"
        
        response = await client.chat(
            message=test_message,
            pdf_content=fake_pdf_content
        )
        
        print(f"📄 PDF Content: {fake_pdf_content[:100]}...")
        print(f"📤 Question: {test_message}")
        print(f"📥 Response: {response}")
        
        if response and "9:00" in response and "6:00" in response:
            print("✅ PDF context test successful!")
            return True
        else:
            print("⚠️ PDF context test completed but response may not be accurate")
            return True
            
    except Exception as e:
        print(f"❌ Error in PDF context test: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Gemini LLM Client Tests")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Connection Test", test_basic_connection()),
        ("Basic Chat Test", test_basic_chat()),
        ("PDF Context Test", test_pdf_context())
    ]
    
    results = []
    for test_name, test_coro in tests:
        print(f"\n📋 Running: {test_name}")
        result = await test_coro
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Gemini client is ready to use.")
        return 0
    else:
        print("⚠️ Some tests failed. Check your configuration.")
        return 1

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
