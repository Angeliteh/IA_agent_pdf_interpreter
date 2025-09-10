# Sistema de Chat con PDFs - Documentación Técnica (MEJORADO)

## 🏗️ Arquitectura del Sistema Mejorado

### Flujo Completo de Procesamiento (Versión 2.0)

```
PDF Escaneado → OCR → Texto → Inyección Constante → Gemini → Respuesta
     ↓              ↓         ↓                      ↓         ↓
  233KB PDF    1,660 chars  PDF en CADA mensaje    IA        Usuario
                            + Monitoreo Tokens
```

### ✨ Mejoras Implementadas

- **✅ Inyección Constante del PDF**: El contenido del PDF se incluye en TODOS los mensajes
- **✅ Monitoreo de Tokens**: Seguimiento en tiempo real del uso de tokens
- **✅ Gestión de Sesiones**: Sistema robusto de manejo de sesiones
- **✅ Persistencia de Contexto**: Garantía de que el PDF nunca se "olvida"

## 📄 1. Procesamiento de PDFs

### Extracción de Texto
```python
# pdf_processor.py
def extract_text(pdf_path) -> Tuple[str, str]:
    # 1. Intenta extracción estándar (PDFs con texto)
    # 2. Si falla, usa OCR.space API (PDFs escaneados)
    # 3. Retorna (texto_extraído, método_usado)
```

**Resultado actual:**
- **Entrada**: PDF escaneado de 233KB, 1 página
- **Salida**: 1,660 caracteres de texto limpio
- **Método**: OCR (porque es escaneado)

## 🤖 2. Sistema de Prompts y Contexto (MEJORADO)

### Estructura del Prompt (Sin Cambios)

```python
# llm_client.py - get_system_prompt()
def get_system_prompt(pdf_content=None):
    base_prompt = """
    Recibirás documentos PDF con información formal.
    Tu tarea es resumir y explicar el contenido en lenguaje claro...
    """

    if pdf_content:
        return f"""
        {base_prompt}

        CONTENIDO DEL DOCUMENTO PDF:
        ---
        {pdf_content}  # ← AQUÍ SE INYECTA TODO EL PDF
        ---

        Ahora puedes responder preguntas sobre este documento...
        """
```

### ✨ Gestión de Conversaciones MEJORADA

```python
# llm_client.py - chat() MEJORADO
async def chat(message, pdf_content=None, conversation_history=None):
    # 1. Monitoreo de tokens NUEVO
    token_info = self.get_token_usage_info(message, pdf_content, conversation_history)
    logger.info(f"Token usage: {token_info['total_tokens']:,} tokens")

    # 2. Agregar historial de conversación
    chat_history = []
    if conversation_history:
        for msg in conversation_history:
            chat_history.append({'role': msg['role'], 'parts': [msg['content']]})

    # 3. INYECCIÓN CONSTANTE DEL PDF (CAMBIO PRINCIPAL)
    if pdf_content:
        system_prompt_with_pdf = self.get_system_prompt(pdf_content)
        full_message = f"{system_prompt_with_pdf}\n\nUsuario: {message}"
        logger.info("PDF content injected into message for persistent context")
    else:
        full_message = message

    # 4. Enviar a Gemini
    chat = self.model.start_chat(history=chat_history)
    response = chat.send_message(full_message)
```

### 🔄 Nueva Clase PDFChatSession

```python
# pdf_chat_session.py - NUEVO
class PDFChatSession:
    def __init__(self):
        self.pdf_content = None          # PDF cargado
        self.conversation_history = []   # Historial completo
        self.total_tokens_used = 0      # Monitoreo de tokens
        self.token_usage_history = []   # Historial de uso

    async def chat(self, message):
        # SIEMPRE inyecta PDF + monitorea tokens + actualiza historial
        response = await self.llm_client.chat(
            message=message,
            pdf_content=self.pdf_content,  # ← SIEMPRE presente
            conversation_history=self.conversation_history
        )
        return {'response': response, 'token_info': {...}}
```

## 🔄 3. Flujo de Sesión MEJORADO

### ✨ Sesión = 1 PDF + Conversación + Monitoreo

```
Sesión Iniciada (PDFChatSession)
    ↓
PDF cargado → Texto extraído → Almacenado en sesión
    ↓
Usuario pregunta 1 → PDF + Pregunta → Respuesta 1 + Token tracking
    ↓
Usuario pregunta 2 → PDF + Pregunta + Historial → Respuesta 2 + Token tracking
    ↓
Usuario pregunta N → PDF + Pregunta + Historial → Respuesta N + Token tracking
                     ↑
            INYECCIÓN CONSTANTE
```

### ✅ Gestión de Memoria SOLUCIONADA

**Problema RESUELTO**: El PDF se inyecta en **TODOS los mensajes**.

**Ventajas**:
- ✅ Contexto PDF garantizado en cada respuesta
- ✅ No hay pérdida de información del documento
- ✅ Monitoreo completo de tokens
- ✅ Gestión robusta de sesiones

**Costo**: Ligeramente más tokens por mensaje (pero dentro de límites seguros)

## 📊 4. Análisis de Tokens y Límites

### Cálculo Aproximado de Tokens

```
Prompt base:           ~200 tokens
PDF content (1,660 chars): ~415 tokens (1 token ≈ 4 chars)
Conversación (8 mensajes): ~800 tokens
TOTAL APROXIMADO:      ~1,415 tokens
```

