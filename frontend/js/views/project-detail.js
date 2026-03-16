/**
 * Project Detail View - JARVIS 2.0
 * Vue détail projet avec 3 colonnes (conversations+workflow, chat, fichiers)
 */

import state from '../core/state.js';
import { API_BASE_URL } from '../config.js';
import { createElement, clearContainer } from '../utils/dom.js';
import ConversationList from '../components/conversation-list.js';
import Chat from '../components/chat.js';
import FileExplorer from '../components/file-explorer.js';
import { WorkflowMonitor } from '../components/workflow-monitor.js';

class ProjectDetailView {
    constructor() {
        this.container = null;
        this.projectId = null;
        this.project = null;
        
        this.conversationList = null;
        this.chat = null;
        this.fileExplorer = null;
        this.workflowMonitor = null;
        
        this.currentConversationId = null;
        this.currentMissionId = null;
    }

    /**
     * Rend la vue
     * @param {HTMLElement} container
     * @param {Object} params - { id: projectId }
     */
    async render(container, params) {
        this.container = container;
        this.projectId = params.id;
        
        clearContainer(container);

        // Charger le projet
        await this.loadProject();

        if (!this.project) {
            container.appendChild(this.renderError());
            return;
        }

        // Créer layout 3 colonnes
        const view = createElement('div', { 
            className: 'layout-three-columns fade-in',
            style: 'height: 100%; display: grid; grid-template-columns: 280px 1fr 280px; gap: 0;'
        }, [
            await this.renderConversationsAndWorkflowColumn(),
            this.renderChatColumn(),
            await this.renderFilesColumn()
        ]);

        container.appendChild(view);
    }

