# PDF Chat Bot API - Developer Documentation

## 🚀 **API Overview**

REST API for PDF document chat with AI using Gemini 2.0 Flash. **Perfect for mobile app integration** with Flutter, React Native, or any HTTP client.

### **Base URL**
```
http://localhost:8000  (Development)
https://your-domain.com  (Production)
```

### **Key Features**
- ✅ **PDF Processing**: Upload and extract text (OCR support)
- ✅ **AI Chat**: Intelligent conversation about PDF content  
- ✅ **Session Management**: Robust session handling
- ✅ **Token Monitoring**: Real-time usage tracking
- ✅ **Constant Context**: PDF injected in every message
- ✅ **Mobile Ready**: CORS enabled, JSON responses

---

## 📱 **Mobile App Integration Guide**

### **Flutter Example**
```dart
class PDFChatAPI {
  final String baseUrl = 'http://localhost:8000';
  
  // 1. Create Session
  Future<String> createSession() async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/sessions'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'session_name': 'Mobile Chat'})
    );
    
    final data = json.decode(response.body);
    return data['session']['session_id'];
  }
  
  // 2. Upload PDF
  Future<bool> uploadPDF(String sessionId, File pdfFile) async {
    var request = http.MultipartRequest(
      'POST', 
      Uri.parse('$baseUrl/api/v1/sessions/$sessionId/pdf')
    );
    request.files.add(await http.MultipartFile.fromPath('file', pdfFile.path));
    
    final response = await request.send();
    return response.statusCode == 200;
  }
  
  // 3. Send Message
  Future<String> sendMessage(String sessionId, String message) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/sessions/$sessionId/chat'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'message': message})
    );
    
    final data = json.decode(response.body);
    return data['response'];
  }
}
```

### **React Native Example**
```javascript
class PDFChatAPI {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }
  
  // Create Session
  async createSession() {
    const response = await fetch(`${this.baseUrl}/api/v1/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_name: 'Mobile Chat' })
    });
    
    const data = await response.json();
    return data.session.session_id;
  }
  
  // Upload PDF
  async uploadPDF(sessionId, pdfUri) {
    const formData = new FormData();
    formData.append('file', {
      uri: pdfUri,
      type: 'application/pdf',
      name: 'document.pdf'
    });
    
    const response = await fetch(
      `${this.baseUrl}/api/v1/sessions/${sessionId}/pdf`,
      { method: 'POST', body: formData }
    );
    
    return response.ok;
  }
  
  // Send Message
  async sendMessage(sessionId, message) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/sessions/${sessionId}/chat`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      }
    );
    
    const data = await response.json();
    return data.response;
  }
}
```

---

## 🔧 **API Endpoints Reference**

### **Sessions**

#### `POST /api/v1/sessions`
Create a new chat session.

**Request:**
```json
{
  "session_name": "My Chat Session",
  "timeout_minutes": 60
}
```

**Response:**
```json
{
  "success": true,
  "message": "Session created successfully",
  "session": {
    "session_id": "pdf_chat_20240115_103000",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "has_pdf": false,
    "message_count": 0,
    "total_tokens_used": 0
  }
}
```

#### `GET /api/v1/sessions/{session_id}`
Get session information.

#### `DELETE /api/v1/sessions/{session_id}`
Delete a session.

#### `GET /api/v1/sessions`
List all active sessions.

### **PDF Operations**

#### `POST /api/v1/sessions/{session_id}/pdf`
Upload PDF to session.

**Request:** Multipart form with `file` field
**Response:**
```json
{
  "success": true,
  "pdf_info": {
    "filename": "document.pdf",
    "file_size": 233203,
    "num_pages": 1,
    "estimated_tokens": 415,
    "extraction_method": "ocr"
  }
}
```

#### `GET /api/v1/sessions/{session_id}/pdf`
Get PDF information.

#### `DELETE /api/v1/sessions/{session_id}/pdf`
Remove PDF from session.

### **Chat**

#### `POST /api/v1/sessions/{session_id}/chat`
Send message and get AI response.

**Request:**
```json
{
  "message": "¿Cuál es el número de oficio?"
}
```

**Response:**
```json
{
  "success": true,
  "response": "El número de oficio es SEPF/C.O./1999/25-26.",
  "token_info": {
    "total_exchange_tokens": 436,
    "session_total_tokens": 436,
    "gemini_usage_percentage": 0.044
  },
  "session_info": {
    "message_count": 2,
    "total_tokens_used": 436
  }
}
```

#### `GET /api/v1/sessions/{session_id}/history`
Get conversation history.

#### `DELETE /api/v1/sessions/{session_id}/history`
Clear conversation history.

### **Monitoring**

#### `GET /api/v1/sessions/{session_id}/stats`
Get detailed session statistics.

#### `GET /api/v1/health`
System health check.

---

## 🛠️ **Development Setup**

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

### **3. Start Server**
```bash
python main.py
```

### **4. Test API**
```bash
python test_api.py
```

### **5. View Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📊 **Response Format**

All endpoints return consistent JSON responses:

### **Success Response**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": { /* endpoint-specific data */ }
}
```

### **Error Response**
```json
{
  "success": false,
  "message": "Error description",
  "timestamp": "2024-01-15T10:30:00Z",
  "error_code": "ERROR_CODE",
  "details": { /* additional error info */ }
}
```

### **Error Codes**
- `SESSION_NOT_FOUND` - Session doesn't exist
- `SESSION_EXPIRED` - Session has expired
- `PDF_NOT_LOADED` - No PDF in session
- `PDF_UPLOAD_FAILED` - PDF processing failed
- `PDF_TOO_LARGE` - File exceeds size limit
- `INVALID_FILE_TYPE` - Not a PDF file
- `CHAT_FAILED` - AI processing failed
- `INTERNAL_ERROR` - Server error

---

## 🔒 **Security & Limits**

### **File Upload Limits**
- **Max file size**: 10MB
- **Allowed types**: PDF only
- **Processing**: OCR for scanned PDFs

### **Rate Limits**
- **Per session**: No specific limit
- **Token usage**: Monitored and reported
- **Session timeout**: 30 minutes default

### **CORS**
- **Enabled**: For all origins (configure for production)
- **Methods**: All HTTP methods
- **Headers**: All headers allowed

---

## 🚀 **Production Deployment**

### **Environment Variables**
```bash
GEMINI_API_KEY=your_gemini_key
OCR_API_KEY=your_ocr_key
DEBUG=false
MAX_TOKENS=8192
TEMPERATURE=0.7
```

### **Docker Deployment**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Health Monitoring**
- **Endpoint**: `/api/v1/health`
- **Metrics**: API status, token usage, active sessions
- **Logging**: Comprehensive request/error logging

---

## 📱 **Mobile App Checklist**

### **Before Integration**
- [ ] API server running and accessible
- [ ] Health check returns `200 OK`
- [ ] Test PDF available for upload
- [ ] API keys configured

### **Integration Steps**
1. **Test connectivity** with root endpoint `/`
2. **Create session** and store session ID
3. **Upload PDF** and verify processing
4. **Send test message** and verify response
5. **Implement error handling** for all scenarios
6. **Add token monitoring** for usage tracking

### **Error Handling**
- Network connectivity issues
- Session expiration
- PDF processing failures
- API rate limits
- Invalid responses

---

## 🎯 **Next Steps**

This API is **production-ready** and designed as a **perfect Lego piece** for your mobile app. The consistent REST design, comprehensive error handling, and detailed documentation make integration straightforward.

**Ready for**: Flutter, React Native, iOS, Android, or any HTTP client.

**Documentation**: Always available at `/docs` for interactive testing.
