/**
 * Library View - JARVIS 2.0
 * Vue de la bibliothèque de documents avec CRUD complet
 */

import { createElement, clearContainer } from '../utils/dom.js';

const API_BASE = 'http://localhost:8000';

const CATEGORY_METADATA = {
    'personal': {
        name: 'Personnel',
        icon: '�',
        description: '11 documents : 5 CONFIG (profil, workflow, architecture, règles, comportement) + 6 autres (conventions, stack, workflow quotidien, UI/UX, erreurs, Flutter)'
    },
    'libraries': {
        name: 'Librairies & Frameworks',
        icon: '�',
        description: '10 documents : FastAPI, Pytest, Pydantic, aiosqlite, Flutter, asyncio, pathlib, JSON, datetime, uuid'
    },
    'methodologies': {
        name: 'Méthodologies',
        icon: '�',
        description: '9 documents : Audit>Plan>Exécution, Gouvernance docs, Revue code, Gestion erreurs, Architecture JARVIS, Tests Python, Git workflow, Code review, Refactoring'
    },
    'prompts': {
        name: 'Prompts & Templates',
        icon: '�',
        description: '6 documents : Délégation CODEUR, Vérification BASE, Création projet, Analyse dette, Debugging, Optimisation'
    },
    'tools': {
        name: 'Outils & Productivité',
        icon: '🛠️',
        description: '4 documents : VS Code shortcuts, PowerShell essentials, Debugging Python, Gemini AI'
    }
};

class LibraryView {
    constructor() {
        this.container = null;
        this.documents = [];
        this.categories = [];
        this.activeFilter = 'all';
    }

    async render(container) {
        this.container = container;
        clearContainer(container);

        const view = createElement('div', { className: 'library-view' });
        const content = createElement('div', { className: 'library-content' });
        
        view.appendChild(content);
        container.appendChild(view);

        await this.fetchLibraryData();
        this.renderContent(content);
    }

