/**
 * Projects List View - JARVIS 2.0
 * Vue liste des projets avec CRUD complet
 */

import state from '../core/state.js';
import router from '../core/router.js';
import { API_BASE_URL } from '../config.js';
import { createElement, clearContainer } from '../utils/dom.js';
import { formatDate, pluralize } from '../utils/format.js';

class ProjectsListView {
    constructor() {
        this.container = null;
        this.projects = [];
    }

    /**
     * Rend la vue
     * @param {HTMLElement} container
     */
    async render(container) {
        this.container = container;
        clearContainer(container);

        const view = createElement('div', { className: 'view-container fade-in' }, [
            this.renderHeader(),
            await this.renderProjectsList()
        ]);

        container.appendChild(view);
    }

    /**
     * Rend le header
     * @returns {HTMLElement}
     */
    renderHeader() {
        const createButton = createElement('button', {
            className: 'btn-create-project',
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
        }, '+ Nouveau Projet');

        createButton.addEventListener('click', () => this.showCreateModal());

        return createElement('div', { className: 'container' }, [
            createElement('div', { className: 'section-header' }, [
                createElement('h1', { className: 'section-title' }, '📁 Mes Projets'),
                createButton
            ])
        ]);
    }

    /**
     * Rend la liste des projets
     * @returns {HTMLElement}
     */
    async renderProjectsList() {
        await this.loadProjects();

        const container = createElement('div', { className: 'container' });

        if (this.projects.length === 0) {
            container.appendChild(this.renderEmptyState());
        } else {
            const grid = createElement('div', { className: 'grid grid-3' });
            this.projects.forEach(project => {
                grid.appendChild(this.createProjectCard(project));
            });
            container.appendChild(grid);
        }

        return container;
    }

