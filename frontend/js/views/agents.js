/**
 * Agents View - JARVIS 2.0
 * Vue détaillée des agents disponibles
 */

import { createElement, clearContainer } from '../utils/dom.js';
import { API_BASE_URL } from '../config.js';

const API_BASE = API_BASE_URL;

class AgentsView {
    constructor() {
        this.container = null;
        this.agents = [];
        this.refreshInterval = null;
    }

    /**
     * Rend la vue Agents
     * @param {HTMLElement} container - Conteneur principal
     */
    async render(container) {
        this.container = container;
        clearContainer(container);

        const view = createElement('div', { className: 'agents-view fade-in' });
        container.appendChild(view);

        this.renderLoading(view);
        await this.loadAgents(view);

        // Rafraîchissement automatique toutes les 30s
        this.refreshInterval = setInterval(() => this.refreshAgents(), 30000);
    }

    /**
     * Affiche le loader
     * @param {HTMLElement} container
     */
    renderLoading(container) {
        clearContainer(container);
        const loading = createElement('div', { className: 'agents-loading' }, [
            createElement('div', { className: 'spinner' }),
            createElement('span', {}, 'Chargement des agents...')
        ]);
        container.appendChild(loading);
    }

    /**
     * Charge les agents depuis l'API
     * @param {HTMLElement} container
     */
    async loadAgents(container) {
        try {
            const response = await fetch(`${API_BASE}/api/agents/detailed`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            this.agents = data.agents || [];
            this.renderContent(container);
        } catch (error) {
            console.error('Erreur chargement agents:', error);
            this.renderError(container, error.message);
        }
    }

    /**
     * Rafraîchit les données sans reconstruire toute la page
     */
    async refreshAgents() {
        if (!this.container) return;
        const view = this.container.querySelector('.agents-view');
        if (!view) return;

        try {
            const response = await fetch(`${API_BASE}/api/agents/detailed`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            this.agents = data.agents || [];
            this.renderContent(view);
        } catch (error) {
            console.error('Erreur rafraîchissement agents:', error);
        }
    }

    /**
     * Rend le contenu principal
     * @param {HTMLElement} container
     */
    renderContent(container) {
        clearContainer(container);

        // Header
        const header = createElement('div', { className: 'agents-header' }, [
            createElement('h1', {}, '🤖 Agents JARVIS'),
            createElement('p', {}, `${this.agents.length} agent(s) configuré(s) — Données temps réel`)
        ]);
        container.appendChild(header);

        // Grille des agents
        const grid = createElement('div', { className: 'agents-grid' });
        this.agents.forEach(agent => {
            grid.appendChild(this.renderAgentCard(agent));
        });
        container.appendChild(grid);
    }

    /**
     * Rend une carte agent complète
     * @param {Object} agent - Données de l'agent
     * @returns {HTMLElement}
     */
    renderAgentCard(agent) {
        const card = createElement('div', { className: 'agent-card slide-in-up' });

        // Header
        card.appendChild(this.renderCardHeader(agent));

        // Body
        const body = createElement('div', { className: 'agent-card-body' });

        // Description
        const desc = createElement('p', { className: 'agent-description' }, agent.description);
        body.appendChild(desc);

        // Section : Paramètres
        body.appendChild(this.renderSection('⚙️ Paramètres', this.renderParams(agent)));

        // Section : Permissions
        body.appendChild(this.renderSection('🔐 Permissions', this.renderPermissions(agent)));

        // Section : Configuration
        body.appendChild(this.renderSection('📋 Configuration', this.renderConfig(agent)));

        // Section : Prompt Cloud
        if (agent.prompt_cloud) {
            body.appendChild(this.renderSection('☁️ Prompt Cloud', this.renderPromptCloud(agent)));
        }

        card.appendChild(body);
        return card;
    }

    /**
     * Rend le header d'une carte agent
     * @param {Object} agent
     * @returns {HTMLElement}
     */
    renderCardHeader(agent) {
        const isOrchestrator = agent.type === 'orchestrator';
        const iconClass = isOrchestrator ? 'orchestrator' : 'worker';
        const icon = isOrchestrator ? '👑' : '⚡';

        return createElement('div', { className: 'agent-card-header' }, [
            createElement('div', { className: `agent-icon ${iconClass}` }, icon),
            createElement('div', { className: 'agent-header-info' }, [
                createElement('h2', {}, agent.name),
                createElement('p', { className: 'agent-role' }, agent.role)
            ]),
            createElement('span', { className: `agent-type-badge ${iconClass}` }, agent.type)
        ]);
    }

    /**
     * Rend une section accordéon
     * @param {string} title - Titre de la section
     * @param {HTMLElement} content - Contenu
     * @param {boolean} openByDefault - Ouvert par défaut
     * @returns {HTMLElement}
     */
    renderSection(title, content, openByDefault = false) {
        const section = createElement('div', { className: `agent-section${openByDefault ? ' open' : ''}` });

        const header = createElement('div', { className: 'agent-section-header' }, [
            createElement('span', { className: 'agent-section-title' }, title),
            createElement('span', { className: 'agent-section-arrow' }, '▼')
        ]);

        header.addEventListener('click', () => {
            section.classList.toggle('open');
        });

        const contentWrapper = createElement('div', { className: 'agent-section-content' });
        contentWrapper.appendChild(content);

        section.appendChild(header);
        section.appendChild(contentWrapper);
        return section;
    }

    /**
     * Rend les paramètres d'un agent
     * @param {Object} agent
     * @returns {HTMLElement}
     */
    renderParams(agent) {
        const grid = createElement('div', { className: 'agent-params' });

        const params = [
            { label: 'Temperature', value: String(agent.temperature) },
            { label: 'Max Tokens', value: String(agent.max_tokens) },
            { label: 'Type', value: agent.type },
            { label: 'Env Var', value: agent.env_var }
        ];

        params.forEach(p => {
            grid.appendChild(createElement('div', { className: 'agent-param' }, [
                createElement('span', { className: 'agent-param-label' }, p.label),
                createElement('span', { className: 'agent-param-value' }, p.value)
            ]));
        });

        return grid;
    }

    /**
     * Rend les permissions d'un agent
     * @param {Object} agent
     * @returns {HTMLElement}
     */
    renderPermissions(agent) {
        const container = createElement('div', { className: 'agent-permissions' });

        (agent.permissions || []).forEach(perm => {
            container.appendChild(
                createElement('span', { className: `permission-tag ${perm}` }, perm)
            );
        });

        return container;
    }

    /**
     * Rend la configuration détaillée
     * @param {Object} agent
     * @returns {HTMLElement}
     */
    renderConfig(agent) {
        const grid = createElement('div', { className: 'agent-params' });

        const configs = [
            { label: 'ID', value: agent.id },
            { label: 'Nom', value: agent.name },
            { label: 'Rôle', value: agent.role },
            { label: 'Type', value: agent.type }
        ];

        configs.forEach(c => {
            grid.appendChild(createElement('div', { className: 'agent-param' }, [
                createElement('span', { className: 'agent-param-label' }, c.label),
                createElement('span', { className: 'agent-param-value' }, c.value)
            ]));
        });

        return grid;
    }

    /**
     * Rend le prompt cloud d'un agent
     * @param {Object} agent
     * @returns {HTMLElement}
     */
    renderPromptCloud(agent) {
        return createElement('div', { className: 'agent-prompt-cloud' }, agent.prompt_cloud);
    }

    /**
     * Rend l'état d'erreur
     * @param {HTMLElement} container
     * @param {string} message
     */
    renderError(container, message) {
        clearContainer(container);

        const errorDiv = createElement('div', { className: 'agents-error' }, [
            createElement('div', { style: 'font-size: 3rem; margin-bottom: 1rem;' }, '⚠️'),
            createElement('h2', {}, 'Erreur de chargement'),
            createElement('p', {}, `Impossible de charger les agents : ${message}`)
        ]);

        const retryBtn = createElement('button', { className: 'retry-btn' }, 'Réessayer');
        retryBtn.addEventListener('click', () => this.loadAgents(container));
        errorDiv.appendChild(retryBtn);

        container.appendChild(errorDiv);
    }

    /**
     * Nettoie la vue
     */
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        if (this.container) {
            clearContainer(this.container);
        }
    }
}

export default AgentsView;