    async fetchLibraryData() {
        try {
            const response = await fetch(`${API_BASE}/api/library`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            this.documents = await response.json();
            this.categories = this.groupByCategory(this.documents);
        } catch (error) {
            console.error('Erreur chargement library:', error);
            this.documents = [];
            this.categories = [];
        }
    }

    groupByCategory(documents) {
        const grouped = {};
        documents.forEach(doc => {
            if (!grouped[doc.category]) {
                const meta = CATEGORY_METADATA[doc.category] || {
                    name: doc.category,
                    icon: '📄',
                    description: ''
                };
                grouped[doc.category] = {
                    id: doc.category,
                    ...meta,
                    items: []
                };
            }
            grouped[doc.category].items.push(doc);
        });
        return Object.values(grouped);
    }

    renderContent(content) {
        clearContainer(content);
        
        content.appendChild(this.renderHeader());
        content.appendChild(this.renderStats());
        
        // Afficher toutes les catégories avec leurs documents
        content.appendChild(this.renderAllCategories());
    }

    renderHeader() {
        const header = createElement('div', { className: 'library-header' });
        
        const headerContent = createElement('div', { className: 'header-content' });
        headerContent.appendChild(createElement('h1', {}, '📚 Library'));
        const subtitle = `Base de connaissances pour les agents et l'utilisateur • ${this.documents.length} documents`;
        headerContent.appendChild(createElement('p', { className: 'header-subtitle' }, subtitle));
        header.appendChild(headerContent);

        const headerActions = createElement('div', { className: 'header-actions' });
        const addBtn = createElement('button', {
            className: 'btn btn-primary',
            onclick: () => this.showCreateModal()
        }, '+ Nouveau document');
        headerActions.appendChild(addBtn);
        header.appendChild(headerActions);

        return header;
    }

    renderStats() {
        const totalDocs = this.documents.length;
        const totalCats = this.categories.length;
        
        // Compter par catégorie
        const personal = this.documents.filter(doc => doc.category === 'personal').length;
        const libraries = this.documents.filter(doc => doc.category === 'libraries').length;
        const methodologies = this.documents.filter(doc => doc.category === 'methodologies').length;
        const prompts = this.documents.filter(doc => doc.category === 'prompts').length;
        const tools = this.documents.filter(doc => doc.category === 'tools').length;
        
        const configDocs = this.documents.filter(doc => doc.category === 'personal' && doc.tags && doc.tags.includes('config')).length;
        const agents = new Set();
        this.documents.forEach(doc => {
            (doc.agents || []).forEach(a => agents.add(a));
        });

        const stats = createElement('div', { className: 'library-stats' });
        stats.appendChild(this.createStatCard('�', String(totalDocs), 'Documents total'));
        stats.appendChild(this.createStatCard('👤', String(personal), 'Personal (dont 5 CONFIG)'));
        stats.appendChild(this.createStatCard('📚', String(libraries), 'Libraries'));
        stats.appendChild(this.createStatCard('�', String(methodologies), 'Méthodologies'));
        stats.appendChild(this.createStatCard('💬', String(prompts), 'Prompts'));
        stats.appendChild(this.createStatCard('🛠️', String(tools), 'Tools'));
        return stats;
    }

    renderAllCategories() {
        const container = createElement('div', { className: 'categories-container' });
        
        // Ordre d'affichage des catégories
        const categoryOrder = ['personal', 'libraries', 'methodologies', 'prompts', 'tools'];
        
        categoryOrder.forEach(categoryId => {
            const category = this.categories.find(cat => cat.id === categoryId);
            if (category && category.items.length > 0) {
                container.appendChild(this.renderCategorySection(category));
            }
        });
        
        return container;
    }

    renderCategorySection(category) {
        const section = createElement('div', { className: 'category-section' });
        
        // Header de catégorie
        const header = createElement('div', { className: 'category-header' });
        const title = createElement('h2', {}, `${category.icon} ${category.name}`);
        const count = createElement('span', { className: 'category-count' }, `${category.items.length} documents`);
        header.appendChild(title);
        header.appendChild(count);
        section.appendChild(header);
        
        if (category.description) {
            const desc = createElement('p', { className: 'category-description' }, category.description);
            section.appendChild(desc);
        }
        
        // Liste des documents
        const list = createElement('div', { className: 'documents-list' });
        
        // Séparer CONFIG des autres si catégorie personal
        if (category.id === 'personal') {
            const configDocs = category.items.filter(doc => doc.tags && doc.tags.includes('config'));
            const otherDocs = category.items.filter(doc => !doc.tags || !doc.tags.includes('config'));
            
            if (configDocs.length > 0) {
                const configHeader = createElement('h3', { className: 'subsection-title' }, '⚙️ Documents de Configuration');
                list.appendChild(configHeader);
                configDocs.forEach(doc => list.appendChild(this.renderDocumentItem(doc, true)));
            }
            
            if (otherDocs.length > 0) {
                const otherHeader = createElement('h3', { className: 'subsection-title' }, '📄 Autres documents personnels');
                list.appendChild(otherHeader);
                otherDocs.forEach(doc => list.appendChild(this.renderDocumentItem(doc, false)));
            }
        } else {
            category.items.forEach(doc => list.appendChild(this.renderDocumentItem(doc, false)));
        }
        
        section.appendChild(list);
        return section;
    }

    renderDocumentItem(doc, isConfig) {
        const item = createElement('div', { className: `document-item ${isConfig ? 'config-item' : ''}` });
        
        // En-tête : icône + nom + badge CONFIG si applicable
        const itemHeader = createElement('div', { className: 'item-header' });
        const icon = createElement('span', { className: 'item-icon' }, doc.icon || '📄');
        const name = createElement('h4', { className: 'item-name' }, doc.name);
        itemHeader.appendChild(icon);
        itemHeader.appendChild(name);
        
        if (isConfig) {
            const badge = createElement('span', { className: 'config-badge-inline' }, 'CONFIG');
            itemHeader.appendChild(badge);
        }
        
        item.appendChild(itemHeader);
        
        // Description
        if (doc.description) {
            const desc = createElement('p', { className: 'item-description' }, doc.description);
            item.appendChild(desc);
        }
        
        // Métadonnées : tags + agents
        const meta = createElement('div', { className: 'item-meta' });
        
        if (doc.tags && doc.tags.length > 0) {
            const tagsLabel = createElement('span', { className: 'meta-label' }, 'Tags: ');
            meta.appendChild(tagsLabel);
            const tagsContainer = createElement('span', { className: 'meta-tags' });
            doc.tags.forEach((tag, index) => {
                const tagSpan = createElement('span', { className: 'tag-inline' }, tag);
                tagsContainer.appendChild(tagSpan);
                if (index < doc.tags.length - 1) {
                    tagsContainer.appendChild(document.createTextNode(', '));
                }
            });
            meta.appendChild(tagsContainer);
        }
        
        if (doc.agents && doc.agents.length > 0) {
            if (doc.tags && doc.tags.length > 0) {
                meta.appendChild(createElement('span', { className: 'meta-separator' }, ' • '));
            }
            const agentsLabel = createElement('span', { className: 'meta-label' }, 'Agents: ');
            meta.appendChild(agentsLabel);
            const agentsContainer = createElement('span', { className: 'meta-agents' });
            doc.agents.forEach((agent, index) => {
                const agentSpan = createElement('span', { className: 'agent-inline' }, agent);
                agentsContainer.appendChild(agentSpan);
                if (index < doc.agents.length - 1) {
                    agentsContainer.appendChild(document.createTextNode(', '));
                }
            });
            meta.appendChild(agentsContainer);
        }
        
        item.appendChild(meta);
        
        // Bouton voir contenu
        const viewBtn = createElement('button', {
            className: 'btn-view-content',
            onclick: () => this.showDocumentModal(doc)
        }, '📖 Voir le contenu');
        item.appendChild(viewBtn);
        
        return item;
    }

    renderConfigCard(doc) {
        const card = createElement('div', { className: 'config-card' });

        const cardHeader = createElement('div', { className: 'config-card-header' });
        cardHeader.appendChild(createElement('span', { className: 'config-icon' }, doc.icon || '⚙️'));
        const badge = createElement('span', { className: 'config-badge' }, 'CONFIG');
        cardHeader.appendChild(badge);
        card.appendChild(cardHeader);

        const cardBody = createElement('div', { className: 'config-card-body' });
        cardBody.appendChild(createElement('h3', { className: 'config-card-title' }, doc.name));
        cardBody.appendChild(createElement('p', { className: 'config-card-description' }, doc.description || ''));
        card.appendChild(cardBody);

        const cardFooter = createElement('div', { className: 'config-card-footer' });
        if (doc.agents && doc.agents.length > 0) {
            const agentsContainer = createElement('div', { className: 'config-agents' });
            doc.agents.forEach(agent => {
                agentsContainer.appendChild(createElement('span', { className: 'agent-badge' }, agent));
            });
            cardFooter.appendChild(agentsContainer);
        }
        card.appendChild(cardFooter);

        card.onclick = () => this.showDocumentModal(doc);
        return card;
    }

    createStatCard(icon, value, label) {
        const card = createElement('div', { className: 'stat-card' });
        card.appendChild(createElement('div', { className: 'stat-icon' }, icon));
        const content = createElement('div', { className: 'stat-content' });
        content.appendChild(createElement('div', { className: 'stat-value' }, value));
        content.appendChild(createElement('div', { className: 'stat-label' }, label));
        card.appendChild(content);
        return card;
    }

    renderFilters() {
        const filters = [
            { id: 'all', label: 'Tout' },
            { id: 'libraries', label: '📚 Librairies' },
            { id: 'methodologies', label: '📋 Méthodologies' },
            { id: 'prompts', label: '💬 Prompts' },
            { id: 'personal', label: '👤 Personnel' },
            { id: 'tools', label: '🛠️ Outils' }
        ];

        const container = createElement('div', { className: 'library-filters' });
        filters.forEach(filter => {
            const btn = createElement('button', {
                className: `filter-btn ${this.activeFilter === filter.id ? 'active' : ''}`,
                onclick: () => {
                    this.activeFilter = filter.id;
                    this.renderContent(this.container.querySelector('.library-content'));
                }
            }, filter.label);
            container.appendChild(btn);
        });
        return container;
    }

    renderGrid() {
        const grid = createElement('div', { className: 'library-grid' });

        const filtered = this.activeFilter === 'all'
            ? this.categories
            : this.categories.filter(cat => cat.id === this.activeFilter);

        filtered.forEach(category => {
            category.items.forEach(doc => {
                grid.appendChild(this.renderDocumentCard(doc, category));
            });
        });

        if (grid.children.length === 0) {
            return this.renderEmptyState();
        }

        return grid;
    }

    renderEmptyState() {
        const empty = createElement('div', { className: 'empty-state' });
        empty.appendChild(createElement('div', { className: 'empty-icon' }, '📭'));
        empty.appendChild(createElement('h3', {}, 'Aucun document'));
        empty.appendChild(createElement('p', {}, 'Aucun document ne correspond à ce filtre.'));
        return empty;
    }

    renderDocumentCard(doc, category) {
        const card = createElement('div', { className: 'document-card' });

        const cardHeader = createElement('div', { className: 'card-header' });
        cardHeader.appendChild(createElement('span', { className: 'card-icon' }, doc.icon || '📄'));
        
        const headerRight = createElement('div', { className: 'card-header-right' });
        headerRight.appendChild(createElement('span', { className: 'card-category' }, category.name));
        
        // Badge CONFIG si applicable
        if (doc.category === 'personal' && doc.tags && doc.tags.includes('config')) {
            const configBadge = createElement('span', { className: 'config-badge-small' }, 'CONFIG');
            headerRight.appendChild(configBadge);
        }
        
        cardHeader.appendChild(headerRight);
        card.appendChild(cardHeader);

        const cardBody = createElement('div', { className: 'card-body' });
        cardBody.appendChild(createElement('h3', { className: 'card-title' }, doc.name));
        cardBody.appendChild(createElement('p', { className: 'card-description' }, doc.description || ''));
        card.appendChild(cardBody);

        const cardFooter = createElement('div', { className: 'card-footer' });
        if (doc.tags && doc.tags.length > 0) {
            const tagsContainer = createElement('div', { className: 'card-tags' });
            doc.tags.forEach(tag => {
                tagsContainer.appendChild(createElement('span', { className: 'tag' }, tag));
            });
            cardFooter.appendChild(tagsContainer);
        }
        if (doc.agents && doc.agents.length > 0) {
            const agentsContainer = createElement('div', { className: 'card-agents' });
            doc.agents.forEach(agent => {
                agentsContainer.appendChild(createElement('span', { className: 'agent-badge' }, agent));
            });
            cardFooter.appendChild(agentsContainer);
        }
        card.appendChild(cardFooter);

        card.onclick = () => this.showDocumentModal(doc);
        return card;
    }

    showDocumentModal(doc) {
        const overlay = createElement('div', { className: 'library-modal-overlay' });
        const modal = createElement('div', { className: 'library-modal library-modal-large' });

        const header = createElement('div', { className: 'library-modal-header' });
        header.appendChild(createElement('h2', {}, `${doc.icon || '📄'} ${doc.name}`));
        const closeBtn = createElement('button', {
            className: 'library-modal-close',
            onclick: () => overlay.remove()
        }, '×');
        header.appendChild(closeBtn);
        modal.appendChild(header);

        const body = createElement('div', { className: 'library-modal-body' });
        if (doc.description) {
            body.appendChild(createElement('p', { className: 'doc-description' }, doc.description));
        }

        const meta = createElement('div', { className: 'doc-meta' });
        if (doc.tags && doc.tags.length > 0) {
            meta.appendChild(createElement('strong', {}, 'Tags: '));
            const tagsContainer = createElement('div', { className: 'doc-tags' });
            doc.tags.forEach(tag => {
                tagsContainer.appendChild(createElement('span', { className: 'tag' }, tag));
            });
            meta.appendChild(tagsContainer);
        }
        if (doc.agents && doc.agents.length > 0) {
            meta.appendChild(createElement('strong', {}, 'Agents: '));
            const agentsContainer = createElement('div', { className: 'doc-agents' });
            doc.agents.forEach(agent => {
                agentsContainer.appendChild(createElement('span', { className: 'agent-badge' }, agent));
            });
            meta.appendChild(agentsContainer);
        }
        body.appendChild(meta);

        const contentDiv = createElement('div', { className: 'doc-content' });
        const pre = createElement('pre');
        const code = createElement('code');
        code.textContent = doc.content || 'Aucun contenu disponible';
        pre.appendChild(code);
        contentDiv.appendChild(pre);
        body.appendChild(contentDiv);
        modal.appendChild(body);

        const footer = createElement('div', { className: 'library-modal-footer' });
        const actions = createElement('div', { className: 'modal-actions' });
        
        const editBtn = createElement('button', {
            className: 'btn btn-primary',
            onclick: () => {
                overlay.remove();
                this.showEditModal(doc);
            }
        }, 'Éditer');
        actions.appendChild(editBtn);

        const deleteBtn = createElement('button', {
            className: 'btn btn-danger',
            onclick: () => {
                overlay.remove();
                this.deleteDocument(doc);
            }
        }, 'Supprimer');
        actions.appendChild(deleteBtn);

        const closeFooterBtn = createElement('button', {
            className: 'btn btn-secondary',
            onclick: () => overlay.remove()
        }, 'Fermer');
        actions.appendChild(closeFooterBtn);

        footer.appendChild(actions);
        modal.appendChild(footer);
        overlay.appendChild(modal);

        overlay.onclick = (e) => {
            if (e.target === overlay) overlay.remove();
        };

        document.body.appendChild(overlay);
    }

    showCreateModal() {
        this.showFormModal(null);
    }

    showEditModal(doc) {
        this.showFormModal(doc);
    }

    showFormModal(doc) {
        const isEdit = !!doc;
        const overlay = createElement('div', { className: 'library-modal-overlay' });
        const modal = createElement('div', { className: 'library-modal' });

        const header = createElement('div', { className: 'library-modal-header' });
        header.appendChild(createElement('h2', {}, isEdit ? 'Éditer le document' : 'Nouveau document'));
        const closeBtn = createElement('button', {
            className: 'library-modal-close',
            onclick: () => overlay.remove()
        }, '×');
        header.appendChild(closeBtn);
        modal.appendChild(header);

        const body = createElement('div', { className: 'library-modal-body' });
        const form = createElement('form', { className: 'document-form' });

        const categories = ['libraries', 'methodologies', 'prompts', 'personal', 'tools'];
        
        form.appendChild(this.createFormGroup('Catégorie', 'select', 'category', doc?.category || 'libraries', categories));
        form.appendChild(this.createFormGroup('Nom', 'text', 'name', doc?.name || '', null, true));
        form.appendChild(this.createFormGroup('Icône', 'text', 'icon', doc?.icon || '📄'));
        form.appendChild(this.createFormGroup('Description', 'textarea', 'description', doc?.description || ''));
        form.appendChild(this.createFormGroup('Contenu (Markdown)', 'textarea', 'content', doc?.content || '', null, true, 200));
        form.appendChild(this.createFormGroup('Tags (séparés par virgules)', 'text', 'tags', (doc?.tags || []).join(', ')));
        form.appendChild(this.createFormGroup('Agents (séparés par virgules)', 'text', 'agents', (doc?.agents || []).join(', ')));

        body.appendChild(form);
        modal.appendChild(body);

        const footer = createElement('div', { className: 'library-modal-footer' });
        const saveBtn = createElement('button', {
            className: 'btn btn-primary',
            onclick: async (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                const data = {
                    category: formData.get('category'),
                    name: formData.get('name'),
                    icon: formData.get('icon'),
                    description: formData.get('description'),
                    content: formData.get('content'),
                    tags: formData.get('tags').split(',').map(t => t.trim()).filter(t => t),
                    agents: formData.get('agents').split(',').map(a => a.trim()).filter(a => a)
                };

                if (isEdit) {
                    await this.updateDocument(doc.id, data);
                } else {
                    await this.createDocument(data);
                }
                overlay.remove();
            }
        }, 'Enregistrer');
        footer.appendChild(saveBtn);

        const cancelBtn = createElement('button', {
            className: 'btn btn-secondary',
            onclick: () => overlay.remove()
        }, 'Annuler');
        footer.appendChild(cancelBtn);

        modal.appendChild(footer);
        overlay.appendChild(modal);

        overlay.onclick = (e) => {
            if (e.target === overlay) overlay.remove();
        };

        document.body.appendChild(overlay);
    }

    createFormGroup(label, type, name, value = '', options = null, required = false, rows = null) {
        const group = createElement('div', { className: 'form-group' });
        const labelEl = createElement('label', {}, label + (required ? ' *' : ''));
        group.appendChild(labelEl);

        let input;
        if (type === 'select') {
            input = createElement('select', { className: 'form-control', name });
            options.forEach(opt => {
                const option = createElement('option', { value: opt }, CATEGORY_METADATA[opt]?.name || opt);
                if (opt === value) option.selected = true;
                input.appendChild(option);
            });
        } else if (type === 'textarea') {
            input = createElement('textarea', {
                className: 'form-control',
                name,
                rows: rows || 4
            });
            input.value = value;
        } else {
            input = createElement('input', {
                type,
                className: 'form-control',
                name,
                value
            });
        }

        if (required) input.required = true;
        group.appendChild(input);
        return group;
    }

    async createDocument(data) {
        try {
            const response = await fetch(`${API_BASE}/api/library`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            await this.fetchLibraryData();
            this.renderContent(this.container.querySelector('.library-content'));
        } catch (error) {
            console.error('Erreur création:', error);
            alert(`Erreur: ${error.message}`);
        }
    }

    async updateDocument(id, data) {
        try {
            const response = await fetch(`${API_BASE}/api/library/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            await this.fetchLibraryData();
            this.renderContent(this.container.querySelector('.library-content'));
        } catch (error) {
            console.error('Erreur mise à jour:', error);
            alert(`Erreur: ${error.message}`);
        }
    }

    async deleteDocument(doc) {
        if (!confirm(`Supprimer "${doc.name}" ?`)) return;
        
        try {
            const response = await fetch(`${API_BASE}/api/library/${doc.id}`, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            await this.fetchLibraryData();
            this.renderContent(this.container.querySelector('.library-content'));
        } catch (error) {
            console.error('Erreur suppression:', error);
            alert(`Erreur: ${error.message}`);
        }
    }

    destroy() {
        if (this.container) {
            clearContainer(this.container);
        }
    }
}

export default LibraryView;
