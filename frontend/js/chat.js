/**
 * Chat Application - JARVIS 2.0
 * Application de chat simple avec sélection d'agent
 */

import AgentSelector from './components/agent-selector.js';
import ChatInterface from './components/chat-interface.js';
import { API_BASE_URL } from './config.js';

class ChatApp {
    constructor() {
        this.agentSelector = null;
        this.chatInterface = null;
        this.currentConversationId = null;
        this.currentAgent = null;
        
        this.init();
    }

    async init() {
        // Initialiser le sélecteur d'agent
        this.agentSelector = new AgentSelector(async (agentId) => {
            await this.createConversation(agentId);
        });
        
        const selectorContainer = document.getElementById('agent-selector-container');
        const selectorElement = await this.agentSelector.render();
        selectorContainer.appendChild(selectorElement);

        // Initialiser l'interface de chat
        this.chatInterface = new ChatInterface();

        // Bouton nouvelle conversation
        const btnNew = document.getElementById('btn-new-conversation');
        btnNew.addEventListener('click', () => this.newConversation());

        console.log('Chat App initialisée');
    }

    async createConversation(agentId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/conversations`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent_id: agentId,
                    title: `Chat ${agentId}`
                })
            });

            if (!response.ok) {
                throw new Error('Erreur création conversation');
            }

            const conversation = await response.json();
            this.currentConversationId = conversation.id;
            this.currentAgent = agentId;

            // Afficher l'interface de chat
            this.showChatInterface();

            console.log('Conversation créée:', conversation);
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la création de la conversation');
        }
    }

    showChatInterface() {
        // Masquer l'état vide
        const emptyState = document.querySelector('.empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }

        // Afficher le conteneur d'input
        const inputContainer = document.getElementById('chat-input-container');
        inputContainer.style.display = 'flex';

        // Initialiser l'interface de chat
        this.chatInterface.init(this.currentConversationId, this.currentAgent);
    }

    newConversation() {
        // Réinitialiser
        this.currentConversationId = null;
        this.currentAgent = null;

        // Masquer l'interface de chat
        const inputContainer = document.getElementById('chat-input-container');
        inputContainer.style.display = 'none';

        // Vider les messages
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">💬</div>
                <h2>Aucune conversation active</h2>
                <p>Sélectionnez un agent et cliquez sur "Activer" pour commencer.</p>
            </div>
        `;

        console.log('Nouvelle conversation');
    }
}

// Démarrer l'application
new ChatApp();
