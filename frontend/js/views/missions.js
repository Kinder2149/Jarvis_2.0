/**
 * Vue Missions - Gestion workflow 5 agents
 */

import { apiClient } from '../api-client.js';
import { formatDate } from '../utils/format.js';

export class MissionsView {
    constructor() {
        this.missions = [];
        this.currentMission = null;
    }

    async render() {
        const container = document.createElement('div');
        container.className = 'missions-view';
        container.innerHTML = `
            <div class="missions-header">
                <h1>🚀 Missions JARVIS 2.0</h1>
                <button class="btn btn-primary" id="new-mission-btn">
                    <span class="icon">➕</span>
                    Nouvelle Mission
                </button>
            </div>

            <div class="missions-content">
                <div class="missions-list" id="missions-list">
                    <div class="loading">Chargement missions...</div>
                </div>

                <div class="mission-detail" id="mission-detail">
                    <div class="empty-state">
                        <p>Sélectionnez une mission ou créez-en une nouvelle</p>
                    </div>
                </div>
            </div>

            <!-- Modal Nouvelle Mission -->
            <div class="modal" id="new-mission-modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Nouvelle Mission</h2>
                        <button class="modal-close" id="close-modal-btn">×</button>
                    </div>
                    <div class="modal-body">
                        <form id="new-mission-form">
                            <div class="form-group">
                                <label for="project-name">Nom du projet</label>
                                <input type="text" id="project-name" required 
                                       placeholder="ex: calculatrice-python">
                            </div>

                            <div class="form-group">
                                <label for="project-path">Chemin projet</label>
                                <input type="text" id="project-path" required 
                                       placeholder="ex: d:/Projets/calculatrice">
                            </div>

                            <div class="form-group">
                                <label for="user-request">Demande</label>
                                <textarea id="user-request" rows="6" required
                                          placeholder="Décrivez votre projet en détail..."></textarea>
                            </div>

                            <div class="form-actions">
                                <button type="button" class="btn btn-secondary" id="cancel-btn">
                                    Annuler
                                </button>
                                <button type="submit" class="btn btn-primary">
                                    Démarrer Mission
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;

        // Event listeners
        this.attachEventListeners(container);

        // Charger missions
        await this.loadMissions();
        this.renderMissionsList(container);

        return container;
    }

    attachEventListeners(container) {
        // Bouton nouvelle mission
        container.querySelector('#new-mission-btn').addEventListener('click', () => {
            this.showNewMissionModal(container);
        });

        // Fermer modal
        container.querySelector('#close-modal-btn').addEventListener('click', () => {
            this.hideNewMissionModal(container);
        });

        container.querySelector('#cancel-btn').addEventListener('click', () => {
            this.hideNewMissionModal(container);
        });

        // Soumettre nouvelle mission
        container.querySelector('#new-mission-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.startNewMission(container);
        });
    }

    showNewMissionModal(container) {
        container.querySelector('#new-mission-modal').style.display = 'flex';
    }

    hideNewMissionModal(container) {
        container.querySelector('#new-mission-modal').style.display = 'none';
        container.querySelector('#new-mission-form').reset();
    }

    async startNewMission(container) {
        const projectName = container.querySelector('#project-name').value;
        const projectPath = container.querySelector('#project-path').value;
        const userRequest = container.querySelector('#user-request').value;

        try {
            const response = await fetch('/api/missions/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_name: projectName,
                    project_path: projectPath,
                    user_request: userRequest
                })
            });

            const result = await response.json();

            if (result.success) {
                this.hideNewMissionModal(container);
                await this.loadMissions();
                this.renderMissionsList(container);

                // Afficher détail mission
                if (result.mission_id) {
                    await this.showMissionDetail(container, result.mission_id);
                }
            } else {
                alert('Erreur: ' + (result.error || result.message));
            }
        } catch (error) {
            console.error('Erreur start mission:', error);
            alert('Erreur lors du démarrage de la mission');
        }
    }

    async loadMissions() {
        try {
            const response = await fetch('/api/missions');
            this.missions = await response.json();
        } catch (error) {
            console.error('Erreur chargement missions:', error);
            this.missions = [];
        }
    }

    renderMissionsList(container) {
        const listContainer = container.querySelector('#missions-list');
        
        if (this.missions.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <p>Aucune mission</p>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = this.missions.map(mission => `
            <div class="mission-item ${mission.status}" data-mission-id="${mission.mission_id}">
                <div class="mission-item-header">
                    <span class="mission-status ${mission.status}">${this.getStatusLabel(mission.status)}</span>
                    <span class="mission-date">${formatDate(mission.created_at)}</span>
                </div>
                <div class="mission-item-body">
                    <h3>${mission.user_request.substring(0, 60)}...</h3>
                    <p class="mission-path">${mission.project_path}</p>
                </div>
            </div>
        `).join('');

        // Event listeners sur items
        listContainer.querySelectorAll('.mission-item').forEach(item => {
            item.addEventListener('click', async () => {
                const missionId = item.dataset.missionId;
                await this.showMissionDetail(container, missionId);
            });
        });
    }

    async showMissionDetail(container, missionId) {
        try {
            const response = await fetch(`/api/missions/${missionId}`);
            const mission = await response.json();

            const detailContainer = container.querySelector('#mission-detail');
            
            // Si mission en attente validation architecture
            if (mission.status === 'validating' && mission.current_phase === 'validation_architecture') {
                detailContainer.innerHTML = this.renderArchitectureValidation(mission);
                this.attachValidationListeners(detailContainer, mission);
            } else {
                detailContainer.innerHTML = this.renderMissionStatus(mission);
            }
        } catch (error) {
            console.error('Erreur chargement mission:', error);
        }
    }

    renderArchitectureValidation(mission) {
        const architecture = mission.pending_validation?.data?.architecture || 'Architecture non disponible';

        return `
            <div class="architecture-validation">
                <div class="validation-header">
                    <h2>🏗️ Validation Architecture</h2>
                    <span class="badge badge-warning">En attente validation</span>
                </div>

                <div class="architecture-content">
                    <h3>Architecture proposée par ARCHITECTE</h3>
                    <div class="architecture-doc">
                        <pre>${architecture}</pre>
                    </div>
                </div>

                <div class="validation-actions">
                    <button class="btn btn-danger" id="reject-architecture-btn">
                        ❌ Rejeter
                    </button>
                    <button class="btn btn-success" id="approve-architecture-btn">
                        ✅ Valider et Continuer
                    </button>
                </div>

                <div class="validation-info">
                    <p><strong>Mission ID:</strong> ${mission.mission_id}</p>
                    <p><strong>Projet:</strong> ${mission.project_path}</p>
                    <p><strong>Demande:</strong> ${mission.user_request}</p>
                </div>
            </div>
        `;
    }

    renderMissionStatus(mission) {
        return `
            <div class="mission-status">
                <div class="status-header">
                    <h2>${mission.user_request}</h2>
                    <span class="badge badge-${mission.status}">${this.getStatusLabel(mission.status)}</span>
                </div>

                <div class="status-info">
                    <div class="info-row">
                        <span class="label">Mission ID:</span>
                        <span class="value">${mission.mission_id}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Projet:</span>
                        <span class="value">${mission.project_path}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Phase:</span>
                        <span class="value">${mission.current_phase || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Créée:</span>
                        <span class="value">${formatDate(mission.created_at)}</span>
                    </div>
                    ${mission.completed_at ? `
                        <div class="info-row">
                            <span class="label">Complétée:</span>
                            <span class="value">${formatDate(mission.completed_at)}</span>
                        </div>
                    ` : ''}
                </div>

                <div class="status-progress">
                    <h3>Progression</h3>
                    <div class="progress-items">
                        <div class="progress-item ${mission.architecture_validated ? 'completed' : ''}">
                            ${mission.architecture_validated ? '✅' : '⏳'} Architecture
                        </div>
                        <div class="progress-item ${mission.code_validated ? 'completed' : ''}">
                            ${mission.code_validated ? '✅' : '⏳'} Code
                        </div>
                        <div class="progress-item ${mission.tests_validated ? 'completed' : ''}">
                            ${mission.tests_validated ? '✅' : '⏳'} Tests
                        </div>
                    </div>
                </div>

                ${mission.files_created.length > 0 ? `
                    <div class="status-files">
                        <h3>Fichiers créés (${mission.files_created.length})</h3>
                        <ul>
                            ${mission.files_created.map(file => `<li>${file}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${mission.last_error ? `
                    <div class="status-error">
                        <h3>Erreur</h3>
                        <p>${mission.last_error}</p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    attachValidationListeners(container, mission) {
        const approveBtn = container.querySelector('#approve-architecture-btn');
        const rejectBtn = container.querySelector('#reject-architecture-btn');

        if (approveBtn) {
            approveBtn.addEventListener('click', async () => {
                await this.validateArchitecture(mission.mission_id, true);
            });
        }

        if (rejectBtn) {
            rejectBtn.addEventListener('click', async () => {
                await this.validateArchitecture(mission.mission_id, false);
            });
        }
    }

    async validateArchitecture(missionId, approved) {
        try {
            // Valider architecture
            const validateResponse = await fetch(`/api/missions/${missionId}/validate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ approved })
            });