    /**
     * Charge le projet
     */
    async loadProject() {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/projects/${this.projectId}`
            );
            
            if (response.ok) {
                this.project = await response.json();
                state.set('currentProject', this.project);
            } else {
                this.project = null;
            }
        } catch (error) {
            console.error('Erreur chargement projet:', error);
            this.project = null;
        }
    }

    /**
     * Rend la colonne conversations + workflow (divisée en 2)
     * @returns {HTMLElement}
     */
    async renderConversationsAndWorkflowColumn() {
        const column = createElement('div', { 
            className: 'column',
            style: 'background-color: var(--color-surface); display: flex; flex-direction: column;'
        });

        // === PARTIE CONVERSATIONS (50% hauteur) ===
        const conversationsSection = createElement('div', {
            className: 'conversations-section',
            style: 'flex: 1; display: flex; flex-direction: column; border-bottom: 1px solid var(--color-border); overflow: hidden;'
        });

        // Header projet
        const header = createElement('div', {
            className: 'column-header',
            style: 'background-color: var(--color-bg); padding: 0.75rem; border-bottom: 1px solid var(--color-border); flex-shrink: 0;'
        }, [
            createElement('h2', { 
                style: 'font-size: 1rem; font-weight: 600; margin-bottom: 0.25rem;'
            }, this.project.name),
            createElement('p', {
                style: 'font-size: 0.7rem; color: var(--color-text-muted); word-break: break-all; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
            }, this.project.path)
        ]);

        conversationsSection.appendChild(header);

        // Liste conversations
        this.conversationList = new ConversationList({
            projectId: this.projectId,
            onConversationSelect: (conversation) => {
                this.handleConversationSelect(conversation);
            },
            onConversationDelete: (conversationId) => {
                if (this.currentConversationId === conversationId) {
                    this.currentConversationId = null;
                    this.renderChatArea();
                }
            },
            onNewConversation: async () => {
                await this.createNewConversation();
            }
        });

        const listElement = await this.conversationList.render();
        conversationsSection.appendChild(listElement);

        column.appendChild(conversationsSection);

        // === PARTIE WORKFLOW (50% hauteur) ===
        const workflowSection = this.renderWorkflowSection();
        column.appendChild(workflowSection);

        return column;
    }

    /**
     * Rend la colonne chat
     * @returns {HTMLElement}
     */
    renderChatColumn() {
        const column = createElement('div', { 
            className: 'column',
            style: 'display: flex; flex-direction: column;'
        });

        // Header chat
        const header = createElement('div', {
            className: 'column-header'
        }, [
            createElement('h3', { 
                style: 'font-size: 1rem; font-weight: 600;'
            }, '💬 Chat')
        ]);

        column.appendChild(header);

        // Zone chat
        const chatArea = createElement('div', {
            className: 'chat-area',
            style: 'flex: 1; overflow: hidden; display: flex; flex-direction: column;'
        });

        column.appendChild(chatArea);

        // Afficher état initial
        this.renderChatArea(chatArea);

        return column;
    }

    /**
     * Rend la zone de chat
     * @param {HTMLElement} chatArea
     */
    renderChatArea(chatArea = null) {
        if (!chatArea) {
            chatArea = this.container.querySelector('.chat-area');
        }

        clearContainer(chatArea);

        if (!this.currentConversationId) {
            chatArea.appendChild(this.renderEmptyChat());
        } else {
            this.chat = new Chat({
                conversationId: this.currentConversationId,
                mode: 'project',
                projectId: this.projectId
            });
            chatArea.appendChild(this.chat.render());
        }
    }

    /**
     * Rend l'état vide du chat
     * @returns {HTMLElement}
     */
    renderEmptyChat() {
        return createElement('div', { className: 'empty-state' }, [
            createElement('div', { className: 'empty-state-icon' }, '💬'),
            createElement('h3', { className: 'empty-state-title' }, 'Aucune conversation sélectionnée'),
            createElement('p', { className: 'empty-state-description' }, 
                'Créez ou sélectionnez une conversation pour commencer à discuter avec l\'IA.'
            )
        ]);
    }

    /**
     * Rend la section workflow (sous conversations)
     * @returns {HTMLElement}
     */
    renderWorkflowSection() {
        const section = createElement('div', { 
            className: 'workflow-section',
            style: 'flex: 1; display: flex; flex-direction: column; overflow: hidden;'
        });

        // Header workflow
        const header = createElement('div', {
            className: 'column-header',
            style: 'background-color: var(--color-bg); padding: 0.75rem; border-bottom: 1px solid var(--color-border); flex-shrink: 0;'
        }, [
            createElement('h3', { 
                style: 'font-size: 0.9rem; font-weight: 600; margin: 0;'
            }, '⚙️ Workflow')
        ]);

        section.appendChild(header);

        // Zone workflow
        const workflowArea = createElement('div', {
            className: 'workflow-area',
            id: 'workflow-area',
            style: 'flex: 1; overflow-y: auto; padding: 0.75rem;'
        });

        // État initial
        workflowArea.appendChild(this.renderEmptyWorkflow());

        section.appendChild(workflowArea);

        return section;
    }

    /**
     * Rend l'état vide du workflow
     * @returns {HTMLElement}
     */
    renderEmptyWorkflow() {
        return createElement('div', { 
            className: 'empty-state',
            style: 'display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; padding: 1rem;'
        }, [
            createElement('div', { 
                className: 'empty-state-icon',
                style: 'font-size: 2rem; margin-bottom: 0.5rem;'
            }, '⚙️'),
            createElement('h3', { 
                className: 'empty-state-title',
                style: 'font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--color-text);'
            }, 'Aucun workflow actif'),
            createElement('p', { 
                className: 'empty-state-description',
                style: 'font-size: 0.75rem; color: var(--color-text-muted); line-height: 1.4;'
            }, 'Le workflow apparaîtra ici quand JARVIS_Maître délèguera une tâche.')
        ]);
    }

    /**
     * Rend la colonne fichiers
     * @returns {HTMLElement}
     */
    async renderFilesColumn() {
        const column = createElement('div', { 
            className: 'column',
            style: 'background-color: var(--color-surface);'
        });

        this.fileExplorer = new FileExplorer({
            projectId: this.projectId,
            onFileSelect: (file) => {
                this.handleFileSelect(file);
            }
        });

        const explorerElement = await this.fileExplorer.render();
        column.appendChild(explorerElement);

        return column;
    }

    /**
     * Gère la sélection d'une conversation
     * @param {Object} conversation
     */
    handleConversationSelect(conversation) {
        this.currentConversationId = conversation.id;
        state.set('currentConversation', conversation);
        this.renderChatArea();
        
        // Écouter les délégations depuis le chat
        this.listenForDelegations();
    }

    /**
     * Écoute les délégations depuis le chat
     */
    listenForDelegations() {
        // Arrêter le polling précédent s'il existe
        if (this.missionPollingInterval) {
            clearInterval(this.missionPollingInterval);
            this.missionPollingInterval = null;
        }
        
        // Polling pour détecter les missions actives
        const checkMissions = async () => {
            // Ne vérifier que si une conversation est active
            if (!this.currentConversationId) {
                return;
            }
            
            try {
                // Filtrer par project_path au lieu de status
                const projectPath = encodeURIComponent(this.project.path);
                const response = await fetch(`${API_BASE_URL}/api/missions?project_path=${projectPath}`);
                
                if (response.ok) {
                    const missions = await response.json();
                    console.log(`[POLLING] ${missions.length} mission(s) trouvée(s) pour ${this.project.path}`);
                    
                    if (missions.length > 0) {
                        // Prendre la mission la plus récente
                        const latestMission = missions[0];
                        console.log(`[POLLING] Mission la plus récente: ${latestMission.mission_id} (status: ${latestMission.status})`);
                        
                        // Afficher le workflow si nouvelle mission ou changement de statut
                        if (latestMission.mission_id !== this.currentMissionId) {
                            console.log(`[POLLING] Nouvelle mission détectée, affichage du workflow`);
                            this.currentMissionId = latestMission.mission_id;
                            this.displayWorkflow(latestMission.mission_id);
                        }
                    }
                } else {
                    console.error(`[POLLING] Erreur API: ${response.status}`);
                }
            } catch (error) {
                console.error('[POLLING] Erreur check missions:', error);
                // Afficher l'erreur dans le workflow monitor si disponible
                if (window.workflowMonitor) {
                    window.workflowMonitor.addLog('❌', 'ERROR', `Erreur polling missions: ${error.message}`);
                }
            }
        };

        // Vérifier toutes les 3 secondes
        this.missionPollingInterval = setInterval(checkMissions, 3000);
        
        // Vérification immédiate
        console.log('[POLLING] Démarrage du polling des missions');
        checkMissions();
    }

    /**
     * Affiche le workflow pour une mission
     * @param {string} missionId
     */
    displayWorkflow(missionId) {
        const workflowArea = this.container.querySelector('#workflow-area');
        if (!workflowArea) return;

        clearContainer(workflowArea);

        // Créer conteneur pour WorkflowMonitor
        const monitorContainer = createElement('div', {
            id: 'workflow-monitor-inline',
            style: 'height: 100%;'
        });

        workflowArea.appendChild(monitorContainer);

        // Initialiser WorkflowMonitor
        this.workflowMonitor = new WorkflowMonitor('workflow-monitor-inline');
        this.workflowMonitor.startMonitoring(missionId);
        
        // Exposer globalement pour les boutons de validation
        window.workflowMonitor = this.workflowMonitor;
    }

    /**
     * Gère la sélection d'un fichier
     * @param {Object} file
     */
    handleFileSelect(file) {
        if (!this.chat || !this.currentConversationId) {
            alert('Veuillez d\'abord sélectionner une conversation.');
            return;
        }

        // Insérer le contenu du fichier dans l'input du chat
        const chatInput = this.container.querySelector('.chat-input');
        if (chatInput) {
            const fileContent = `\`\`\`${file.name}\n${file.content}\n\`\`\``;
            chatInput.value = chatInput.value 
                ? `${chatInput.value}\n\n${fileContent}` 
                : fileContent;
            chatInput.focus();
            
            // Auto-resize
            chatInput.style.height = 'auto';
            chatInput.style.height = chatInput.scrollHeight + 'px';
        }
    }

    /**
     * Crée une nouvelle conversation
     */
    async createNewConversation() {
        try {
            const agentId = state.get('currentAgent');
            
            const response = await fetch(
                `${API_BASE_URL}/api/projects/${this.projectId}/conversations`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        agent_id: agentId,
                        title: `Conversation ${new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`
                    })
                }
            );

            if (response.ok) {
                const conversation = await response.json();
                this.currentConversationId = conversation.id;
                this.conversationList.setSelectedConversation(conversation.id);
                this.renderChatArea();
                
                // Démarrer le polling des missions
                this.listenForDelegations();
            } else {
                alert('Erreur lors de la création de la conversation.');
            }
        } catch (error) {
            console.error('Erreur création conversation:', error);
            alert('Erreur de connexion au serveur.');
        }
    }

    /**
     * Rend une erreur
     * @returns {HTMLElement}
     */
    renderError() {
        return createElement('div', { className: 'view-container' }, [
            createElement('div', { className: 'empty-state' }, [
                createElement('div', { className: 'empty-state-icon' }, '⚠️'),
                createElement('h3', { className: 'empty-state-title' }, 'Projet introuvable'),
                createElement('p', { className: 'empty-state-description' }, 
                    'Le projet demandé n\'existe pas ou a été supprimé.'
                ),
                createElement('button', {
                    style: `
                        padding: 0.75rem 1.5rem;
                        background-color: var(--color-primary);
                        color: white;
                        border: none;
                        border-radius: var(--radius-md);
                        font-weight: 600;
                        cursor: pointer;
                        margin-top: var(--spacing-lg);
                    `,
                    onClick: () => {
                        window.location.hash = '/projects';
                    }
                }, 'Retour aux projets')
            ])
        ]);
    }

    /**
     * Nettoie la vue
     */
    destroy() {
        if (this.chat) {
            this.chat.destroy();
        }
        if (this.container) {
            clearContainer(this.container);
        }
    }
}

// Fonction globale pour valider l'architecture
window.validateArchitecture = async function(missionId) {
    if (!confirm('Valider cette architecture et continuer le workflow ?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/missions/${missionId}/continue`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('Architecture validée:', result);
            
            // Rafraîchir la page pour voir la suite du workflow
            alert('✅ Architecture validée ! Le workflow continue...');
            location.reload();
        } else {
            const error = await response.json();
            alert(`❌ Erreur : ${error.detail}`);
        }
    } catch (error) {
        console.error('Erreur validation architecture:', error);
        alert(`❌ Erreur réseau : ${error.message}`);
    }
};

export default ProjectDetailView;
