/**
 * Chat Component - JARVIS 2.0
 * Composant chat unifié (simple + projet)
 */

import { createElement, clearContainer, scrollToBottom } from '../utils/dom.js';
import { API_BASE_URL } from '../config.js';
import { formatTime } from '../utils/format.js';
import { WorkflowMonitor } from './workflow-monitor.js';

class Chat {
    constructor(options = {}) {
        this.conversationId = options.conversationId;
        this.mode = options.mode || 'simple'; // 'simple' ou 'project'
        this.projectId = options.projectId;
        
        this.element = null;
        this.messagesContainer = null;
        this.input = null;
        this.messages = [];
        this.isLoading = false;
        this.workflowMonitor = null;
    }

    /**
     * Rend le composant chat
     * @returns {HTMLElement}
     */
    render() {
        this.element = createElement('div', { className: 'chat-container' }, [
            this.renderMessagesContainer(),
            this.renderInputContainer(),
            this.renderWorkflowMonitor()
        ]);

        if (this.conversationId) {
            this.loadMessages();
        }

        return this.element;
    }

    /**
     * Rend le conteneur de messages
     * @returns {HTMLElement}
     */
    renderMessagesContainer() {
        this.messagesContainer = createElement('div', { 
            className: 'messages-container',
            id: 'messages'
        });

        return this.messagesContainer;
    }

    /**
     * Rend le conteneur d'input
     * @returns {HTMLElement}
     */
    /**
     * Rend le conteneur du WorkflowMonitor
     * @returns {HTMLElement}
     */
    renderWorkflowMonitor() {
        const container = createElement('div', {
            id: 'workflow-monitor-container',
            style: 'display: none;'
        });

        this.workflowMonitor = new WorkflowMonitor('workflow-monitor-container');

        return container;
    }

    renderInputContainer() {
        this.input = createElement('textarea', {
            className: 'chat-input',
            placeholder: 'Tapez votre message...',
            rows: 1
        });

        const sendButton = createElement('button', {
            className: 'btn-send',
            title: 'Envoyer (Entrée)'
        }, '→');

        sendButton.addEventListener('click', () => this.sendMessage());

        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.input.addEventListener('input', () => {
            this.input.style.height = 'auto';
            this.input.style.height = this.input.scrollHeight + 'px';
        });

        return createElement('div', { className: 'chat-input-container' }, [
            createElement('div', { className: 'chat-input-wrapper' }, [
                this.input,
                createElement('div', { className: 'chat-input-actions' }, [sendButton])
            ])
        ]);
    }

