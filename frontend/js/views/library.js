/**
 * Library View - JARVIS 2.0
 * Vue de la bibliothèque de documents avec CRUD complet
 */

import { createElement, clearContainer } from '../utils/dom.js';
import { API_BASE_URL, RAG_API_URL } from '../config.js';

const API_BASE = API_BASE_URL;
const RAG_API = RAG_API_URL;

const CATEGORY_METADATA = {
    'patterns': {
        name: 'Patterns de Code',
        icon: '📝',
        description: 'Patterns de code validés pour génération'
    },
    'rules': {
        name: 'Règles & Standards',
        icon: '📋',
        description: 'Règles de développement et standards'
    },
    'templates': {
        name: 'Templates',
        icon: '📄',
        description: 'Templates de code réutilisables'
    },
    'assets': {
        name: 'Assets',
        icon: '🎨',
        description: 'Ressources et assets'
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
            const response = await fetch(`${RAG_API}/rag/library/list`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            if (data.status === 'success') {
                this.documents = data.documents || [];
                this.categories = data.categories || [];
            } else {
                throw new Error(data.message || 'Erreur serveur RAG');
            }
        } catch (error) {
            console.error('Erreur chargement library RAG:', error);
            this.documents = [];
            this.categories = [];
        }
    }

    groupByCategory(documents) {
        const grouped = {};
        documents.forEach(doc => {
            if (!grouped[doc.category]) {
                const meta = CATEGORY_METADATA[doc.category] || {
                    name: doc.category.charAt(0).toUpperCase() + doc.category.slice(1),
                    icon: '📄',
                    description: ''
                };
                grouped[doc.category] = {
                    id: doc.category,
                    ...meta,
                    count: 0,
                    documents: []
                };
            }
            grouped[doc.category].documents.push(doc);
            grouped[doc.category].count++;
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
        headerContent.appendChild(createElement('h1', {}, '📚 Librairie RAG'));
        const subtitle = `Patterns de code et ressources pour les agents • ${this.documents.length} documents`;
        headerContent.appendChild(createElement('p', { className: 'header-subtitle' }, subtitle));
        header.appendChild(headerContent);

        // Pas de bouton "Nouveau document" - la librairie RAG est gérée via fichiers sur disque
        const headerActions = createElement('div', { className: 'header-actions' });
        const infoText = createElement('span', { className: 'header-info' }, '📁 Fichiers dans RAG/library/');
        headerActions.appendChild(infoText);
        header.appendChild(headerActions);

        return header;
    }

    renderStats() {
        const totalDocs = this.documents.length;
        const totalCats = this.categories.length;
        
        // Compter par catégorie RAG
        const patterns = this.documents.filter(doc => doc.category === 'patterns').length;
        const rules = this.documents.filter(doc => doc.category === 'rules').length;
        const templates = this.documents.filter(doc => doc.category === 'templates').length;
        const assets = this.documents.filter(doc => doc.category === 'assets').length;

        const stats = createElement('div', { className: 'library-stats' });
        stats.appendChild(this.createStatCard('📊', String(totalDocs), 'Documents total'));
        stats.appendChild(this.createStatCard('�', String(patterns), 'Patterns'));
        stats.appendChild(this.createStatCard('📋', String(rules), 'Règles'));
        stats.appendChild(this.createStatCard('�', String(templates), 'Templates'));
        stats.appendChild(this.createStatCard('🎨', String(assets), 'Assets'));
        return stats;
    }

    renderAllCategories() {
        const container = createElement('div', { className: 'categories-container' });
        
        // Ordre d'affichage des catégories RAG
        const categoryOrder = ['patterns', 'rules', 'templates', 'assets'];
        
        categoryOrder.forEach(categoryId => {
            const category = this.categories.find(cat => cat.name && cat.name.toLowerCase().includes(categoryId));
            if (category && category.documents && category.documents.length > 0) {
                container.appendChild(this.renderCategorySection(category));
            }
        });
        
        return container;
    }

    renderCategorySection(category) {
        const section = createElement('div', { className: 'category-section' });
        
        // Récupérer métadonnées de la catégorie
        const meta = CATEGORY_METADATA[category.name.toLowerCase()] || CATEGORY_METADATA[Object.keys(CATEGORY_METADATA).find(k => category.name.toLowerCase().includes(k))] || {
            icon: '📄',
            description: ''
        };
        
        // Header de catégorie
        const header = createElement('div', { className: 'category-header' });
        const title = createElement('h2', {}, `${meta.icon} ${category.name}`);
        const count = createElement('span', { className: 'category-count' }, `${category.count || category.documents.length} documents`);
        header.appendChild(title);
        header.appendChild(count);
        section.appendChild(header);
        
        if (meta.description) {
            const desc = createElement('p', { className: 'category-description' }, meta.description);
            section.appendChild(desc);
        }
        
        // Liste des documents
        const list = createElement('div', { className: 'documents-list' });
        category.documents.forEach(doc => list.appendChild(this.renderDocumentItem(doc, false)));
        
        section.appendChild(list);
        return section;
    }

    renderDocumentItem(doc, isConfig) {
        const item = createElement('div', { className: `document-item ${isConfig ? 'config-item' : ''}` });
        
        // En-tête : icône + nom
        const itemHeader = createElement('div', { className: 'item-header' });
        const icon = createElement('span', { className: 'item-icon' }, '📄');
        const name = createElement('h4', { className: 'item-name' }, doc.title || doc.name);
        itemHeader.appendChild(icon);
        itemHeader.appendChild(name);
        item.appendChild(itemHeader);
        
        // Description
        if (doc.description) {
            const desc = createElement('p', { className: 'item-description' }, doc.description);
            item.appendChild(desc);
        }
        
        // Métadonnées : taille + extension
        const meta = createElement('div', { className: 'item-meta' });
        const sizeKb = Math.round(doc.size / 1024);
        meta.appendChild(createElement('span', { className: 'meta-label' }, `${sizeKb} Ko • ${doc.extension}`));
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

    async showDocumentModal(doc) {
        const overlay = createElement('div', { className: 'library-modal-overlay' });
        const modal = createElement('div', { className: 'library-modal library-modal-large' });

        const header = createElement('div', { className: 'library-modal-header' });
        header.appendChild(createElement('h2', {}, `📄 ${doc.title || doc.name}`));
        const closeBtn = createElement('button', {
            className: 'library-modal-close',
            onclick: () => overlay.remove()
        }, '×');
        header.appendChild(closeBtn);
        modal.appendChild(header);

        const body = createElement('div', { className: 'library-modal-body' });
        
        // Afficher loading
        const loadingDiv = createElement('div', { className: 'loading' }, 'Chargement du contenu...');
        body.appendChild(loadingDiv);
        modal.appendChild(body);
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Récupérer le contenu depuis le serveur RAG
        try {
            const response = await fetch(`${RAG_API}/rag/library/document/${doc.category}/${doc.name}`);
            const data = await response.json();
            
            if (data.status === 'success' && data.document) {
                const fullDoc = data.document;
                
                // Remplacer loading par contenu
                clearContainer(body);
                
                if (doc.description) {
                    body.appendChild(createElement('p', { className: 'doc-description' }, doc.description));
                }

                const meta = createElement('div', { className: 'doc-meta' });
                const sizeKb = Math.round(fullDoc.size / 1024);
                meta.appendChild(createElement('span', { className: 'meta-label' }, `Taille: ${sizeKb} Ko • Extension: ${fullDoc.extension}`));
                body.appendChild(meta);

                const contentDiv = createElement('div', { className: 'doc-content' });
                const pre = createElement('pre');
                const code = createElement('code');
                code.textContent = fullDoc.content || 'Aucun contenu disponible';
                pre.appendChild(code);
                contentDiv.appendChild(pre);
                body.appendChild(contentDiv);
            } else {
                throw new Error(data.message || 'Erreur chargement document');
            }
        } catch (error) {
            console.error('Erreur chargement document:', error);
            clearContainer(body);
            body.appendChild(createElement('p', { className: 'error' }, `Erreur: ${error.message}`));
        }

        const footer = createElement('div', { className: 'library-modal-footer' });
        const actions = createElement('div', { className: 'modal-actions' });
        
        const closeFooterBtn = createElement('button', {
            className: 'btn btn-secondary',
            onclick: () => overlay.remove()
        }, 'Fermer');
        actions.appendChild(closeFooterBtn);

        footer.appendChild(actions);
        modal.appendChild(footer);

        overlay.onclick = (e) => {
            if (e.target === overlay) overlay.remove();
        };
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
