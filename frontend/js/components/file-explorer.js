/**
 * File Explorer Component - JARVIS 2.0
 * Explorateur de fichiers pour les projets
 */

import { createElement, clearContainer } from '../utils/dom.js';
import { API_BASE_URL } from '../config.js';
import { formatFileSize } from '../utils/format.js';

class FileExplorer {
    constructor(options = {}) {
        this.projectId = options.projectId;
        this.onFileSelect = options.onFileSelect;
        
        this.element = null;
        this.fileTree = null;
        this.currentPath = '';
    }

    /**
     * Rend le composant
     * @returns {HTMLElement}
     */
    async render() {
        this.element = createElement('div', { className: 'file-explorer' });

        await this.loadFileTree();
        this.renderFileTree();

        return this.element;
    }

    /**
     * Charge l'arborescence des fichiers
     */
    async loadFileTree() {
        if (!this.projectId) return;

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/projects/${this.projectId}/files/tree?max_depth=3`
            );
            this.fileTree = await response.json();
        } catch (error) {
            console.error('Erreur chargement fichiers:', error);
            this.fileTree = null;
        }
    }

    /**
     * Affiche l'arborescence
     */
    renderFileTree() {
        clearContainer(this.element);

        // Header
        const header = createElement('div', {
            style: `
                padding: var(--spacing-md);
                border-bottom: 1px solid var(--color-border);
            `
        }, [
            createElement('h3', { 
                style: 'font-size: 1rem; font-weight: 600;'
            }, '📂 Fichiers')
        ]);

        this.element.appendChild(header);

        // Tree container
        const treeContainer = createElement('div', {
            className: 'file-tree-container',
            style: 'padding: var(--spacing-sm); overflow-y: auto;'
        });

        if (this.fileTree) {
            treeContainer.appendChild(this.renderNode(this.fileTree, 0));
        } else {
            treeContainer.appendChild(this.renderEmptyState());
        }

        this.element.appendChild(treeContainer);
    }

    /**
     * Rend un nœud de l'arbre
     * @param {Object} node
     * @param {number} level
     * @returns {HTMLElement}
     */
    renderNode(node, level) {
        const container = createElement('div', {
            style: `margin-left: ${level * 16}px;`
        });

        if (node.type === 'directory') {
            container.appendChild(this.renderDirectory(node, level));
        } else {
            container.appendChild(this.renderFile(node));
        }

        return container;
    }

    /**
     * Rend un dossier
     * @param {Object} dir
     * @param {number} level
     * @returns {HTMLElement}
     */
    renderDirectory(dir, level) {
        const isExpanded = true; // Par défaut ouvert

        const dirElement = createElement('div', { className: 'directory-item' });

        // Header du dossier
        const header = createElement('div', {
            style: `
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.25rem 0.5rem;
                cursor: pointer;
                border-radius: var(--radius-sm);
                transition: background-color var(--transition-fast);
            `
        }, [
            createElement('span', {}, isExpanded ? '📂' : '📁'),
            createElement('span', {
                style: 'font-size: 0.875rem; font-weight: 500;'
            }, dir.name)
        ]);

        header.addEventListener('mouseenter', () => {
            header.style.backgroundColor = 'var(--color-surface-hover)';
        });

        header.addEventListener('mouseleave', () => {
            header.style.backgroundColor = 'transparent';
        });

        dirElement.appendChild(header);

        // Contenu du dossier
        if (isExpanded && dir.items && dir.items.length > 0) {
            const content = createElement('div', { className: 'directory-content' });
            dir.items.forEach(item => {
                content.appendChild(this.renderNode(item, level + 1));
            });
            dirElement.appendChild(content);
        }

        return dirElement;
    }

    /**
     * Rend un fichier
     * @param {Object} file
     * @returns {HTMLElement}
     */
    renderFile(file) {
        const fileElement = createElement('div', {
            className: 'file-item',
            style: `
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.25rem 0.5rem;
                cursor: pointer;
                border-radius: var(--radius-sm);
                transition: all var(--transition-fast);
            `
        }, [
            createElement('span', {}, this.getFileIcon(file.extension)),
            createElement('span', {
                style: 'font-size: 0.875rem; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
            }, file.name),
            file.size ? createElement('span', {
                style: 'font-size: 0.75rem; color: var(--color-text-muted);'
            }, formatFileSize(file.size)) : null
        ].filter(Boolean));

        fileElement.addEventListener('click', async () => {
            await this.handleFileClick(file);
        });

        fileElement.addEventListener('mouseenter', () => {
            fileElement.style.backgroundColor = 'var(--color-primary-light)';
            fileElement.style.color = 'var(--color-primary)';
        });

        fileElement.addEventListener('mouseleave', () => {
            fileElement.style.backgroundColor = 'transparent';
            fileElement.style.color = 'var(--color-text)';
        });

        return fileElement;
    }

    /**
     * Récupère l'icône d'un fichier selon son extension
     * @param {string} extension
     * @returns {string}
     */
    getFileIcon(extension) {
        const icons = {
            '.py': '🐍',
            '.js': '📜',
            '.ts': '📘',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📋',
            '.md': '📝',
            '.txt': '📄',
            '.sql': '🗄️',
            '.env': '🔐',
            '.git': '🔧'
        };

        return icons[extension] || '📄';
    }

    /**
     * Gère le clic sur un fichier
     * @param {Object} file
     */
    async handleFileClick(file) {
        if (this.onFileSelect) {
            try {
                // Construire le chemin relatif
                const path = file.path || file.name;
                
                // Charger le contenu du fichier
                const response = await fetch(
                    `${API_BASE_URL}/api/projects/${this.projectId}/files/read?path=${encodeURIComponent(path)}`
                );

                if (response.ok) {
                    const data = await response.json();
                    this.onFileSelect({
                        name: file.name,
                        path: path,
                        content: data.content,
                        size: data.size
                    });
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Erreur lors de la lecture du fichier.');
                }
            } catch (error) {
                console.error('Erreur lecture fichier:', error);
                alert('Erreur de connexion au serveur.');
            }
        }
    }

    /**
     * Rend l'état vide
     * @returns {HTMLElement}
     */
    renderEmptyState() {
        return createElement('div', {
            style: 'padding: var(--spacing-lg); text-align: center; color: var(--color-text-muted);'
        }, [
            createElement('div', { style: 'font-size: 2rem; margin-bottom: 0.5rem;' }, '📂'),
            createElement('p', { style: 'font-size: 0.875rem;' }, 'Aucun fichier')
        ]);
    }

    /**
     * Rafraîchit l'arborescence
     */
    async refresh() {
        await this.loadFileTree();
        this.renderFileTree();
    }
}

export default FileExplorer;