    /**
     * Charge les messages
     */
    async loadMessages() {
        if (!this.conversationId) return;

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/conversations/${this.conversationId}/messages?limit=100`
            );
            const messages = await response.json();
            this.messages = messages;
            this.renderMessages();
        } catch (error) {
            console.error('Erreur chargement messages:', error);
            this.addErrorMessage('Erreur lors du chargement des messages.');
        }
    }

    /**
     * Affiche tous les messages
     */
    renderMessages() {
        clearContainer(this.messagesContainer);
        this.messages.forEach(msg => this.addMessage(msg.role, msg.content, msg.timestamp, false));
        scrollToBottom(this.messagesContainer);
    }

    /**
     * Ajoute un message à l'affichage
     * @param {string} role - user, assistant, system
     * @param {string} content - Contenu
     * @param {string} timestamp - Date ISO
     * @param {boolean} animate - Animer l'apparition
     */
    addMessage(role, content, timestamp = new Date().toISOString(), animate = true) {
        const bubble = createElement('div', { className: 'message-bubble' });

        if (role === 'assistant') {
            bubble.innerHTML = this.formatAssistantContent(content);
        } else {
            bubble.textContent = content;
        }

        const messageEl = createElement('div', { 
            className: `message ${role}${animate ? ' slide-in-up' : ''}`
        }, [
            this.createAvatar(role),
            createElement('div', { className: 'message-content' }, [
                createElement('div', { className: 'message-header' }, [
                    createElement('span', { className: 'message-author' }, 
                        role === 'user' ? 'Vous' : role === 'assistant' ? 'IA' : 'Système'
                    ),
                    createElement('span', { className: 'message-time' }, formatTime(timestamp))
                ]),
                bubble
            ])
        ]);

        this.messagesContainer.appendChild(messageEl);
        scrollToBottom(this.messagesContainer, animate);
    }

    /**
     * Formate le contenu d'un message assistant
     * Détecte les marqueurs de phase et le markdown basique
     * @param {string} content
     * @returns {string} HTML formaté
     */
    formatAssistantContent(content) {
        let html = this.escapeHtml(content);

        // Détecter les blocs de code (``` ... ```) — les protéger avant le reste
        const codeBlocks = [];
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
            const idx = codeBlocks.length;
            codeBlocks.push(`<pre class="code-block"><code>${code.trim()}</code></pre>`);
            return `__CODE_BLOCK_${idx}__`;
        });

        // Marqueurs de phase : [RÉFLEXION] et [PRODUCTION]
        html = html.replace(/\[R[ÉE]FLEXION\]/gi, 
            '<div class="phase-tag phase-reflexion">RÉFLEXION</div>');
        html = html.replace(/\[PRODUCTION\]/gi, 
            '<div class="phase-tag phase-production">PRODUCTION</div>');

        // Titres markdown
        html = html.replace(/^### (.+)$/gm, '<h4 class="msg-heading">$1</h4>');
        html = html.replace(/^## (.+)$/gm, '<h3 class="msg-heading">$1</h3>');
        html = html.replace(/^# (.+)$/gm, '<h2 class="msg-heading">$1</h2>');

        // Gras et italique
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Code inline
        html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

        // Listes à puces
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

        // Listes numérotées
        html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');

        // Restaurer les blocs de code
        codeBlocks.forEach((block, idx) => {
            html = html.replace(`__CODE_BLOCK_${idx}__`, block);
        });

        // Paragraphes (lignes vides → <br>)
        html = html.replace(/\n\n/g, '<br><br>');
        html = html.replace(/\n/g, '<br>');

        return html;
    }

    /**
     * Échappe les caractères HTML
     * @param {string} text
     * @returns {string}
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Crée un avatar
     * @param {string} role
     * @returns {HTMLElement}
     */
    createAvatar(role) {
        const icons = {
            user: '👤',
            assistant: '🤖',
            system: 'ℹ️'
        };

        return createElement('div', { className: 'message-avatar' }, icons[role] || '?');
    }

    /**
     * Ajoute un message d'erreur
     * @param {string} message
     */
    addErrorMessage(message) {
        this.addMessage('error', message);
    }

    /**
     * Affiche l'indicateur de typing
     */
    showTypingIndicator() {
        const indicator = createElement('div', { 
            className: 'typing-indicator',
            id: 'typing-indicator'
        }, [
            this.createAvatar('assistant'),
            createElement('div', { className: 'typing-dots' }, [
                createElement('div', { className: 'typing-dot' }),
                createElement('div', { className: 'typing-dot' }),
                createElement('div', { className: 'typing-dot' })
            ])
        ]);

        this.messagesContainer.appendChild(indicator);
        scrollToBottom(this.messagesContainer);
    }

    /**
     * Masque l'indicateur de typing
     */
    hideTypingIndicator() {
        const indicator = this.messagesContainer.querySelector('#typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Envoie un message
     */
    async sendMessage() {
        if (this.isLoading || !this.conversationId) return;

        const content = this.input.value.trim();
        if (!content) return;

        // Ajouter message utilisateur
        this.addMessage('user', content);
        this.messages.push({ role: 'user', content, timestamp: new Date().toISOString() });

        // Vider input
        this.input.value = '';
        this.input.style.height = 'auto';

        // Afficher typing
        this.showTypingIndicator();
        this.isLoading = true;

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/conversations/${this.conversationId}/messages`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                }
            );

            const data = await response.json();

            this.hideTypingIndicator();

            if (response.ok) {
                // Ne pas ajouter de message si la réponse est vide (Gemini peut retourner "" avec tool_calls)
                if (data.response && data.response.trim()) {
                    this.addMessage('assistant', data.response);
                    this.messages.push({ 
                        role: 'assistant', 
                        content: data.response, 
                        timestamp: new Date().toISOString() 
                    });
                }

                // Détecter délégation et démarrer monitoring workflow
                if (data.delegations && data.delegations.length > 0) {
                    const delegation = data.delegations[0];
                    if (delegation.mission_id) {
                        console.log('Délégation détectée, mission_id:', delegation.mission_id);
                        this.workflowMonitor.startMonitoring(delegation.mission_id);
                    }
                }
            } else {
                this.addErrorMessage(data.detail || 'Erreur lors de l\'envoi du message.');
            }
        } catch (error) {
            console.error('Erreur envoi message:', error);
            this.hideTypingIndicator();
            this.addErrorMessage('Erreur de connexion au serveur.');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Définit la conversation
     * @param {string} conversationId
     */
    setConversation(conversationId) {
        this.conversationId = conversationId;
        this.messages = [];
        clearContainer(this.messagesContainer);
        this.loadMessages();
    }

    /**
     * Nettoie le composant
     */
    destroy() {
        if (this.element) {
            this.element.remove();
        }
    }
}

export default Chat;