    /**
     * Charge les projets
     */
    async loadProjects() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/projects`);
            this.projects = await response.json();
        } catch (error) {
            console.error('Erreur chargement projets:', error);
            this.projects = [];
        }
    }

    /**
     * Crée une card projet
     * @param {Object} project
     * @returns {HTMLElement}
     */
    createProjectCard(project) {
        const deleteBtn = createElement('button', {
            className: 'btn-delete-project',
            title: 'Supprimer le projet',
            style: `
                position: absolute;
                top: 0.5rem;
                right: 0.5rem;
                background: transparent;
                border: none;
                cursor: pointer;
                padding: 0.25rem 0.4rem;
                border-radius: var(--radius-sm, 4px);
                font-size: 1rem;
                line-height: 1;
                opacity: 0;
                transition: opacity var(--transition-fast, 0.15s), background 0.15s;
                z-index: 2;
            `
        }, '🗑️');

        deleteBtn.addEventListener('mouseenter', () => {
            deleteBtn.style.background = 'rgba(255,59,48,0.15)';
        });
        deleteBtn.addEventListener('mouseleave', () => {
            deleteBtn.style.background = 'transparent';
        });

        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.confirmDeleteProject(project);
        });

        const card = createElement('div', {
            className: 'card',
            style: 'cursor: pointer; position: relative;'
        }, [
            deleteBtn,
            createElement('div', { className: 'card-body' }, [
                createElement('h3', { className: 'card-title mb-sm' }, project.name),
                createElement('p', { 
                    className: 'text-secondary mb-sm',
                    style: 'font-size: 0.875rem; word-break: break-all;'
                }, project.path),
                project.description ? 
                    createElement('p', { className: 'text-muted' }, project.description) : 
                    null
            ].filter(Boolean)),
            createElement('div', { className: 'card-footer' }, [
                createElement('span', { className: 'text-muted' }, 
                    `${project.conversation_count} ${pluralize(project.conversation_count, 'conversation')}`
                ),
                createElement('span', { className: 'text-muted' }, formatDate(project.created_at))
            ])
        ]);

        card.addEventListener('mouseenter', () => {
            deleteBtn.style.opacity = '1';
        });
        card.addEventListener('mouseleave', () => {
            deleteBtn.style.opacity = '0';
        });

        card.addEventListener('click', () => {
            router.navigate(`/projects/${project.id}`);
        });

        return card;
    }

    /**
     * Confirme la suppression d'un projet
     * @param {Object} project
     */
    confirmDeleteProject(project) {
        const modal = createElement('div', {
            style: `
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: var(--z-modal, 1000);
            `
        });

        const cancelBtn = createElement('button', {
            style: `
                padding: 0.6rem 1.2rem;
                background: var(--color-surface);
                color: var(--color-text);
                border: 1px solid var(--color-border);
                border-radius: var(--radius-md);
                cursor: pointer;
                font-weight: 500;
            `
        }, 'Annuler');

        const confirmBtn = createElement('button', {
            style: `
                padding: 0.6rem 1.2rem;
                background: #ff3b30;
                color: white;
                border: none;
                border-radius: var(--radius-md);
                cursor: pointer;
                font-weight: 600;
            `
        }, 'Supprimer');

        const box = createElement('div', {
            style: `
                background: var(--color-surface);
                padding: 2rem;
                border-radius: var(--radius-lg);
                max-width: 400px;
                width: 90%;
                text-align: center;
            `
        }, [
            createElement('p', { style: 'font-size: 2rem; margin-bottom: 0.75rem;' }, '🗑️'),
            createElement('h3', { style: 'margin-bottom: 0.5rem;' }, 'Supprimer ce projet ?'),
            createElement('p', { 
                className: 'text-muted',
                style: 'margin-bottom: 1.5rem; font-size: 0.9rem;'
            }, `"${project.name}" sera supprimé définitivement.`),
            createElement('div', { style: 'display: flex; gap: 0.75rem; justify-content: center;' }, [
                cancelBtn,
                confirmBtn
            ])
        ]);

        cancelBtn.addEventListener('click', () => modal.remove());
        modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });

        confirmBtn.addEventListener('click', async () => {
            confirmBtn.textContent = '...';
            confirmBtn.disabled = true;
            await this.deleteProject(project.id);
            modal.remove();
        });

        modal.appendChild(box);
        document.body.appendChild(modal);
    }

    /**
     * Supprime un projet via l'API
     * @param {string} projectId
     */
    async deleteProject(projectId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                await this.render(this.container);
            } else {
                const error = await response.json();
                alert(error.detail || 'Erreur lors de la suppression.');
            }
        } catch (error) {
            console.error('Erreur suppression projet:', error);
            alert('Erreur de connexion au serveur.');
        }
    }

    /**
     * Rend l'état vide
     * @returns {HTMLElement}
     */
    renderEmptyState() {
        return createElement('div', { className: 'empty-state' }, [
            createElement('div', { className: 'empty-state-icon' }, '📁'),
            createElement('h3', { className: 'empty-state-title' }, 'Aucun projet'),
            createElement('p', { className: 'empty-state-description' }, 
                'Créez votre premier projet pour commencer à travailler avec JARVIS.'
            ),
            createElement('button', {
                className: 'btn-create-project',
                style: `
                    padding: 0.75rem 1.5rem;
                    background-color: var(--color-primary);
                    color: white;
                    border: none;
                    border-radius: var(--radius-md);
                    font-weight: 600;
                    cursor: pointer;
                `
            }, '+ Créer un Projet')
        ]);
    }

    /**
     * Affiche le modal de création
     */
    showCreateModal() {
        const modal = createElement('div', {
            style: `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: var(--z-modal);
            `
        });

        const form = this.createProjectForm();
        modal.appendChild(form);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        document.body.appendChild(modal);
    }

    /**
     * Crée le formulaire de projet
     * @returns {HTMLElement}
     */
    createProjectForm() {
        const nameInput = createElement('input', {
            type: 'text',
            placeholder: 'Nom du projet',
            required: true,
            style: `
                width: 100%;
                padding: 0.75rem;
                background: var(--color-bg);
                border: 1px solid var(--color-border);
                border-radius: var(--radius-md);
                color: var(--color-text);
                margin-bottom: 1rem;
            `
        });

        const pathInput = createElement('input', {
            type: 'text',
            placeholder: 'Chemin du projet (ex: D:/Coding/MonProjet)',
            required: true,
            style: `
                width: 100%;
                padding: 0.75rem;
                background: var(--color-bg);
                border: 1px solid var(--color-border);
                border-radius: var(--radius-md);
                color: var(--color-text);
                margin-bottom: 1rem;
            `
        });

        const descInput = createElement('textarea', {
            placeholder: 'Description (optionnel)',
            rows: 3,
            style: `
                width: 100%;
                padding: 0.75rem;
                background: var(--color-bg);
                border: 1px solid var(--color-border);
                border-radius: var(--radius-md);
                color: var(--color-text);
                margin-bottom: 1rem;
                resize: vertical;
            `
        });

        const submitButton = createElement('button', {
            type: 'submit',
            style: `
                padding: 0.75rem 1.5rem;
                background: var(--color-primary);
                color: white;
                border: none;
                border-radius: var(--radius-md);
                font-weight: 600;
                cursor: pointer;
            `
        }, 'Créer');

        const formElement = createElement('form', {
            style: `
                background: var(--color-surface);
                padding: 2rem;
                border-radius: var(--radius-lg);
                max-width: 500px;
                width: 90%;
            `
        }, [
            createElement('h2', { style: 'margin-bottom: 1.5rem;' }, 'Nouveau Projet'),
            nameInput,
            pathInput,
            descInput,
            submitButton
        ]);

        formElement.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.createProject({
                name: nameInput.value,
                path: pathInput.value,
                description: descInput.value || undefined
            });
            formElement.closest('[style*="position: fixed"]').remove();
        });

        return formElement;
    }

    /**
     * Crée un projet
     * @param {Object} data
     */
    async createProject(data) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/projects`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const project = await response.json();
                router.navigate(`/projects/${project.id}`);
            } else {
                const error = await response.json();
                alert(error.detail || 'Erreur lors de la création du projet.');
            }
        } catch (error) {
            console.error('Erreur création projet:', error);
            alert('Erreur de connexion au serveur.');
        }
    }

    /**
     * Nettoie la vue
     */
    destroy() {
        if (this.container) {
            clearContainer(this.container);
        }
    }
}

export default ProjectsListView;
