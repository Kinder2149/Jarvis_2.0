/**
 * Conversation List Component - JARVIS 2.0
 * Liste des conversations avec sélection et gestion
 */

import { createElement, clearContainer } from '../utils/dom.js';
import { API_BASE_URL } from '../config.js';
import { formatDate, pluralize } from '../utils/format.js';

class ConversationList {
    constructor(options = {}) {
        this.projectId = options.projectId || null;
        this.onConversationSelect = options.onConversationSelect;
        this.onConversationDelete = options.onConversationDelete;
        this.onNewConversation = options.onNewConversation;
        
        this.element = null;
        this.conversations = [];
        this.selectedConversationId = null;
    }

    /**
     * Rend le composant
     * @returns {HTMLElement}
     */
    async render() {
        this.element = createElement('div', { className: 'conversation-list' });

        await this.loadConversations();
        this.renderConversations();

        return this.element;
    }

    /**
     * Charge les conversations
     */
    async loadConversations() {
        try {
            let url;
            if (this.projectId) {
                url = `${API_BASE_URL}/api/projects/${this.projectId}/conversations`;
            } else {
                url = `${API_BASE_URL}/api/conversations`;
            }

            const response = await fetch(url);
            this.conversations = await response.json();
        } catch (error) {
            console.error('Erreur chargement conversations:', error);
            this.conversations = [];
        }
    }

    /**
     * Affiche les conversations
     */
    renderConversations() {
        clearContainer(this.element);

        // Header avec bouton nouveau
        const header = createElement('div', { 
            className: 'conversation-list-header',
            style: `
                padding: var(--spacing-md);
                border-bottom: 1px solid var(--color-border);
                display: flex;
                align-items: center;
                justify-content: space-between;
            `
        }, [
            createElement('h3', { 
                style: 'font-size: 1rem; font-weight: 600;'
            }, 'Conversations'),
            this.createNewButton()
        ]);

        this.element.appendChild(header);

        // Liste
        const listContainer = createElement('div', { 
            className: 'conversation-list-items',
            style: 'padding: var(--spacing-sm);'
        });

        if (this.conversations.length === 0) {
            listContainer.appendChild(this.renderEmptyState());
        } else {
            this.conversations.forEach(conv => {
                listContainer.appendChild(this.createConversationItem(conv));
            });
        }

        this.element.appendChild(listContainer);
    }

    /**
     * Crée le bouton nouveau
     * @returns {HTMLElement}
     */
    createNewButton() {
        const button = createElement('button', {
            title: 'Nouvelle conversation',
            style: `
                width: 32px;
                height: 32px;
                border-radius: var(--radius-md);
                background-color: var(--color-primary);
                color: white;
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.25rem;
                transition: all var(--transition-fast);
            `
        }, '+');

        button.addEventListener('click', async () => {
            if (this.onNewConversation) {
                await this.onNewConversation();
                await this.refresh();
            }
        });

        button.addEventListener('mouseenter', () => {
            button.style.backgroundColor = 'var(--color-primary-hover)';
            button.style.transform = 'scale(1.1)';
        });

        button.addEventListener('mouseleave', () => {
            button.style.backgroundColor = 'var(--color-primary)';
            button.style.transform = 'scale(1)';
        });

        return button;
    }

