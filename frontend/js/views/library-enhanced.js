/**
 * Library View Enhanced - JARVIS 2.0
 * Vue moderne de la Knowledge Base avec chargement API
 */

import { createElement, clearContainer } from '../utils/dom.js';

const API_BASE = 'http://localhost:8000';

/**
 * Métadonnées des catégories
 */
const CATEGORY_METADATA = {
    'libraries': {
        id: 'libraries',
        name: 'Librairies & Frameworks',
        icon: '📚',
        color: 'var(--color-primary)',
        description: 'Documentation de référence des librairies Python, Flutter, JS, etc.'
    },
    'methodologies': {
        id: 'methodologies',
        name: 'Méthodologies',
        icon: '📋',
        color: 'var(--color-secondary)',
        description: 'Processus de travail, audits, plans d\'exécution'
    },
    'prompts': {
        id: 'prompts',
        name: 'Prompts & Templates',
        icon: '💬',
        color: 'var(--color-info)',
        description: 'Prompts récurrents pour les tâches courantes et la communication inter-agents'
    },
    'personal': {
        id: 'personal',
        name: 'Données personnelles',
        icon: '👤',
        color: 'var(--color-warning)',
        description: 'Préférences, conventions, informations spécifiques à Val C.'
    }
};

class LibraryViewEnhanced {
    constructor() {
        this.container = null;
        this.documents = [];
        this.activeFilter = 'all';
    }

    async render(container) {
        this.container = container;
        clearContainer(container);

        const view = createElement('div', { className: 'library-view' });
        container.appendChild(view);

        this.renderLoading(view);
        await this.loadDocuments(view);
    }

    renderLoading(container) {
        clearContainer(container);
        const loading = createElement('div', { className: 'loading-container' }, [
            createElement('div', { className: 'spinner' }),
            createElement('p', { className: 'loading-text' }, 'Chargement de la Library...')
        ]);
        container.appendChild(loading);
    }