**Límite de Gemini 2.0 Flash**: 1M tokens de entrada
**Nuestro uso actual**: 0.14% del límite ✅

### Proyección para Múltiples PDFs

```
1 PDF (1,660 chars):     ~415 tokens
5 PDFs similares:        ~2,075 tokens
10 PDFs similares:       ~4,150 tokens
Conversación larga:      ~2,000 tokens
TOTAL (10 PDFs):         ~6,150 tokens (0.6% del límite)
```

## 🎯 5. Limitaciones Actuales

### ❌ Problemas Identificados

1. **Inyección única**: PDF solo se inyecta en primer mensaje
2. **Sin segmentación**: No hay separación clara entre PDFs
3. **Sin gestión de tokens**: No monitoreamos el uso
4. **Sesión simple**: Solo 1 PDF por sesión

### ⚠️ Riesgos Potenciales

1. **Conversaciones largas**: Gemini podría perder contexto del PDF
2. **PDFs grandes**: Podrían exceder límites de tokens
3. **Múltiples PDFs**: Sin estructura para diferenciarlos

## 🔧 6. Mejoras Propuestas

### Opción A: Inyección Constante (Recomendada)
```python
# Inyectar PDF en cada mensaje
def chat(message, pdf_content, conversation_history):
    system_prompt_with_pdf = f"""
    {base_prompt}
    
    DOCUMENTO ACTUAL:
    ---
    {pdf_content}
    ---
    
    HISTORIAL DE CONVERSACIÓN:
    {conversation_history}
    
    NUEVA PREGUNTA: {message}
    """
```

### Opción B: Múltiples PDFs con Segmentación
```python
def chat(message, pdf_contents_dict, conversation_history):
    system_prompt = f"""
    {base_prompt}
    
    DOCUMENTOS DISPONIBLES:
    
    DOCUMENTO 1 - "archivo1.pdf":
    ---
    {pdf_contents_dict['doc1']}
    ---
    
    DOCUMENTO 2 - "archivo2.pdf":
    ---
    {pdf_contents_dict['doc2']}
    ---
    
    CONVERSACIÓN PREVIA:
    {conversation_history}
    
    NUEVA PREGUNTA: {message}
    """
```

### Opción C: Monitoreo de Tokens
```python
def estimate_tokens(text):
    return len(text) // 4  # Aproximación

def chat_with_token_management(message, pdf_content, history):
    total_tokens = (
        estimate_tokens(base_prompt) +
        estimate_tokens(pdf_content) +
        estimate_tokens(str(history)) +
        estimate_tokens(message)
    )
    
    if total_tokens > MAX_TOKENS:
        # Truncar historial o segmentar PDF
        pass
```

## 🎯 7. Recomendación Inmediata

### Para el MVP (Mínimo Producto Viable):

1. **Mantener**: 1 PDF por sesión
2. **Implementar**: Inyección constante del PDF
3. **Agregar**: Monitoreo básico de tokens
4. **Preparar**: Estructura para múltiples PDFs a futuro

### Código Propuesto:
```python
class PDFChatSession:
    def __init__(self):
        self.pdf_content = None
        self.pdf_filename = None
        self.conversation_history = []
        self.token_count = 0
    
    def load_pdf(self, pdf_path):
        # Cargar y procesar PDF
        pass
    
    async def chat(self, message):
        # Inyectar PDF + historial en cada mensaje
        pass
    
    def get_token_usage(self):
        # Monitorear uso de tokens
        pass
```

## ✅ MEJORAS IMPLEMENTADAS (v2.0)

### 🎯 Cambios Realizados

1. **✅ Inyección constante del PDF** - IMPLEMENTADO
2. **✅ Monitoreo de tokens** - IMPLEMENTADO
3. **✅ Gestión robusta de sesiones** - IMPLEMENTADO
4. **✅ Sistema preparado para API** - LISTO

### 📁 Nuevos Archivos

- `pdf_chat_session.py` - Clase mejorada para manejo de sesiones
- `test_enhanced_system.py` - Tests completos del sistema mejorado

### 🔧 Archivos Modificados

- `llm_client.py` - Inyección constante + monitoreo de tokens
- `SYSTEM_DOCUMENTATION.md` - Documentación actualizada

### 🚀 Próximos Pasos

1. **✅ Sistema LLM mejorado** - COMPLETADO
2. **✅ Inyección constante PDF** - COMPLETADO
3. **✅ Monitoreo de tokens** - COMPLETADO
4. **🔄 Backend con FastAPI** - SIGUIENTE (base sólida lista)
5. **⏳ Frontend básico** - Pendiente

### 💡 Características del Sistema v2.0

- **Modelo**: Gemini 2.0 Flash (1M tokens de contexto)
- **Enfoque**: Documentos administrativos con contexto persistente
- **Estilo**: Respuestas claras con información siempre disponible
- **Contexto**: Inyección del PDF completo en CADA mensaje
- **Monitoreo**: Tracking completo de uso de tokens
- **Sesiones**: Gestión robusta con timeouts y limpieza automática
- **PDFs**: Procesamiento híbrido (texto estándar + OCR)
- **Escalabilidad**: Preparado para múltiples sesiones concurrentes
