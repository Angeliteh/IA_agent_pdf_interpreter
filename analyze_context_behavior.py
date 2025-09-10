"""
Script para analizar el comportamiento del contexto y tokens en el sistema
"""
import asyncio
import sys
from pdf_processor import get_pdf_processor
from llm_client import get_gemini_client

class ContextAnalyzer:
    """Analiza el comportamiento del contexto y tokens"""
    
    def __init__(self):
        self.pdf_processor = get_pdf_processor()
        self.llm_client = get_gemini_client()
    
    def estimate_tokens(self, text: str) -> int:
        """Estima tokens usando la regla 1 token ≈ 4 caracteres"""
        return len(text) // 4
    
    def analyze_pdf_content(self, pdf_path: str):
        """Analiza el contenido del PDF y su impacto en tokens"""
        print("📄 Analizando contenido del PDF...")
        
        # Extraer texto
        text, method = self.pdf_processor.extract_text(pdf_path)
        
        # Análisis básico
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.split('\n'))
        estimated_tokens = self.estimate_tokens(text)
        
        print(f"📊 Estadísticas del PDF:")
        print(f"   - Caracteres: {char_count:,}")
        print(f"   - Palabras: {word_count:,}")
        print(f"   - Líneas: {line_count}")
        print(f"   - Tokens estimados: {estimated_tokens:,}")
        print(f"   - Método extracción: {method}")
        
        return text, estimated_tokens
    
    def analyze_prompt_structure(self, pdf_content: str):
        """Analiza la estructura del prompt con PDF"""
        print("\n🔍 Analizando estructura del prompt...")
        
        # Obtener prompt base
        base_prompt = self.llm_client.get_system_prompt()
        base_tokens = self.estimate_tokens(base_prompt)
        
        # Obtener prompt con PDF
        prompt_with_pdf = self.llm_client.get_system_prompt(pdf_content)
        full_tokens = self.estimate_tokens(prompt_with_pdf)
        
        pdf_tokens = full_tokens - base_tokens
        
        print(f"📝 Análisis del prompt:")
        print(f"   - Prompt base: {base_tokens:,} tokens")
        print(f"   - PDF content: {pdf_tokens:,} tokens")
        print(f"   - Prompt total: {full_tokens:,} tokens")
        print(f"   - Overhead del sistema: {((full_tokens - pdf_tokens) / full_tokens * 100):.1f}%")
        
        return base_tokens, pdf_tokens, full_tokens
    
    async def test_context_persistence(self, pdf_content: str):
        """Prueba si el contexto del PDF se mantiene en conversaciones largas"""
        print("\n🔄 Probando persistencia del contexto...")
        
        conversation_history = []
        
        # Serie de preguntas para probar memoria
        test_questions = [
            "¿Cuál es el número de oficio del documento?",
            "¿Qué fecha se menciona para el evento?", 
            "¿Cuál era la fecha original?",
            "¿Qué diferencia hay entre las dos fechas?",
            "¿Recuerdas el número de oficio que mencioné al principio?",  # Test de memoria
            "¿Puedes repetir las fechas que hemos discutido?",  # Test de memoria
        ]
        
        total_tokens = 0
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Pregunta {i}/{len(test_questions)} ---")
            print(f"❓ {question}")
            
            # Calcular tokens antes del mensaje
            question_tokens = self.estimate_tokens(question)
            history_tokens = self.estimate_tokens(str(conversation_history))
            
            print(f"📊 Tokens antes: Pregunta={question_tokens}, Historial={history_tokens}")
            
            # Enviar mensaje
            response = await self.llm_client.chat(
                message=question,
                pdf_content=pdf_content,  # PDF en TODOS los mensajes (después del fix)
                conversation_history=conversation_history
            )
            
            # Actualizar historial
            conversation_history.append({'role': 'user', 'content': question})
            conversation_history.append({'role': 'assistant', 'content': response})
            
            response_tokens = self.estimate_tokens(response)
            total_tokens += question_tokens + response_tokens
            
            print(f"💬 Respuesta ({response_tokens} tokens): {response[:100]}...")
            print(f"📈 Tokens acumulados: {total_tokens:,}")
            
            # Verificar si la respuesta contiene información del PDF
            pdf_keywords = ["oficio", "SEPF", "septiembre", "taller", "SEED"]
            keywords_found = sum(1 for keyword in pdf_keywords if keyword.lower() in response.lower())
            
            print(f"🎯 Contexto PDF detectado: {keywords_found}/{len(pdf_keywords)} keywords")
            
            if keywords_found < 2 and i > 3:
                print("⚠️ POSIBLE PÉRDIDA DE CONTEXTO PDF")
        
        return conversation_history, total_tokens
    
    async def test_token_limits(self, pdf_content: str):
        """Prueba comportamiento cerca de límites de tokens"""
        print("\n🚨 Probando límites de tokens...")
        
        # Simular conversación muy larga
        long_history = []
        
        # Crear historial artificial largo
        for i in range(50):  # 50 intercambios
            long_history.append({
                'role': 'user', 
                'content': f"Esta es la pregunta número {i+1} sobre el documento. ¿Puedes confirmar que aún recuerdas el contenido del PDF?"
            })
            long_history.append({
                'role': 'assistant',
                'content': f"Sí, recuerdo el documento. Esta es mi respuesta número {i+1} con detalles adicionales sobre el contenido que hemos estado discutiendo."
            })
        
        history_tokens = self.estimate_tokens(str(long_history))
        pdf_tokens = self.estimate_tokens(pdf_content)
        
        print(f"📊 Simulación de conversación larga:")
        print(f"   - Historial: {history_tokens:,} tokens")
        print(f"   - PDF: {pdf_tokens:,} tokens")
        print(f"   - Total estimado: {history_tokens + pdf_tokens:,} tokens")
        
        # Límites de Gemini
        gemini_limit = 1_000_000  # 1M tokens
        percentage_used = ((history_tokens + pdf_tokens) / gemini_limit) * 100
        
        print(f"   - % del límite Gemini: {percentage_used:.3f}%")
        
        if percentage_used > 50:
            print("⚠️ ADVERTENCIA: Cerca del límite de tokens")
        elif percentage_used > 80:
            print("🚨 CRÍTICO: Muy cerca del límite")
        else:
            print("✅ Uso de tokens dentro de límites seguros")