    async loadDocuments(container) {
        try {
            const response = await fetch(`${API_BASE}/api/library`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            this.documents = await response.json();
            this.renderContent(container);
        } catch (error) {
            console.error('Erreur chargement Library:', error);
            this.renderError(container, error.message);
        }
    }

    renderError(container, message) {
        clearContainer(container);
        const errorDiv = createElement('div', { className: 'error-container' }, [
            createElement('div', { className: 'error-icon' }, '⚠️'),
            createElement('h2', {}, 'Erreur de chargement'),
            createElement('p', {}, `Impossible de charger la Library : ${message}`)
        ]);

        const retryBtn = createElement('button', { className: 'btn btn-primary' }, 'Réessayer');
        retryBtn.addEventListener('click', () => this.loadDocuments(container));
        errorDiv.appendChild(retryBtn);

        container.appendChild(errorDiv);
    }

    renderContent(container) {
        clearContainer(container);

        const content = createElement('div', { className: 'library-content' });
        
        content.appendChild(this.renderHeader());
        content.appendChild(this.renderStats());
        content.appendChild(this.renderFilters());
        content.appendChild(this.renderGrid());
        
        container.appendChild(content);
    }

    renderHeader() {
        return createElement('div', { className: 'library-header' }, [
            createElement('div', { className: 'header-content' }, [
                createElement('h1', {}, '📚 Knowledge Base'),
                createElement('p', { className: 'header-subtitle' }, 'Base de connaissances pour les agents et l\'utilisateur')
            ]),
            createElement('div', { className: 'header-actions' }, [
                this.createActionButton('🔄', 'Rafraîchir', () => this.loadDocuments(this.container)),
                this.createActionButton('➕', 'Ajouter', () => this.showAddModal())
            ])
        ]);
    }

    createActionButton(icon, label, onClick) {
        const btn = createElement('button', { 
            className: 'btn btn-secondary',
            title: label
        }, `${icon} ${label}`);
        btn.addEventListener('click', onClick);
        return btn;
    }

    renderStats() {
        const stats = this.calculateStats();
        
        return createElement('div', { className: 'library-stats' }, [
            this.createStatCard('📄', stats.total, 'Documents'),
            this.createStatCard('📚', stats.libraries, 'Librairies'),
            this.createStatCard('📋', stats.methodologies, 'Méthodologies'),
            this.createStatCard('💬', stats.prompts, 'Prompts'),
            this.createStatCard('👤', stats.personal, 'Personnel')
        ]);
    }

    calculateStats() {
        return {
            total: this.documents.length,
            libraries: this.documents.filter(d => d.category === 'libraries').length,
            methodologies: this.documents.filter(d => d.category === 'methodologies').length,
            prompts: this.documents.filter(d => d.category === 'prompts').length,
            personal: this.documents.filter(d => d.category === 'personal').length
        };
    }

    createStatCard(icon, value, label) {
        return createElement('div', { className: 'stat-card' }, [
            createElement('div', { className: 'stat-icon' }, icon),
            createElement('div', { className: 'stat-content' }, [
                createElement('div', { className: 'stat-value' }, String(value)),
                createElement('div', { className: 'stat-label' }, label)
            ])
        ]);
    }

    renderFilters() {
        const filters = [
            { id: 'all', label: '🔍 Tous', count: this.documents.length },
            { id: 'libraries', label: '📚 Librairies', count: this.documents.filter(d => d.category === 'libraries').length },
            { id: 'methodologies', label: '📋 Méthodologies', count: this.documents.filter(d => d.category === 'methodologies').length },
            { id: 'prompts', label: '💬 Prompts', count: this.documents.filter(d => d.category === 'prompts').length },
            { id: 'personal', label: '👤 Personnel', count: this.documents.filter(d => d.category === 'personal').length }
        ];

        const container = createElement('div', { className: 'library-filters' });

        filters.forEach(filter => {
            const btn = createElement('button', {
                className: `filter-btn${this.activeFilter === filter.id ? ' active' : ''}`
            }, `${filter.label} (${filter.count})`);

            btn.addEventListener('click', () => {
                this.activeFilter = filter.id;
                this.renderContent(this.container);
            });

            container.appendChild(btn);
        });

        return container;
    }

    renderGrid() {
        const filtered = this.activeFilter === 'all' 
            ? this.documents 
            : this.documents.filter(doc => doc.category === this.activeFilter);

        if (filtered.length === 0) {
            return createElement('div', { className: 'empty-state' }, [
                createElement('div', { className: 'empty-icon' }, '📭'),
                createElement('p', {}, 'Aucun document dans cette catégorie')
            ]);
        }

        const grid = createElement('div', { className: 'library-grid' });

        filtered.forEach(doc => {
            grid.appendChild(this.renderDocumentCard(doc));
        });

        return grid;
    }

    renderDocumentCard(doc) {
        const category = CATEGORY_METADATA[doc.category];
        
        const card = createElement('div', { className: 'document-card' });
        
        const header = createElement('div', { className: 'card-header' }, [
            createElement('div', { className: 'card-icon' }, doc.icon || category?.icon || '📄'),
            createElement('div', { className: 'card-category' }, category?.name || doc.category)
        ]);
        
        const body = createElement('div', { className: 'card-body' }, [
            createElement('h3', { className: 'card-title' }, doc.name),
            createElement('p', { className: 'card-description' }, doc.description || 'Pas de description')
        ]);
        
        const footer = createElement('div', { className: 'card-footer' });
        
        if (doc.tags && doc.tags.length > 0) {
            const tagsContainer = createElement('div', { className: 'card-tags' });
            doc.tags.forEach(tag => {
                tagsContainer.appendChild(
                    createElement('span', { className: 'tag' }, tag)
                );
            });
            footer.appendChild(tagsContainer);
        }
        
        if (doc.agents && doc.agents.length > 0) {
            const agentsContainer = createElement('div', { className: 'card-agents' });
            doc.agents.forEach(agent => {
                agentsContainer.appendChild(
                    createElement('span', { className: 'agent-badge' }, agent)
                );
            });
            footer.appendChild(agentsContainer);
        }
        
        card.appendChild(header);
        card.appendChild(body);
        card.appendChild(footer);
        
        card.addEventListener('click', () => this.showDocumentDetail(doc));
        
        return card;
    }

    showDocumentDetail(doc) {
        const overlay = createElement('div', { className: 'library-modal-overlay' });
        const modal = createElement('div', { className: 'library-modal library-modal-large' });

        const closeBtn = createElement('button', { className: 'library-modal-close' }, '×');
        closeBtn.addEventListener('click', () => overlay.remove());

        const editBtn = createElement('button', { className: 'btn btn-secondary btn-sm' }, '✏️ Modifier');
        editBtn.addEventListener('click', () => {
            overlay.remove();
            this.showDocumentForm(doc);
        });

        const header = createElement('div', { className: 'library-modal-header' }, [
            createElement('h2', {}, `${doc.icon || '📄'} ${doc.name}`),
            createElement('div', { className: 'modal-actions' }, [editBtn, closeBtn])
        ]);

        const body = createElement('div', { className: 'library-modal-body' });
        
        if (doc.description) {
            body.appendChild(createElement('p', { className: 'doc-description' }, doc.description));
        }
        
        if (doc.tags && doc.tags.length > 0) {
            const tagsDiv = createElement('div', { className: 'doc-meta' });
            tagsDiv.appendChild(createElement('strong', {}, 'Tags : '));
            const tagsContainer = createElement('span', { className: 'doc-tags' });
            doc.tags.forEach(tag => {
                tagsContainer.appendChild(createElement('span', { className: 'tag' }, tag));
            });
            tagsDiv.appendChild(tagsContainer);
            body.appendChild(tagsDiv);
        }
        
        if (doc.agents && doc.agents.length > 0) {
            const agentsDiv = createElement('div', { className: 'doc-meta' });
            agentsDiv.appendChild(createElement('strong', {}, 'Agents : '));
            const agentsContainer = createElement('span', { className: 'doc-agents' });
            doc.agents.forEach(agent => {
                agentsContainer.appendChild(createElement('span', { className: 'agent-badge' }, agent));
            });
            agentsDiv.appendChild(agentsContainer);
            body.appendChild(agentsDiv);
        }
        
        const contentDiv = createElement('div', { className: 'doc-content' });
        const pre = createElement('pre', {});
        const code = createElement('code', {});
        code.textContent = doc.content || 'Pas de contenu';
        pre.appendChild(code);
        contentDiv.appendChild(pre);
        body.appendChild(contentDiv);

        modal.appendChild(header);
        modal.appendChild(body);
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });
    }

    showAddModal() {
        this.showDocumentForm(null);
    }

    showDocumentForm(doc = null) {
        const isEdit = doc !== null;
        const overlay = createElement('div', { className: 'library-modal-overlay' });
        const modal = createElement('div', { className: 'library-modal library-modal-large' });

        const closeBtn = createElement('button', { className: 'library-modal-close' }, '×');
        closeBtn.addEventListener('click', () => overlay.remove());

        const header = createElement('div', { className: 'library-modal-header' }, [
            createElement('h2', {}, isEdit ? `✏️ Modifier ${doc.name}` : '➕ Nouveau Document'),
            closeBtn
        ]);

        const body = createElement('div', { className: 'library-modal-body' });
        const form = this.createDocumentForm(doc);
        body.appendChild(form);

        const footer = createElement('div', { className: 'library-modal-footer' });
        
        const cancelBtn = createElement('button', { className: 'btn btn-secondary' }, 'Annuler');
        cancelBtn.addEventListener('click', () => overlay.remove());
        
        const saveBtn = createElement('button', { className: 'btn btn-primary' }, isEdit ? '💾 Sauvegarder' : '➕ Créer');
        saveBtn.addEventListener('click', async () => {
            await this.saveDocument(form, doc?.id, overlay);
        });
        
        if (isEdit) {
            const deleteBtn = createElement('button', { className: 'btn btn-danger' }, '🗑️ Supprimer');
            deleteBtn.addEventListener('click', async () => {
                if (confirm(`Êtes-vous sûr de vouloir supprimer "${doc.name}" ?`)) {
                    await this.deleteDocument(doc.id, overlay);
                }
            });
            footer.appendChild(deleteBtn);
        }
        
        footer.appendChild(cancelBtn);
        footer.appendChild(saveBtn);

        modal.appendChild(header);
        modal.appendChild(body);
        modal.appendChild(footer);
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });
    }

    createDocumentForm(doc) {
        const form = createElement('form', { className: 'document-form' });

        // Catégorie
        const categoryGroup = createElement('div', { className: 'form-group' });
        categoryGroup.appendChild(createElement('label', {}, 'Catégorie *'));
        const categorySelect = createElement('select', { 
            className: 'form-control',
            name: 'category',
            required: true
        });
        Object.keys(CATEGORY_METADATA).forEach(catId => {
            const option = createElement('option', { value: catId }, CATEGORY_METADATA[catId].name);
            if (doc?.category === catId) option.selected = true;
            categorySelect.appendChild(option);
        });
        categoryGroup.appendChild(categorySelect);
        form.appendChild(categoryGroup);

        // Nom
        const nameGroup = createElement('div', { className: 'form-group' });
        nameGroup.appendChild(createElement('label', {}, 'Nom *'));
        const nameInput = createElement('input', { 
            className: 'form-control',
            type: 'text',
            name: 'name',
            placeholder: 'Ex: FastAPI',
            required: true,
            value: doc?.name || ''
        });
        nameGroup.appendChild(nameInput);
        form.appendChild(nameGroup);

        // Icône
        const iconGroup = createElement('div', { className: 'form-group' });
        iconGroup.appendChild(createElement('label', {}, 'Icône (emoji)'));
        const iconInput = createElement('input', { 
            className: 'form-control',
            type: 'text',
            name: 'icon',
            placeholder: 'Ex: ⚡',
            value: doc?.icon || ''
        });
        iconGroup.appendChild(iconInput);
        form.appendChild(iconGroup);

        // Description
        const descGroup = createElement('div', { className: 'form-group' });
        descGroup.appendChild(createElement('label', {}, 'Description'));
        const descInput = createElement('textarea', { 
            className: 'form-control',
            name: 'description',
            placeholder: 'Description courte du document',
            rows: 2
        });
        descInput.value = doc?.description || '';
        descGroup.appendChild(descInput);
        form.appendChild(descGroup);

        // Contenu
        const contentGroup = createElement('div', { className: 'form-group' });
        contentGroup.appendChild(createElement('label', {}, 'Contenu *'));
        const contentInput = createElement('textarea', { 
            className: 'form-control',
            name: 'content',
            placeholder: 'Contenu du document (Markdown supporté)',
            rows: 10,
            required: true
        });
        contentInput.value = doc?.content || '';
        contentGroup.appendChild(contentInput);
        form.appendChild(contentGroup);

        // Tags
        const tagsGroup = createElement('div', { className: 'form-group' });
        tagsGroup.appendChild(createElement('label', {}, 'Tags (séparés par des virgules)'));
        const tagsInput = createElement('input', { 
            className: 'form-control',
            type: 'text',
            name: 'tags',
            placeholder: 'Ex: python, web, api',
            value: doc?.tags?.join(', ') || ''
        });
        tagsGroup.appendChild(tagsInput);
        form.appendChild(tagsGroup);

        // Agents
        const agentsGroup = createElement('div', { className: 'form-group' });
        agentsGroup.appendChild(createElement('label', {}, 'Agents (séparés par des virgules)'));
        const agentsInput = createElement('input', { 
            className: 'form-control',
            type: 'text',
            name: 'agents',
            placeholder: 'Ex: CODEUR, BASE',
            value: doc?.agents?.join(', ') || ''
        });
        agentsGroup.appendChild(agentsInput);
        form.appendChild(agentsGroup);

        return form;
    }

    async saveDocument(form, docId, overlay) {
        const formData = new FormData(form);
        const data = {
            category: formData.get('category'),
            name: formData.get('name'),
            icon: formData.get('icon') || '',
            description: formData.get('description') || '',
            content: formData.get('content'),
            tags: formData.get('tags').split(',').map(t => t.trim()).filter(t => t),
            agents: formData.get('agents').split(',').map(a => a.trim()).filter(a => a)
        };

        try {
            const url = docId ? `${API_BASE}/api/library/${docId}` : `${API_BASE}/api/library`;
            const method = docId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `Erreur ${response.status}`);
            }

            overlay.remove();
            await this.loadDocuments(this.container);
            this.showNotification(docId ? 'Document modifié avec succès' : 'Document créé avec succès', 'success');
        } catch (error) {
            console.error('Erreur sauvegarde:', error);
            this.showNotification(`Erreur : ${error.message}`, 'error');
        }
    }

    async deleteDocument(docId, overlay) {
        try {
            const response = await fetch(`${API_BASE}/api/library/${docId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `Erreur ${response.status}`);
            }

            overlay.remove();
            await this.loadDocuments(this.container);
            this.showNotification('Document supprimé avec succès', 'success');
        } catch (error) {
            console.error('Erreur suppression:', error);
            this.showNotification(`Erreur : ${error.message}`, 'error');
        }
    }

    showNotification(message, type = 'info') {
        const notification = createElement('div', { 
            className: `notification notification-${type}` 
        }, message);
        
        document.body.appendChild(notification);
        
        setTimeout(() => notification.classList.add('show'), 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

export default LibraryViewEnhanced;
