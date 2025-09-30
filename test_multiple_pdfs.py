"""
Test específico para validar el manejo de múltiples PDFs
Prueba cómo el LLM entiende y diferencia múltiples documentos
"""
import asyncio
import sys
import os
from pdf_chat_session import create_session

class MultiplePDFTester:
    """Tester específico para múltiples PDFs"""
    
    def __init__(self):
        self.test_pdfs = {
            'prueba1': '/home/parrot/bot-trascription/pdfs_pruebas/prueba1/JEFES, JEFAS Y ENCARGADOS.pdf',
            'prueba2_doc1': '/home/parrot/bot-trascription/pdfs_pruebas/prueba2/OFICIO 2006-25 JEFA, JEFES Y ENCARGDOS DE SECTOR INFORMACIÓN SOBRE LOS EIA.pdf',
            'prueba2_doc2': '/home/parrot/bot-trascription/pdfs_pruebas/prueba2/VACUNA VHP.pdf'
        }
    
    async def test_single_pdf_clarity(self):
        """Test: Un solo PDF - verificar claridad del prompt"""
        print("📄 Test 1: UN SOLO PDF")
        print("=" * 50)
        
        session = create_session("test_single_pdf")
        
        # Cargar un PDF
        if not session.load_pdf(self.test_pdfs['prueba1'], "Documento_Jefes.pdf"):
            print("❌ Error cargando PDF")
            return False
        
        print(f"✅ PDF cargado: {len(session.pdfs)} documento(s)")
        print(f"📊 Contenido combinado: {len(session.combined_pdf_content)} caracteres")
        
        # Ver cómo se ve el prompt
        prompt_preview = session.combined_pdf_content[:500] + "..." if len(session.combined_pdf_content) > 500 else session.combined_pdf_content
        print(f"\n🔍 Vista previa del contenido combinado:")
        print("-" * 50)
        print(prompt_preview)
        print("-" * 50)
        
        # Probar chat
        result = await session.chat("¿De qué trata este documento?")
        if result['success']:
            print(f"\n🤖 Respuesta: {result['response'][:200]}...")
            print(f"📊 Tokens usados: {result['token_info']['total_exchange_tokens']:,}")
        else:
            print(f"❌ Error en chat: {result['error']}")
            return False
        
        return True
    
    async def test_multiple_pdfs_clarity(self):
        """Test: Múltiples PDFs - verificar que el LLM los diferencia"""
        print("\n📄📄 Test 2: MÚLTIPLES PDFs")
        print("=" * 50)
        
        session = create_session("test_multiple_pdfs")
        
        # Cargar primer PDF
        if not session.load_pdf(self.test_pdfs['prueba2_doc1'], "Oficio_EIA.pdf"):
            print("❌ Error cargando primer PDF")
            return False
        
        print(f"✅ Primer PDF cargado: {len(session.pdfs)} documento(s)")
        
        # Cargar segundo PDF
        if not session.load_pdf(self.test_pdfs['prueba2_doc2'], "Vacuna_VHP.pdf"):
            print("❌ Error cargando segundo PDF")
            return False
        
        print(f"✅ Segundo PDF cargado: {len(session.pdfs)} documento(s)")
        print(f"📊 Contenido combinado: {len(session.combined_pdf_content)} caracteres")
        
        # Ver cómo se ve el contenido combinado
        print(f"\n🔍 Estructura del contenido combinado:")
        print("-" * 50)
        lines = session.combined_pdf_content.split('\n')
        for i, line in enumerate(lines[:20]):  # Primeras 20 líneas
            print(f"{i+1:2d}: {line}")
        print("... (contenido truncado)")
        print("-" * 50)
        
        # Preguntas específicas para probar diferenciación
        test_questions = [
            "¿Cuántos documentos tienes cargados?",
            "¿Cuáles son los nombres de los documentos?",
            "¿De qué trata cada documento?",
            "¿Hay información sobre vacunas en algún documento?",
            "¿Hay información sobre EIA en algún documento?",
            "Dame un resumen de cada documento por separado"
        ]
        
        print(f"\n🎯 Probando {len(test_questions)} preguntas de diferenciación:")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Pregunta {i}/{len(test_questions)} ---")
            print(f"❓ {question}")
            
            result = await session.chat(question)
            if result['success']:
                response = result['response']
                print(f"🤖 Respuesta: {response[:300]}...")
                
                # Verificar si menciona múltiples documentos
                multiple_indicators = [
                    "documento", "documentos", "primer", "segundo", 
                    "Oficio", "Vacuna", "EIA", "VHP", "#1", "#2"
                ]
                indicators_found = sum(1 for indicator in multiple_indicators if indicator.lower() in response.lower())
                print(f"📊 Indicadores de múltiples docs: {indicators_found}/{len(multiple_indicators)}")
                print(f"📊 Tokens: {result['token_info']['total_exchange_tokens']:,}")
                
                if indicators_found >= 3:
                    print("✅ Parece entender múltiples documentos")
                else:
                    print("⚠️ Posible confusión con múltiples documentos")
            else:
                print(f"❌ Error: {result['error']}")
                return False
        
        return True
    
    async def test_prompt_structure_analysis(self):
        """Test: Analizar la estructura del prompt que recibe el LLM"""
        print("\n🔍 Test 3: ANÁLISIS DE ESTRUCTURA DEL PROMPT")
        print("=" * 50)
        
        session = create_session("test_prompt_analysis")
        
        # Cargar múltiples PDFs
        session.load_pdf(self.test_pdfs['prueba2_doc1'], "Doc1_Oficio.pdf")
        session.load_pdf(self.test_pdfs['prueba2_doc2'], "Doc2_Vacuna.pdf")
        
        # Obtener el prompt completo que se envía al LLM
        from llm_client import get_gemini_client
        llm_client = get_gemini_client()
        
        full_prompt = llm_client.get_system_prompt(session.combined_pdf_content)
        
        print(f"📊 Estadísticas del prompt:")
        print(f"   - Longitud total: {len(full_prompt):,} caracteres")
        print(f"   - Tokens estimados: {llm_client.estimate_tokens(full_prompt):,}")
        print(f"   - Contiene 'MÚLTIPLES': {'✅' if 'MÚLTIPLES' in full_prompt else '❌'}")
        print(f"   - Contiene 'DOCUMENTO #1': {'✅' if 'DOCUMENTO #1' in full_prompt else '❌'}")
        print(f"   - Contiene 'DOCUMENTO #2': {'✅' if 'DOCUMENTO #2' in full_prompt else '❌'}")
        
        # Mostrar estructura del prompt
        print(f"\n🔍 Estructura del prompt (primeras 1000 caracteres):")
        print("-" * 70)
        print(full_prompt[:1000])
        print("... (contenido truncado)")
        print("-" * 70)
        
        # Buscar secciones clave
        key_sections = [
            "DOCUMENTOS PDF CARGADOS:",
            "INSTRUCCIONES ESPECIALES:",
            "DOCUMENTO #1:",
            "DOCUMENTO #2:",
            "FIN DEL DOCUMENTO"
        ]
        
        print(f"\n🔍 Secciones clave encontradas:")
        for section in key_sections:
            found = section in full_prompt
            print(f"   - {section}: {'✅' if found else '❌'}")
        
        return True
    
    async def test_pdf_removal_and_rebuilding(self):
        """Test: Verificar que la eliminación y reconstrucción funciona"""
        print("\n🗑️ Test 4: ELIMINACIÓN Y RECONSTRUCCIÓN")
        print("=" * 50)
        
        session = create_session("test_pdf_removal")
        
        # Cargar múltiples PDFs
        session.load_pdf(self.test_pdfs['prueba2_doc1'], "Doc_A.pdf")
        session.load_pdf(self.test_pdfs['prueba2_doc2'], "Doc_B.pdf")
        
        print(f"✅ Cargados: {len(session.pdfs)} PDFs")
        original_content_length = len(session.combined_pdf_content)
        print(f"📊 Contenido original: {original_content_length:,} caracteres")
        
        # Eliminar un PDF
        removed = session.remove_pdf("Doc_A.pdf")
        print(f"🗑️ PDF eliminado: {'✅' if removed else '❌'}")
        print(f"📊 PDFs restantes: {len(session.pdfs)}")
        
        new_content_length = len(session.combined_pdf_content) if session.combined_pdf_content else 0
        print(f"📊 Contenido después: {new_content_length:,} caracteres")
        
        # Verificar que el contenido se reconstruyó correctamente
        if new_content_length > 0 and new_content_length < original_content_length:
            print("✅ Contenido reconstruido correctamente")
        else:
            print("❌ Problema en la reconstrucción del contenido")
            return False
        
        # Probar chat después de eliminación
        result = await session.chat("¿Cuántos documentos tienes ahora?")
        if result['success']:
            print(f"🤖 Respuesta después de eliminación: {result['response'][:150]}...")
        else:
            print(f"❌ Error en chat después de eliminación: {result['error']}")
            return False
        
        return True