            const validateResult = await validateResponse.json();

            if (!validateResult.success) {
                alert('Erreur validation: ' + validateResult.message);
                return;
            }

            if (approved) {
                // Continuer mission
                alert('Architecture validée. Lancement du workflow...');
                
                const continueResponse = await fetch(`/api/missions/${missionId}/continue`, {
                    method: 'POST'
                });

                const continueResult = await continueResponse.json();

                if (continueResult.success) {
                    alert(`Mission complétée ! ${continueResult.files_created.length} fichiers créés.`);
                } else {
                    alert('Erreur: ' + continueResult.error);
                }
            } else {
                alert('Architecture rejetée. ARCHITECTE va proposer une nouvelle version.');
            }

            // Recharger missions
            await this.loadMissions();
            const container = document.querySelector('.missions-view');
            if (container) {
                this.renderMissionsList(container);
                await this.showMissionDetail(container, missionId);
            }

        } catch (error) {
            console.error('Erreur validation:', error);
            alert('Erreur lors de la validation');
        }
    }

    getStatusLabel(status) {
        const labels = {
            'pending': 'En attente',
            'in_progress': 'En cours',
            'validating': 'Validation requise',
            'completed': 'Complétée',
            'failed': 'Échouée',
            'cancelled': 'Annulée'
        };
        return labels[status] || status;
    }
}

export default MissionsView;
