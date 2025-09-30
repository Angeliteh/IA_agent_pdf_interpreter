"""
Test Interactivo para Validación Humana de Múltiples PDFs
Similar a test_enhanced_system.py pero enfocado en validación práctica
"""
import asyncio
import sys
import os
from pdf_chat_session import create_session

class HumanValidationTester:
    """Tester interactivo para validación humana"""
    
    def __init__(self):
        self.test_scenarios = {
            'single_pdf': {
                'name': 'UN SOLO PDF',
                'pdfs': ['/home/parrot/bot-trascription/pdfs_pruebas/prueba1/JEFES, JEFAS Y ENCARGADOS.pdf'],
                'pdf_names': ['Documento_Jefes.pdf'],
                'test_questions': [
                    "¿De qué trata este documento?",
                    "¿Quién envía este documento?",
                    "¿Cuál es el asunto del documento?",
                    "¿A quién está dirigido?",
                    "¿Hay alguna fecha mencionada?"
                ]
            },
            'multiple_pdfs': {
                'name': 'MÚLTIPLES PDFs',
                'pdfs': [
                    '/home/parrot/bot-trascription/pdfs_pruebas/prueba2/OFICIO 2006-25 JEFA, JEFES Y ENCARGDOS DE SECTOR INFORMACIÓN SOBRE LOS EIA.pdf',
                    '/home/parrot/bot-trascription/pdfs_pruebas/prueba2/VACUNA VHP.pdf'
                ],
                'pdf_names': ['Oficio_EIA.pdf', 'Vacuna_VHP.pdf'],
                'test_questions': [
                    "¿Cuántos documentos tienes?",
                    "¿Cuáles son los nombres de los documentos?",
                    "¿De qué trata cada documento?",
                    "¿Cuál documento habla sobre vacunas?",
                    "¿Cuál documento habla sobre EIA?",
                    "¿Hay alguna relación entre los dos documentos?",
                    "Dame un resumen de cada documento",
                    "¿Qué documento es más reciente?",
                    "¿Ambos documentos son de la misma institución?"
                ]
            }
        }
    
    def print_header(self, title):
        """Imprimir encabezado bonito"""
        print(f"\n{'='*60}")
        print(f"🎯 {title}")
        print(f"{'='*60}")
    
    def print_section(self, title):
        """Imprimir sección"""
        print(f"\n{'─'*40}")
        print(f"📋 {title}")
        print(f"{'─'*40}")
    
    async def setup_session(self, scenario_key):
        """Configurar sesión con PDFs del escenario"""
        scenario = self.test_scenarios[scenario_key]
        session = create_session(f"human_test_{scenario_key}")
        
        print(f"\n🔧 Configurando sesión: {scenario['name']}")
        
        # Cargar PDFs
        for i, (pdf_path, pdf_name) in enumerate(zip(scenario['pdfs'], scenario['pdf_names'])):
            if not os.path.exists(pdf_path):
                print(f"❌ PDF no encontrado: {pdf_path}")
                return None
            
            print(f"📄 Cargando PDF {i+1}/{len(scenario['pdfs'])}: {pdf_name}")
            if not session.load_pdf(pdf_path, pdf_name):
                print(f"❌ Error cargando PDF: {pdf_name}")
                return None
            print(f"✅ PDF cargado: {pdf_name}")
        
        # Mostrar información de la sesión
        print(f"\n📊 Información de la sesión:")
        print(f"   - PDFs cargados: {len(session.pdfs)}")
        print(f"   - Contenido total: {len(session.combined_pdf_content):,} caracteres")
        print(f"   - Tokens estimados: {session.llm_client.estimate_tokens(session.combined_pdf_content):,}")
        
        return session
    
    def show_prompt_structure(self, session):
        """Mostrar estructura del prompt para validación humana"""
        self.print_section("ESTRUCTURA DEL PROMPT")
        
        # Obtener prompt completo
        full_prompt = session.llm_client.get_system_prompt(session.combined_pdf_content)
        
        print(f"📊 Estadísticas del prompt:")
        print(f"   - Longitud: {len(full_prompt):,} caracteres")
        print(f"   - Tokens: {session.llm_client.estimate_tokens(full_prompt):,}")
        
        # Mostrar primeras líneas del prompt
        print(f"\n🔍 Primeras líneas del prompt:")
        print("─" * 50)
        lines = full_prompt.split('\n')
        for i, line in enumerate(lines[:15]):
            print(f"{i+1:2d}: {line}")
        print("... (resto del prompt)")
        print("─" * 50)
        
        # Mostrar estructura de documentos
        print(f"\n📄 Estructura de documentos en el prompt:")
        content = session.combined_pdf_content
        doc_markers = []
        for line in content.split('\n'):
            if 'DOCUMENTO #' in line:
                doc_markers.append(line.strip())
        
        for marker in doc_markers:
            print(f"   ✅ {marker}")
        
        if len(doc_markers) > 1:
            print(f"   🎯 Detectados {len(doc_markers)} documentos separados")
        else:
            print(f"   📄 Un solo documento")
    
    async def interactive_chat(self, session, scenario_key):
        """Chat interactivo con preguntas predefinidas y libres"""
        scenario = self.test_scenarios[scenario_key]
        
        self.print_section("PREGUNTAS PREDEFINIDAS")
        
        print(f"🎯 Probando {len(scenario['test_questions'])} preguntas predefinidas:")
        
        for i, question in enumerate(scenario['test_questions'], 1):
            print(f"\n{'─'*30}")
            print(f"❓ Pregunta {i}/{len(scenario['test_questions'])}: {question}")
            print("─" * 30)
            
            # Enviar pregunta
            result = await session.chat(question)
            
            if result['success']:
                response = result['response']
                print(f"🤖 Respuesta:")
                print(f"{response}")
                print(f"\n📊 Tokens: {result['token_info']['total_exchange_tokens']:,}")
                
                # Pausa para que el usuario pueda leer
                input("\n⏸️  Presiona ENTER para continuar...")
            else:
                print(f"❌ Error: {result['error']}")
                return False
        
        # Chat libre
        self.print_section("CHAT LIBRE")
        print("💬 Ahora puedes hacer preguntas libres. Escribe 'salir' para terminar.")
        
        while True:
            try:
                user_question = input("\n❓ Tu pregunta: ").strip()
                
                if user_question.lower() in ['salir', 'exit', 'quit', '']:
                    break
                
                result = await session.chat(user_question)
                
                if result['success']:
                    print(f"\n🤖 Respuesta:")
                    print(f"{result['response']}")
                    print(f"\n📊 Tokens: {result['token_info']['total_exchange_tokens']:,}")
                else:
                    print(f"❌ Error: {result['error']}")
                    
            except KeyboardInterrupt:
                print("\n⏹️ Chat interrumpido")
                break
        
        return True
    
    async def run_scenario(self, scenario_key):
        """Ejecutar un escenario completo"""
        scenario = self.test_scenarios[scenario_key]
        
        self.print_header(f"ESCENARIO: {scenario['name']}")
        
        # Configurar sesión
        session = await self.setup_session(scenario_key)
        if not session:
            print("❌ Error configurando sesión")
            return False
        
        # Mostrar estructura del prompt
        self.show_prompt_structure(session)
        
        # Confirmar si continuar
        print(f"\n🎯 ¿Todo se ve bien? ¿Continuar con las preguntas?")
        continue_test = input("✅ Presiona ENTER para continuar o 'n' para saltar: ").strip().lower()
        
        if continue_test == 'n':
            print("⏭️ Escenario saltado")
            return True
        
        # Chat interactivo
        success = await self.interactive_chat(session, scenario_key)
        
        if success:
            print(f"\n✅ Escenario '{scenario['name']}' completado")
        else:
            print(f"\n❌ Escenario '{scenario['name']}' falló")
        
        return success

