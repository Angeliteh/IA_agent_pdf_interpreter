/**
 * PDF Chat Bot - Enhanced Multi-Session Interface
 * Improved UX with tab-based sessions
 */

class PDFChatBotApp {
    constructor() {
        // Detect if running on Live Server or production
        const isLiveServer = window.location.port === '5500';
        this.apiBase = isLiveServer ? 'http://localhost:8000/api/v1' : '/api/v1';
        
        this.sessions = new Map(); // sessionId -> session data
        this.activeSessionId = null;
        this.totalTokens = 0;
        this.isConnected = false;
        
        this.init();
    }
    
    async init() {
        this.bindEvents();
        await this.checkSystemHealth();
        this.updateGlobalStats();
        this.showWelcomeScreen();
    }
    
    bindEvents() {
        // New session button
        document.getElementById('new-session-btn').addEventListener('click', () => {
            this.showSessionModal();
        });
        
        // File upload
        const fileInput = document.getElementById('file-input');
        const uploadZone = document.getElementById('upload-zone');
        const uploadBtn = document.getElementById('upload-btn');
        
        uploadBtn.addEventListener('click', () => fileInput.click());
        uploadZone.addEventListener('click', () => fileInput.click());
        uploadZone.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadZone.addEventListener('drop', this.handleDrop.bind(this));
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        // Chat input
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        messageInput.addEventListener('input', this.handleInputChange.bind(this));
        sendBtn.addEventListener('click', this.sendMessage.bind(this));
        
        // Chat actions
        document.getElementById('clear-chat-btn').addEventListener('click', this.clearCurrentChat.bind(this));
        document.getElementById('export-chat-btn').addEventListener('click', this.exportCurrentChat.bind(this));
        
        // Modal handling
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', this.closeModal.bind(this));
        });
        
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.closeModal();
            });
        });
        
        // Session modal
        document.getElementById('create-session-btn').addEventListener('click', this.createSessionFromModal.bind(this));
        
        // Session type selection
        document.querySelectorAll('.session-type-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.session-type-btn').forEach(b => b.classList.remove('selected'));
                e.currentTarget.classList.add('selected');
            });
        });
    }
    
    // API Methods
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            this.showToast(`Error: ${error.message}`, 'error');
            throw error;
        }
    }
    
    async checkSystemHealth() {
        try {
            const health = await this.apiCall('/health');
            this.isConnected = true;
            console.log('System health:', health);
        } catch (error) {
            this.isConnected = false;
            console.error('System health check failed:', error);
        }
    }
    
    // Session Management
    async createNewSession(name = null, type = 'general') {
        try {
            this.showLoading('Creando nueva sesión...');
            
            const response = await this.apiCall('/sessions', { method: 'POST' });
            const sessionId = response.session.session_id;
            
            const sessionData = {
                id: sessionId,
                name: name || `Sesión ${this.sessions.size + 1}`,
                type: type,
                pdfs: [],
                messages: [],
                tokens: 0,
                createdAt: new Date(),
                isActive: false
            };
            
            this.sessions.set(sessionId, sessionData);
            this.addSessionTab(sessionData);
            this.switchToSession(sessionId);
            
            this.showToast('Nueva sesión creada', 'success');
            this.updateGlobalStats();
            
            return sessionId;
            
        } catch (error) {
            this.showToast('Error creando sesión', 'error');
            throw error;
        } finally {
            this.hideLoading();
        }
    }
    
    switchToSession(sessionId) {
        // Deactivate current session
        if (this.activeSessionId) {
            const currentSession = this.sessions.get(this.activeSessionId);
            if (currentSession) {
                currentSession.isActive = false;
            }
        }
        
        // Activate new session
        const session = this.sessions.get(sessionId);
        if (!session) return;
        
        session.isActive = true;
        this.activeSessionId = sessionId;
        
        // Update UI
        this.updateSessionTabs();
        this.showSessionContent();
        this.loadSessionData(session);
    }
    
    async closeSession(sessionId) {
        if (this.sessions.size <= 1) {
            this.showToast('No puedes cerrar la última sesión', 'warning');
            return;
        }
        
        if (confirm('¿Cerrar esta sesión? Se perderá la conversación.')) {
            this.sessions.delete(sessionId);
            
            // If closing active session, switch to another
            if (sessionId === this.activeSessionId) {
                const remainingSessions = Array.from(this.sessions.keys());
                if (remainingSessions.length > 0) {
                    this.switchToSession(remainingSessions[0]);
                } else {
                    this.showWelcomeScreen();
                }
            }
            
            this.updateSessionTabs();
            this.updateGlobalStats();
        }
    }
    
    // UI Management
    showWelcomeScreen() {
        document.getElementById('welcome-screen').style.display = 'flex';
        document.getElementById('session-content').style.display = 'none';
        this.activeSessionId = null;
    }
    
    showSessionContent() {
        document.getElementById('welcome-screen').style.display = 'none';
        document.getElementById('session-content').style.display = 'block';
    }
    
    addSessionTab(sessionData) {
        const tabsContainer = document.getElementById('tabs-container');
        
        const tab = document.createElement('div');
        tab.className = 'session-tab';
        tab.dataset.sessionId = sessionData.id;
        
        const typeIcons = {
            general: 'file-alt',
            legal: 'balance-scale',
            technical: 'cogs',
            academic: 'graduation-cap'
        };
        
        tab.innerHTML = `
            <i class="fas fa-${typeIcons[sessionData.type]} tab-icon"></i>
            <span class="tab-name">${sessionData.name}</span>
            <button class="tab-close" onclick="app.closeSession('${sessionData.id}')" title="Cerrar sesión">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        tab.addEventListener('click', (e) => {
            if (!e.target.closest('.tab-close')) {
                this.switchToSession(sessionData.id);
            }
        });
        
        tabsContainer.appendChild(tab);
    }
    
    updateSessionTabs() {
        const tabs = document.querySelectorAll('.session-tab');
        tabs.forEach(tab => {
            const sessionId = tab.dataset.sessionId;
            const session = this.sessions.get(sessionId);
            
            if (!session) {
                tab.remove();
                return;
            }
            
            if (session.isActive) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
    }
    
    loadSessionData(session) {
        // Update session info
        document.getElementById('current-session-id').textContent = session.id.substring(0, 8) + '...';
        document.getElementById('current-pdf-count').textContent = `${session.pdfs.length} PDF${session.pdfs.length !== 1 ? 's' : ''}`;
        
        // Update chat title
        document.getElementById('chat-title').textContent = session.name;
        document.getElementById('chat-subtitle').textContent = session.pdfs.length > 0 
            ? `${session.pdfs.length} documento${session.pdfs.length !== 1 ? 's' : ''} cargado${session.pdfs.length !== 1 ? 's' : ''}`
            : 'Sube PDFs para comenzar';
        
        // Load PDFs
        this.renderPDFList(session.pdfs);
        
        // Load messages
        this.renderMessages(session.messages);
        
        // Update input state
        this.updateInputState(session);
        
        // Update action buttons
        document.getElementById('clear-chat-btn').disabled = session.messages.length === 0;
        document.getElementById('export-chat-btn').disabled = session.messages.length === 0;
    }
    
    updateGlobalStats() {
        const totalSessions = this.sessions.size;
        const totalPDFs = Array.from(this.sessions.values()).reduce((sum, session) => sum + session.pdfs.length, 0);
        const totalTokens = Array.from(this.sessions.values()).reduce((sum, session) => sum + session.tokens, 0);
        
        document.getElementById('total-sessions').textContent = totalSessions;
        document.getElementById('total-pdfs').textContent = totalPDFs;
        document.getElementById('total-tokens').textContent = totalTokens.toLocaleString();
    }
    
    // File Handling
    handleDragOver(e) {
        e.preventDefault();
        document.getElementById('upload-zone').classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        document.getElementById('upload-zone').classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        document.getElementById('upload-zone').classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files).filter(file => 
            file.type === 'application/pdf'
        );
        
        if (files.length > 0) {
            this.processFiles(files);
        } else {
            this.showToast('Solo se permiten archivos PDF', 'warning');
        }
    }
    
    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
        e.target.value = ''; // Reset input
    }
    
    async processFiles(files) {
        if (!this.activeSessionId) {
            this.showToast('Crea una sesión primero', 'warning');
            return;
        }
        
        const session = this.sessions.get(this.activeSessionId);
        
        for (const file of files) {
            await this.processSingleFile(file, session);
        }
        
        await this.refreshSessionPDFs(session);
    }
    
    async processSingleFile(file, session) {
        try {
            this.showLoading(`Subiendo ${file.name}...`);
            
            let result;
            if (session.pdfs.length === 0) {
                // First PDF - use main upload endpoint
                result = await this.uploadPDF(file, session.id);
            } else {
                // Additional PDF - use add endpoint
                result = await this.addPDFToSession(file, session.id);
            }
            
            this.showToast(`PDF "${file.name}" cargado exitosamente`, 'success');
            
        } catch (error) {
            this.showToast(`Error subiendo "${file.name}": ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async uploadPDF(file, sessionId) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.apiBase}/sessions/${sessionId}/pdf`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail?.message || 'Upload failed');
        }
        
        return await response.json();
    }
    
    async addPDFToSession(file, sessionId) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.apiBase}/sessions/${sessionId}/pdfs/add`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail?.message || 'Upload failed');
        }
        
        return await response.json();
    }
    
    async refreshSessionPDFs(session) {
        try {
            const response = await this.apiCall(`/sessions/${session.id}/pdfs`);
            session.pdfs = response.pdfs || [];
            this.loadSessionData(session);
            this.updateGlobalStats();
        } catch (error) {
            console.error('Error refreshing PDFs:', error);
        }
    }
    
    renderPDFList(pdfs) {
        const pdfList = document.getElementById('pdf-list');
        const emptyPdfs = document.getElementById('empty-pdfs');
        
        if (pdfs.length === 0) {
            emptyPdfs.style.display = 'block';
            pdfList.innerHTML = '';
            pdfList.appendChild(emptyPdfs);
            return;
        }
        
        emptyPdfs.style.display = 'none';
        pdfList.innerHTML = '';
        
        pdfs.forEach(pdf => {
            const pdfItem = this.createPDFItem(pdf);
            pdfList.appendChild(pdfItem);
        });
    }
    
    createPDFItem(pdfData) {
        const item = document.createElement('div');
        item.className = 'pdf-item';
        
        item.innerHTML = `
            <div class="pdf-icon">PDF</div>
            <div class="pdf-info">
                <div class="pdf-name" title="${pdfData.filename}">${pdfData.filename}</div>
                <div class="pdf-meta">
                    <span>${this.formatFileSize(pdfData.size)}</span>
                    <span>${pdfData.pages} pág${pdfData.pages > 1 ? 's' : ''}</span>
                    <span>${pdfData.tokens.toLocaleString()} tokens</span>
                </div>
            </div>
            <div class="pdf-actions">
                <button class="info-btn" title="Ver detalles" onclick="app.showPDFDetails('${pdfData.filename}')">
                    <i class="fas fa-info-circle"></i>
                </button>
                <button class="delete-btn" title="Eliminar" onclick="app.removePDFFromSession('${pdfData.filename}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        return item;
    }
    
    async removePDFFromSession(filename) {
        if (!this.activeSessionId) return;
        
        if (confirm(`¿Eliminar "${filename}"?`)) {
            try {
                this.showLoading('Eliminando PDF...');
                
                const response = await this.apiCall(`/sessions/${this.activeSessionId}/pdfs/${encodeURIComponent(filename)}`, {
                    method: 'DELETE'
                });
                
                this.showToast(`PDF "${filename}" eliminado`, 'success');
                
                const session = this.sessions.get(this.activeSessionId);
                await this.refreshSessionPDFs(session);
                
            } catch (error) {
                this.showToast(`Error eliminando PDF: ${error.message}`, 'error');
            } finally {
                this.hideLoading();
            }
        }
    }
    
    // Chat Handling
    handleInputChange() {
        const input = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        
        // Auto-resize textarea
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        
        // Enable/disable send button
        const hasText = input.value.trim().length > 0;
        const session = this.activeSessionId ? this.sessions.get(this.activeSessionId) : null;
        const hasPDFs = session && session.pdfs.length > 0;
        
        sendBtn.disabled = !hasText || !hasPDFs;
        
        // Update token estimate
        this.updateTokenEstimate(input.value);
    }
    
    updateInputState(session) {
        const input = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const statusEl = document.getElementById('input-status');
        
        if (session.pdfs.length === 0) {
            input.disabled = true;
            sendBtn.disabled = true;
            statusEl.textContent = 'Sube al menos un PDF para comenzar';
        } else {
            input.disabled = false;
            statusEl.textContent = `${session.pdfs.length} PDF${session.pdfs.length > 1 ? 's' : ''} cargado${session.pdfs.length > 1 ? 's' : ''}`;
        }
    }
    
    updateTokenEstimate(text) {
        const estimatedTokens = Math.ceil(text.length / 4);
        document.getElementById('token-estimate').textContent = `~${estimatedTokens} tokens`;
    }
    
    async sendMessage() {
        if (!this.activeSessionId) return;
        
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        const session = this.sessions.get(this.activeSessionId);
        if (!session || session.pdfs.length === 0) return;
        
        // Add user message to session and UI
        const userMessage = {
            text: message,
            sender: 'user',
            timestamp: new Date(),
            tokens: 0
        };
        
        session.messages.push(userMessage);
        this.addMessageToUI(userMessage);
        
        input.value = '';
        this.handleInputChange();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await this.apiCall(`/sessions/${session.id}/chat`, {
                method: 'POST',
                body: JSON.stringify({ message })
            });
            
            if (response.success) {
                const botMessage = {
                    text: response.response,
                    sender: 'bot',
                    timestamp: new Date(),
                    tokens: response.token_info.total_exchange_tokens
                };
                
                session.messages.push(botMessage);
                session.tokens += response.token_info.total_exchange_tokens;
                
                this.addMessageToUI(botMessage);
                this.updateGlobalStats();
                this.loadSessionData(session); // Update action buttons
                
            } else {
                throw new Error(response.error || 'Chat failed');
            }
            
        } catch (error) {
            const errorMessage = {
                text: `Error: ${error.message}`,
                sender: 'bot',
                timestamp: new Date(),
                tokens: 0,
                isError: true
            };
            
            session.messages.push(errorMessage);
            this.addMessageToUI(errorMessage);
            
        } finally {
            this.hideTypingIndicator();
        }
    }
    
    renderMessages(messages) {
        const container = document.getElementById('messages-container');
        const welcomeMessage = container.querySelector('.chat-welcome');
        
        // Clear existing messages but keep welcome
        container.innerHTML = '';
        container.appendChild(welcomeMessage);
        
        messages.forEach(message => {
            this.addMessageToUI(message, false); // Don't scroll for bulk loading
        });
        
        // Scroll to bottom after loading all messages
        container.scrollTop = container.scrollHeight;
    }
    
    addMessageToUI(message, shouldScroll = true) {
        const container = document.getElementById('messages-container');
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.sender} ${message.isError ? 'error' : ''}`;
        
        const timestamp = message.timestamp.toLocaleTimeString();
        const tokenText = message.tokens > 0 ? `${message.tokens.toLocaleString()} tokens` : '';
        
        messageEl.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-${message.sender === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-bubble">
                <div class="message-text">${this.formatMessageText(message.text)}</div>
                <div class="message-meta">
                    <span>${timestamp}</span>
                    ${tokenText ? `<span>${tokenText}</span>` : ''}
                </div>
            </div>
        `;
        
        container.appendChild(messageEl);
        
        if (shouldScroll) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    formatMessageText(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
    
    showTypingIndicator() {
        const container = document.getElementById('messages-container');
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typing-indicator';
        
        indicator.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-bubble">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        container.appendChild(indicator);
        container.scrollTop = container.scrollHeight;
    }
    
    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    async clearCurrentChat() {
        if (!this.activeSessionId) return;
        
        if (confirm('¿Limpiar toda la conversación de esta sesión?')) {
            try {
                await this.apiCall(`/sessions/${this.activeSessionId}/clear`, { method: 'POST' });
                
                const session = this.sessions.get(this.activeSessionId);
                session.messages = [];
                session.tokens = 0;
                
                this.renderMessages([]);
                this.loadSessionData(session);
                this.updateGlobalStats();
                
                this.showToast('Conversación limpiada', 'success');
            } catch (error) {
                this.showToast('Error limpiando conversación', 'error');
            }
        }
    }
    
    exportCurrentChat() {
        if (!this.activeSessionId) return;
        
        const session = this.sessions.get(this.activeSessionId);
        const chatData = {
            sessionId: session.id,
            sessionName: session.name,
            sessionType: session.type,
            pdfs: session.pdfs,
            messages: session.messages,
            totalTokens: session.tokens,
            createdAt: session.createdAt,
            exportedAt: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-${session.name.replace(/\s+/g, '-')}-${session.id.substring(0, 8)}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('Chat exportado', 'success');
    }
    
    // Modal Management
    showSessionModal() {
        // Reset form
        document.getElementById('session-name').value = '';
        document.querySelectorAll('.session-type-btn').forEach(btn => btn.classList.remove('selected'));
        document.querySelector('.session-type-btn[data-type="general"]').classList.add('selected');
        
        this.showModal('session-modal');
    }
    
    async createSessionFromModal() {
        const name = document.getElementById('session-name').value.trim();
        const selectedType = document.querySelector('.session-type-btn.selected');
        const type = selectedType ? selectedType.dataset.type : 'general';
        
        this.closeModal();
        
        try {
            await this.createNewSession(name, type);
        } catch (error) {
            console.error('Error creating session from modal:', error);
        }
    }
    
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.add('show');
    }
    
    closeModal() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
        });
    }
    
    async showPDFDetails(filename) {
        if (!this.activeSessionId) return;
        
        const session = this.sessions.get(this.activeSessionId);
        const pdf = session.pdfs.find(p => p.filename === filename);
        if (!pdf) return;
        
        const content = document.getElementById('pdf-details-content');
        content.innerHTML = `
            <div style="display: grid; gap: 16px;">
                <div>
                    <strong>Nombre:</strong><br>
                    <code>${pdf.filename}</code>
                </div>
                <div>
                    <strong>Tamaño:</strong> ${this.formatFileSize(pdf.size)}
                </div>
                <div>
                    <strong>Páginas:</strong> ${pdf.pages}
                </div>
                <div>
                    <strong>Tokens:</strong> ${pdf.tokens.toLocaleString()}
                </div>
                <div>
                    <strong>Método de extracción:</strong> ${pdf.method}
                </div>
                <div>
                    <strong>Subido:</strong> ${new Date(pdf.uploaded_at).toLocaleString()}
                </div>
            </div>
        `;
        
        this.showModal('pdf-details-modal');
    }
    
    // Utility Methods
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    showLoading(text = 'Cargando...') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        loadingText.textContent = text;
        overlay.classList.add('show');
    }
    
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.remove('show');
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
    
    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PDFChatBotApp();
});