    /**
     * Crée un item de conversation
     * @param {Object} conversation
     * @returns {HTMLElement}
     */
    createConversationItem(conversation) {
        const isSelected = conversation.id === this.selectedConversationId;

        const item = createElement('div', {
            className: `conversation-item${isSelected ? ' selected' : ''}`,
            dataset: { id: conversation.id },
            style: `
                padding: var(--spacing-md);
                border-radius: var(--radius-md);
                cursor: pointer;
                transition: all var(--transition-fast);
                background-color: ${isSelected ? 'var(--color-primary-light)' : 'transparent'};
                border: 1px solid ${isSelected ? 'var(--color-primary)' : 'transparent'};
                margin-bottom: var(--spacing-xs);
            `
        }, [
            createElement('div', { 
                style: 'display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;'
            }, [
                createElement('div', { 
                    style: 'flex: 1; min-width: 0;'
                }, [
                    createElement('div', {
                        style: `
                            font-weight: 600;
                            font-size: 0.875rem;
                            color: ${isSelected ? 'var(--color-primary)' : 'var(--color-text)'};
                            overflow: hidden;
                            text-overflow: ellipsis;
                            white-space: nowrap;
                        `
                    }, conversation.title || 'Sans titre'),
                    createElement('div', {
                        style: 'font-size: 0.75rem; color: var(--color-text-muted); margin-top: 0.25rem;'
                    }, `${conversation.message_count} ${pluralize(conversation.message_count, 'message')}`)
                ]),
                this.createDeleteButton(conversation.id)
            ]),
            createElement('div', {
                style: 'font-size: 0.75rem; color: var(--color-text-muted);'
            }, formatDate(conversation.updated_at))
        ]);

        item.addEventListener('click', (e) => {
            if (!e.target.closest('.btn-delete')) {
                this.selectConversation(conversation.id);
            }
        });

        item.addEventListener('mouseenter', () => {
            if (!isSelected) {
                item.style.backgroundColor = 'var(--color-surface-hover)';
            }
        });

        item.addEventListener('mouseleave', () => {
            if (!isSelected) {
                item.style.backgroundColor = 'transparent';
            }
        });

        return item;
    }

    /**
     * Crée le bouton supprimer
     * @param {string} conversationId
     * @returns {HTMLElement}
     */
    createDeleteButton(conversationId) {
        const button = createElement('button', {
            className: 'btn-delete',
            title: 'Supprimer',
            style: `
                width: 24px;
                height: 24px;
                border-radius: var(--radius-sm);
                background-color: transparent;
                color: var(--color-text-muted);
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
                transition: all var(--transition-fast);
            `
        }, '×');

        button.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (confirm('Supprimer cette conversation ?')) {
                await this.deleteConversation(conversationId);
            }
        });

        button.addEventListener('mouseenter', () => {
            button.style.backgroundColor = 'var(--color-danger)';
            button.style.color = 'white';
        });

        button.addEventListener('mouseleave', () => {
            button.style.backgroundColor = 'transparent';
            button.style.color = 'var(--color-text-muted)';
        });

        return button;
    }

    /**
     * Rend l'état vide
     * @returns {HTMLElement}
     */
    renderEmptyState() {
        return createElement('div', {
            style: 'padding: var(--spacing-lg); text-align: center; color: var(--color-text-muted);'
        }, [
            createElement('div', { style: 'font-size: 2rem; margin-bottom: 0.5rem;' }, '💬'),
            createElement('p', { style: 'font-size: 0.875rem;' }, 'Aucune conversation')
        ]);
    }

    /**
     * Sélectionne une conversation
     * @param {string} conversationId
     */
    selectConversation(conversationId) {
        this.selectedConversationId = conversationId;
        this.renderConversations();

        if (this.onConversationSelect) {
            const conversation = this.conversations.find(c => c.id === conversationId);
            this.onConversationSelect(conversation);
        }
    }

    /**
     * Supprime une conversation
     * @param {string} conversationId
     */
    async deleteConversation(conversationId) {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/conversations/${conversationId}`,
                { method: 'DELETE' }
            );

            if (response.ok) {
                if (this.selectedConversationId === conversationId) {
                    this.selectedConversationId = null;
                }

                if (this.onConversationDelete) {
                    this.onConversationDelete(conversationId);
                }

                await this.refresh();
            } else {
                alert('Erreur lors de la suppression.');
            }
        } catch (error) {
            console.error('Erreur suppression conversation:', error);
            alert('Erreur de connexion au serveur.');
        }
    }

    /**
     * Rafraîchit la liste
     */
    async refresh() {
        await this.loadConversations();
        this.renderConversations();
    }

    /**
     * Récupère la conversation sélectionnée
     * @returns {string|null}
     */
    getSelectedConversationId() {
        return this.selectedConversationId;
    }

    /**
     * Définit la conversation sélectionnée
     * @param {string} conversationId
     */
    setSelectedConversation(conversationId) {
        this.selectedConversationId = conversationId;
        this.renderConversations();
    }
}

export default ConversationList;
