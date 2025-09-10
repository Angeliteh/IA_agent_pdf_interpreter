# PDF Chat Bot

Un sistema de chat inteligente para procesar y analizar documentos PDF usando Gemini 2.0 Flash.

## 🚀 Configuración Inicial

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

1. Copia el archivo de ejemplo:
```bash
cp .env.example .env
```

2. Edita `.env` y reemplaza `your_gemini_api_key_here` con tu API key real de Gemini:
```
GEMINI_API_KEY=tu_api_key_aqui
```

### 3. Obtener API Key de Gemini

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una nueva API key
3. Cópiala y pégala en tu archivo `.env`

## 🧪 Probar el Sistema LLM

Una vez configurado, puedes probar que todo funciona:

```bash
python test_llm.py
```

Este script ejecutará:
- ✅ Test de conexión a Gemini API
- ✅ Test de chat básico
- ✅ Test de contexto PDF simulado

## 📁 Estructura del Proyecto

```
bot-trascription/
├── config.py              # Configuración del sistema
├── llm_client.py           # Cliente de Gemini
├── pdf_processor.py        # Procesador híbrido de PDFs (texto + OCR)
├── test_llm.py             # Tests del sistema LLM
├── test_pdf_processor.py   # Tests del procesador de PDFs
├── requirements.txt        # Dependencias
├── .env.example            # Ejemplo de variables de entorno
└── README.md              # Este archivo
```

## 🧪 Probar el Sistema de PDF

Una vez configuradas las API keys, puedes probar la conversión de PDF a texto:

```bash
python test_pdf_processor.py
```

Este script probará:
- ✅ Disponibilidad de OCR
- ✅ Extracción de información del PDF
- ✅ Conversión de PDF escaneado a texto

## 🔧 Próximos Pasos

1. ✅ **Sistema LLM básico** - Completado
2. ✅ **Conversión PDF a texto** - Completado
3. 🔄 **Backend con FastAPI** - Siguiente
4. ⏳ **Frontend básico** - Pendiente

## 💡 Características del Sistema

- **Modelo**: Gemini 2.0 Flash (buena ventana de contexto)
- **Enfoque**: Documentos administrativos cortos
- **Estilo**: Respuestas claras y directas para personas ocupadas
- **Contexto**: Inyección del PDF completo en el prompt inicial
- **PDFs**: Procesamiento híbrido (texto estándar + OCR para escaneados)
- **OCR**: Usa OCR.space API (misma que tu proyecto word_autofill exitoso)