async def main():
    """Ejecutar validación humana completa"""
    print("🧪 VALIDACIÓN HUMANA DE MÚLTIPLES PDFs")
    print("=" * 60)
    print("Este test te permite validar manualmente que el sistema")
    print("responde correctamente a preguntas sobre uno o múltiples PDFs.")
    print("=" * 60)
    
    tester = HumanValidationTester()
    
    # Verificar PDFs
    all_pdfs = []
    for scenario in tester.test_scenarios.values():
        all_pdfs.extend(scenario['pdfs'])
    
    missing_pdfs = [pdf for pdf in all_pdfs if not os.path.exists(pdf)]
    if missing_pdfs:
        print("❌ PDFs faltantes:")
        for pdf in missing_pdfs:
            print(f"   - {pdf}")
        return 1
    
    print("✅ Todos los PDFs encontrados")
    
    # Menú de escenarios
    scenarios = list(tester.test_scenarios.keys())
    
    print(f"\n📋 Escenarios disponibles:")
    for i, key in enumerate(scenarios, 1):
        scenario = tester.test_scenarios[key]
        print(f"   {i}. {scenario['name']} ({len(scenario['pdfs'])} PDF{'s' if len(scenario['pdfs']) > 1 else ''})")
    print(f"   0. Ejecutar todos")
    
    try:
        choice = input(f"\n🎯 Selecciona escenario (0-{len(scenarios)}): ").strip()
        
        if choice == '0':
            # Ejecutar todos
            for key in scenarios:
                success = await tester.run_scenario(key)
                if not success:
                    print(f"\n⚠️ Escenario {key} tuvo problemas")
        elif choice.isdigit() and 1 <= int(choice) <= len(scenarios):
            # Ejecutar escenario específico
            selected_key = scenarios[int(choice) - 1]
            await tester.run_scenario(selected_key)
        else:
            print("❌ Opción inválida")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrumpido")
        return 1
    
    print(f"\n🎉 VALIDACIÓN HUMANA COMPLETADA")
    print("=" * 60)
    print("Ahora tienes una idea clara de cómo responde el sistema")
    print("a preguntas reales sobre uno o múltiples PDFs.")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrumpido")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error: {e}")
        sys.exit(1)