async def main():
    """Ejecuta todos los análisis"""
    print("🔍 Análisis del Sistema de Contexto y Tokens")
    print("=" * 60)
    
    analyzer = ContextAnalyzer()
    pdf_path = "JEFES, JEFAS Y ENCARGADOS.pdf"
    
    # 1. Analizar PDF
    pdf_content, pdf_tokens = analyzer.analyze_pdf_content(pdf_path)
    
    # 2. Analizar estructura del prompt
    base_tokens, content_tokens, total_tokens = analyzer.analyze_prompt_structure(pdf_content)
    
    # 3. Probar persistencia del contexto
    history, conversation_tokens = await analyzer.test_context_persistence(pdf_content)
    
    # 4. Probar límites de tokens
    await analyzer.test_token_limits(pdf_content)
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL ANÁLISIS")
    print("=" * 60)
    print(f"PDF tokens: {pdf_tokens:,}")
    print(f"Prompt base tokens: {base_tokens:,}")
    print(f"Conversación real tokens: {conversation_tokens:,}")
    print(f"Total tokens usados: {pdf_tokens + base_tokens + conversation_tokens:,}")
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    
    if conversation_tokens > pdf_tokens * 2:
        print("- ⚠️ La conversación usa más tokens que el PDF")
        print("- 💡 Considerar truncar historial en conversaciones largas")
    
    if pdf_tokens > 1000:
        print("- ⚠️ PDF relativamente grande en tokens")
        print("- 💡 Considerar segmentación para PDFs más grandes")
    
    print("- ✅ Implementar monitoreo de tokens en producción")
    print("- ✅ Considerar inyección constante del PDF para mejor contexto")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Análisis interrumpido")
    except Exception as e:
        print(f"\n💥 Error: {e}")
