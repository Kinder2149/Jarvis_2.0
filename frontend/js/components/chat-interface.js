/**
 * Chat Interface Component - JARVIS 2.0
 * Gestion de l'interface de chat (messages + input)
 */

import { API_BASE_URL } from '../config.js';
import Message from './message.js';

class ChatInterface {
    constructor() {
        this.conversationId = null;
        this.agentId = null;
        this.messages = [];
    }

    init(conversationId, agentId) {
        this.conversationId = conversationId;
        this.agentId = agentId;
        this.messages = [];

        // Configurer l'input
        const input = document.getElementById('chat-input');
        const btnSend = document.getElementById('btn-send');

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        btnSend.addEventListener('click', () => this.sendMessage());

        console.log('Chat Interface initialisée pour conversation:', conversationId);
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const content = input.value.trim();

        if (!content) return;

        // Désactiver l'input
        input.disabled = true;
        const btnSend = document.getElementById('btn-send');
        btnSend.disabled = true;

        // Afficher le message utilisateur
        this.addMessage('user', content);
        input.value = '';

        try {
            // Envoyer le message à l'API
            const response = await fetch(
                `${API_BASE_URL}/api/conversations/${this.conversationId}/messages`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                }
            );

            if (!response.ok) {
                throw new Error('Erreur envoi message');
            }

            const data = await response.json();

            // Afficher la réponse de l'assistant
            this.addMessage('assistant', data.response);

        } catch (error) {
            console.error('Erreur:', error);
            this.addMessage('assistant', '❌ Erreur lors de l\'envoi du message.');
        } finally {
            // Réactiver l'input
            input.disabled = false;
            btnSend.disabled = false;
            input.focus();
        }
    }

    addMessage(role, content) {
        const messagesContainer = document.getElementById('chat-messages');

        // Créer le message
        const message = new Message({ role, content });
        const messageElement = message.render();

        messagesContainer.appendChild(messageElement);

        // Scroll vers le bas
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

export default ChatInterface;
