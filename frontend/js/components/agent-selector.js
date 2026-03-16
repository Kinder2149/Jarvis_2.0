/**
 * Agent Selector Component - JARVIS 2.0
 * Sélecteur d'agent avec création de conversation
 */

import state from '../core/state.js';
import { API_BASE_URL } from '../config.js';
import { createElement } from '../utils/dom.js';

class AgentSelector {
    constructor(onAgentSelected) {
        this.onAgentSelected = onAgentSelected;
        this.element = null;
        this.agents = [];
    }

    /**
     * Charge les agents disponibles
     */
    async loadAgents() {
        try {
            const response = await fetch(`${API_BASE_URL}/agents`);
            const data = await response.json();
            this.agents = data.agents;
            state.set('agents', this.agents);
        } catch (error) {
            console.error('Erreur chargement agents:', error);
            this.agents = [
                { id: 'BASE', name: 'BASE', role: 'Assistant générique' },
                { id: 'JARVIS_Maître', name: 'JARVIS_Maître', role: 'Assistant personnel' }
            ];
        }
    }

    /**
     * Rend le sélecteur
     * @returns {HTMLElement}
     */
    async render() {
        await this.loadAgents();

        const currentAgent = state.get('currentAgent');

        this.element = createElement('div', { className: 'agent-selector' }, [
            createElement('label', { 
                className: 'text-secondary',
                style: 'font-size: 0.875rem; margin-bottom: 0.5rem; display: block;'
            }, 'Agent IA'),
            createElement('div', { style: 'display: flex; gap: 0.5rem;' }, [
                this.createSelect(currentAgent),
                this.createActivateButton()
            ])
        ]);

        return this.element;
    }

    /**
     * Crée le select
     * @param {string} currentAgent
     * @returns {HTMLElement}
     */
    createSelect(currentAgent) {
        const select = createElement('select', {
            className: 'agent-select',
            style: `
                flex: 1;
                padding: 0.75rem;
                background-color: var(--color-bg);
                border: 1px solid var(--color-border);
                border-radius: var(--radius-md);
                color: var(--color-text);
                font-size: 1rem;
                cursor: pointer;
            `
        });

        this.agents.forEach(agent => {
            const option = createElement('option', {
                value: agent.id
            }, `${agent.name} - ${agent.role}`);

            if (agent.id === currentAgent) {
                option.selected = true;
            }

            select.appendChild(option);
        });

        select.addEventListener('change', (e) => {
            state.set('currentAgent', e.target.value);
        });

        return select;
    }

    /**
     * Crée le bouton activer
     * @returns {HTMLElement}
     */
    createActivateButton() {
        const button = createElement('button', {
            className: 'btn-activate',
            style: `
                padding: 0.75rem 1.5rem;
                background-color: var(--color-primary);
                color: white;
                border: none;
                border-radius: var(--radius-md);
                font-weight: 600;
                cursor: pointer;
                transition: all var(--transition-fast);
            `
        }, 'Activer');

        button.addEventListener('click', async () => {
            const agentId = state.get('currentAgent');
            button.disabled = true;
            button.textContent = '...';

            if (this.onAgentSelected) {
                await this.onAgentSelected(agentId);
            }

            button.disabled = false;
            button.textContent = 'Activer';
        });

        button.addEventListener('mouseenter', () => {
            if (!button.disabled) {
                button.style.backgroundColor = 'var(--color-primary-hover)';
                button.style.transform = 'scale(1.05)';
            }
        });

        button.addEventListener('mouseleave', () => {
            button.style.backgroundColor = 'var(--color-primary)';
            button.style.transform = 'scale(1)';
        });

        return button;
    }

    /**
     * Récupère l'agent sélectionné
     * @returns {string}
     */
    getSelectedAgent() {
        return state.get('currentAgent');
    }
}

export default AgentSelector;