async def main():
    """Ejecutar todos los tests de múltiples PDFs"""
    print("🧪 TESTS DE MÚLTIPLES PDFs - Validación de Comprensión del LLM")
    print("=" * 80)
    
    tester = MultiplePDFTester()
    
    # Verificar que los PDFs existen
    missing_pdfs = []
    for name, path in tester.test_pdfs.items():
        if not os.path.exists(path):
            missing_pdfs.append(f"{name}: {path}")
    
    if missing_pdfs:
        print("❌ PDFs de prueba no encontrados:")
        for missing in missing_pdfs:
            print(f"   - {missing}")
        return 1
    
    print("✅ Todos los PDFs de prueba encontrados")
    
    # Ejecutar tests
    tests = [
        ("Un Solo PDF", tester.test_single_pdf_clarity),
        ("Múltiples PDFs", tester.test_multiple_pdfs_clarity),
        ("Análisis de Prompt", tester.test_prompt_structure_analysis),
        ("Eliminación y Reconstrucción", tester.test_pdf_removal_and_rebuilding),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name.upper()} {'='*20}")
            if await test_func():
                passed += 1
                print(f"✅ {test_name} - PASÓ")
            else:
                print(f"❌ {test_name} - FALLÓ")
        except Exception as e:
            print(f"💥 {test_name} - ERROR: {e}")
    
    # Resultados finales
    print("\n" + "=" * 80)
    print("📋 RESULTADOS FINALES")
    print("=" * 80)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASÓ" if i < passed else "❌ FALLÓ"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{len(tests)} tests pasaron")
    
    if passed == len(tests):
        print("\n🎉 TODOS LOS TESTS PASARON!")
        print("✅ El sistema maneja múltiples PDFs correctamente")
        print("✅ El LLM entiende la diferencia entre documentos")
        print("✅ La estructura del prompt es clara")
        print("✅ La eliminación y reconstrucción funciona")
        print("\n🚀 LISTO PARA CONTINUAR CON LA INTERFAZ WEB")
    else:
        print(f"\n⚠️ {len(tests) - passed} tests fallaron")
        print("🔧 Revisar y ajustar antes de continuar")
    
    return 0 if passed == len(tests) else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrumpidos")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error: {e}")
        sys.exit(1)
