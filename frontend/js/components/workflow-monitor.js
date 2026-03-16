/**
 * WorkflowMonitor - Composant d'affichage du workflow 5 agents en temps réel
 * 
 * Affiche :
 * - État de la mission (PENDING, IN_PROGRESS, COMPLETED, FAILED)
 * - Phase actuelle (ARCHITECTURE, GENERATION_CODE, TESTS, VALIDATION)
 * - Progression des agents (CODEUR, TESTEUR, VALIDATEUR)
 * - Fichiers créés/modifiés
 * - Erreurs éventuelles
 */

import { API_BASE_URL } from '../config.js';

export class WorkflowMonitor {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.missionId = null;
        this.pollInterval = null;
        this.pollDelay = 2000; // 2 secondes
        this.logs = []; // Historique des logs
        this.maxLogs = 100; // Nombre max de logs à conserver
    }

    /**
     * Démarre le monitoring d'une mission
     */
    async startMonitoring(missionId) {
        this.missionId = missionId;
        this.logs = []; // Reset logs
        
        // Afficher le conteneur
        this.container.style.display = 'block';
        
        // Afficher interface logs
        this.renderLogsInterface();
        
        // Ajouter log initial
        this.addLog('🚀', 'WORKFLOW', `Démarrage monitoring mission ${missionId}`);
        
        // Premier fetch immédiat
        await this.fetchMissionStatus();
        
        // Polling régulier
        this.pollInterval = setInterval(() => {
            this.fetchMissionStatus();
        }, this.pollDelay);
    }

    /**
     * Arrête le monitoring
     */
    stopMonitoring() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    /**
     * Récupère l'état de la mission depuis l'API
     */
    async fetchMissionStatus() {
        if (!this.missionId) return;

        try {
            const response = await fetch(`${API_BASE_URL}/api/missions/${this.missionId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const mission = await response.json();
            this.updateLogsFromMission(mission);

            // Arrêter le polling si mission terminée ou échouée
            if (mission.status === 'COMPLETED' || mission.status === 'FAILED') {
                if (mission.status === 'COMPLETED') {
                    this.addLog('✅', 'WORKFLOW', 'Mission complétée avec succès');
                } else {
                    this.addLog('❌', 'WORKFLOW', `Mission échouée: ${mission.last_error || 'Erreur inconnue'}`);
                }
                this.stopMonitoring();
            }

        } catch (error) {
            console.error('Erreur fetch mission status:', error);
            this.addLog('❌', 'ERROR', `Erreur récupération statut: ${error.message}`);
        }
    }

    /**
     * Ajoute un log à l'historique
     */
    addLog(emoji, category, message) {
        const timestamp = new Date().toLocaleTimeString('fr-FR');
        const log = { emoji, category, message, timestamp };
        
        this.logs.push(log);
        
        // Limiter le nombre de logs
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }
        
        // Mettre à jour l'affichage
        this.updateLogsDisplay();
    }

    /**
     * Met à jour les logs depuis l'état de la mission
     */
    updateLogsFromMission(mission) {
        const lastPhase = this.lastPhase;
        const lastStatus = this.lastStatus;
        
        // Détecter changement de phase
        if (mission.current_phase !== lastPhase) {
            const phaseEmojis = {
                'ARCHITECTURE': '📐',
                'VALIDATION_ARCHI': '🔍',
                'GENERATION_CODE': '💻',
                'GENERATION_TESTS': '🧪',
                'VALIDATION_CODE': '✅'
            };
            
            const phaseLabels = {
                'ARCHITECTURE': 'Appel ARCHITECTE',
                'VALIDATION_ARCHI': 'Validation architecture',
                'GENERATION_CODE': 'Appel CODEUR',
                'GENERATION_TESTS': 'Appel TESTEUR',
                'VALIDATION_CODE': 'Appel VALIDATEUR'
            };
            
            const emoji = phaseEmojis[mission.current_phase] || '📋';
            const label = phaseLabels[mission.current_phase] || mission.current_phase;
            
            this.addLog(emoji, 'PHASE', label);
        }
        
        // Détecter changement de statut
        if (mission.status !== lastStatus) {
            if (mission.status === 'VALIDATING') {
                this.addLog('⏸️', 'WORKFLOW', 'Mission en attente validation architecture');
                // Afficher l'interface de validation
                this.showValidationInterface(mission);
            } else if (mission.status === 'IN_PROGRESS') {
                this.addLog('⚙️', 'WORKFLOW', 'Mission en cours');
            }
        }
        
        // Détecter fichiers créés
        if (mission.files_created && mission.files_created.length > 0) {
            const newFiles = mission.files_created.filter(f => 
                !this.lastFilesCreated || !this.lastFilesCreated.includes(f)
            );
            
            newFiles.forEach(file => {
                this.addLog('✅', 'FILE', `Fichier créé: ${file}`);
            });
            
            this.lastFilesCreated = [...mission.files_created];
        }
        
        // Détecter validations
        if (mission.architecture_validated && !this.lastArchitectureValidated) {
            this.addLog('✅', 'VALIDATION', 'Architecture validée');
        }
        if (mission.code_validated && !this.lastCodeValidated) {
            this.addLog('✅', 'VALIDATION', 'Code validé');
        }
        if (mission.tests_validated && !this.lastTestsValidated) {
            this.addLog('✅', 'VALIDATION', 'Tests validés');
        }
        
        // Sauvegarder état actuel
        this.lastPhase = mission.current_phase;
        this.lastStatus = mission.status;
        this.lastArchitectureValidated = mission.architecture_validated;
        this.lastCodeValidated = mission.code_validated;
        this.lastTestsValidated = mission.tests_validated;
    }

    /**
     * Affiche l'interface des logs
     */
    renderLogsInterface() {
        this.container.innerHTML = `
            <div class="workflow-monitor-logs">
                <div class="workflow-logs-header">
                    <h3>📋 Workflow Logs</h3>
                    <button class="btn-clear-logs" onclick="window.workflowMonitor?.clearLogs()">🗑️ Effacer</button>
                </div>
                <div class="workflow-logs-body" id="workflow-logs-container">
                    <div class="logs-empty">En attente d'événements...</div>
                </div>
            </div>
        `;
    }

    /**
     * Met à jour l'affichage des logs
     */
    updateLogsDisplay() {
        const logsContainer = document.getElementById('workflow-logs-container');
        if (!logsContainer) return;
        
        if (this.logs.length === 0) {
            logsContainer.innerHTML = '<div class="logs-empty">En attente d\'événements...</div>';
            return;
        }
        
        const logsHtml = this.logs.map(log => `
            <div class="log-entry log-${log.category.toLowerCase()}">
                <span class="log-emoji">${log.emoji}</span>
                <span class="log-category">[${log.category}]</span>
                <span class="log-message">${this.escapeHtml(log.message)}</span>
                <span class="log-timestamp">${log.timestamp}</span>
            </div>
        `).join('');
        
        logsContainer.innerHTML = logsHtml;
        
        // Auto-scroll vers le bas
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    /**
     * Efface les logs
     */
    clearLogs() {
        this.logs = [];
        this.updateLogsDisplay();
        this.addLog('🗑️', 'SYSTEM', 'Logs effacés');
    }

    /**
     * Affiche l'interface de validation architecture
     */
    showValidationInterface(mission) {
        const logsContainer = document.getElementById('workflow-logs-container');
        if (!logsContainer) return;
        
        // Extraire l'architecture depuis pending_validation
        const architecture = mission.pending_validation?.data?.architecture || 'Architecture non disponible';
        
        // Créer l'interface de validation
        const validationHtml = `
            <div class="validation-interface">
                <div class="validation-header">
                    <h4>🔍 Validation Architecture Requise</h4>
                </div>
                <div class="validation-content">
                    <div class="architecture-preview">
                        <pre>${this.escapeHtml(architecture.substring(0, 500))}${architecture.length > 500 ? '...' : ''}</pre>
                    </div>
                    <div class="validation-actions">
                        <button class="btn-validate" onclick="window.workflowMonitor?.validateArchitecture('${mission.mission_id}', true)">
                            ✅ Valider
                        </button>
                        <button class="btn-reject" onclick="window.workflowMonitor?.validateArchitecture('${mission.mission_id}', false)">
                            ❌ Rejeter
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Insérer l'interface avant les logs
        logsContainer.insertAdjacentHTML('afterbegin', validationHtml);
    }

    /**
     * Valide ou rejette l'architecture
     */
    async validateArchitecture(missionId, approved) {
        try {
            this.addLog('⚙️', 'WORKFLOW', `${approved ? 'Validation' : 'Rejet'} architecture en cours...`);
            
            // Appeler l'API de validation
            const response = await fetch(`${API_BASE_URL}/api/missions/${missionId}/validate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ approved })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            this.addLog('✅', 'WORKFLOW', `Architecture ${approved ? 'validée' : 'rejetée'}`);
            
            // Si validée, continuer le workflow
            if (approved) {
                this.addLog('🚀', 'WORKFLOW', 'Continuation du workflow...');
                
                const continueResponse = await fetch(`${API_BASE_URL}/api/missions/${missionId}/continue`, {
                    method: 'POST'
                });
                
                if (!continueResponse.ok) {
                    throw new Error(`HTTP ${continueResponse.status}`);
                }
                
                this.addLog('✅', 'WORKFLOW', 'Workflow relancé (CODEUR → TESTEUR → VALIDATEUR)');
            }
            
            // Supprimer l'interface de validation
            const validationInterface = document.querySelector('.validation-interface');
            if (validationInterface) {
                validationInterface.remove();
            }
            
        } catch (error) {
            this.addLog('❌', 'ERROR', `Erreur validation: ${error.message}`);
        }
    }

    /**
     * Affiche l'état de la mission (ancien render, gardé pour compatibilité)
     */
    render(mission) {
        // Cas spécial : validation architecture
        if (mission.status === 'VALIDATING' && mission.current_phase === 'VALIDATION_ARCHI') {
            this.renderValidationArchitecture(mission);
            return;
        }
        
        const statusEmoji = {
            'PENDING': '⏳',
            'IN_PROGRESS': '⚙️',
            'VALIDATING': '🔍',
            'COMPLETED': '✅',
            'FAILED': '❌'
        };

        const phaseLabel = {
            'ARCHITECTURE': 'Architecture',
            'VALIDATION_ARCHI': 'Validation Architecture',
            'GENERATION_CODE': 'Génération Code',
            'TESTS': 'Tests',
            'VALIDATION': 'Validation'
        };

        const statusClass = mission.status.toLowerCase();
        const emoji = statusEmoji[mission.status] || '📋';
        const phase = phaseLabel[mission.current_phase] || mission.current_phase;

        this.container.innerHTML = `
            <div class="workflow-monitor-inline">
                <div class="workflow-body">
                    <div class="mission-info">
                        <div class="info-row">
                            <span class="label">Mission ID:</span>
                            <code>${mission.mission_id}</code>
                        </div>
                        <div class="info-row">
                            <span class="label">Statut:</span>
                            <span class="status-badge status-${statusClass}">${mission.status}</span>
                        </div>
                        ${mission.current_phase ? `
                        <div class="info-row">
                            <span class="label">Phase:</span>
                            <span class="phase-badge">${phase}</span>
                        </div>
                        ` : ''}
                    </div>

                    ${this.renderProgress(mission)}

                    ${mission.files_created && mission.files_created.length > 0 ? `
                    <div class="files-section">
                        <h4>📁 Fichiers créés (${mission.files_created.length})</h4>
                        <ul class="files-list">
                            ${mission.files_created.map(f => `<li><code>${f}</code></li>`).join('')}
                        </ul>
                    </div>
                    ` : ''}

                    ${mission.files_modified && mission.files_modified.length > 0 ? `
                    <div class="files-section">
                        <h4>📝 Fichiers modifiés (${mission.files_modified.length})</h4>
                        <ul class="files-list">
                            ${mission.files_modified.map(f => `<li><code>${f}</code></li>`).join('')}
                        </ul>
                    </div>
                    ` : ''}

                    ${mission.last_error ? `
                    <div class="error-section">
                        <h4>❌ Erreur</h4>
                        <pre>${mission.last_error}</pre>
                    </div>
                    ` : ''}

                    ${mission.status === 'COMPLETED' ? `
                    <div class="success-message">
                        ✅ Mission complétée avec succès !
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Affiche la progression du workflow
     */
    renderProgress(mission) {
        const steps = [
            { key: 'architecture_validated', label: 'Architecture', icon: '📐' },
            { key: 'code_validated', label: 'Code', icon: '💻' },
            { key: 'tests_validated', label: 'Tests', icon: '🧪' }
        ];

        const stepsHtml = steps.map(step => {
            const isCompleted = mission[step.key];
            const isCurrent = !isCompleted && (
                (step.key === 'architecture_validated' && mission.current_phase === 'ARCHITECTURE') ||
                (step.key === 'code_validated' && mission.current_phase === 'GENERATION_CODE') ||
                (step.key === 'tests_validated' && mission.current_phase === 'TESTS')
            );

            const statusClass = isCompleted ? 'completed' : (isCurrent ? 'current' : 'pending');

            return `
                <div class="progress-step ${statusClass}">
                    <div class="step-icon">${step.icon}</div>
                    <div class="step-label">${step.label}</div>
                    <div class="step-status">
                        ${isCompleted ? '✅' : (isCurrent ? '⚙️' : '⏳')}
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="workflow-progress">
                <h4>Progression</h4>
                <div class="progress-steps">
                    ${stepsHtml}
                </div>
            </div>
        `;
    }

    /**
     * Affiche la validation d'architecture
     */
    renderValidationArchitecture(mission) {
        const architecture = mission.pending_validation?.data?.architecture || 'Architecture non disponible';
        
        this.container.innerHTML = `
            <div class="workflow-monitor">
                <div class="workflow-header">
                    <h3>🏗️ Validation Architecture</h3>
                </div>
                <div class="workflow-body">
                    <div class="validation-section">
                        <p style="margin-bottom: 1rem; font-weight: 500;">L'ARCHITECTE a proposé l'architecture suivante :</p>
                        <div class="architecture-content" style="background: var(--color-bg); padding: 1rem; border-radius: 4px; margin-bottom: 1rem; max-height: 400px; overflow-y: auto;">
                            <pre style="white-space: pre-wrap; word-wrap: break-word; margin: 0; font-size: 0.85rem;">${this.escapeHtml(architecture)}</pre>
                        </div>
                        <div class="validation-actions" style="display: flex; gap: 0.5rem;">
                            <button class="btn-primary" onclick="window.validateArchitecture('${mission.mission_id}')" style="flex: 1; padding: 0.75rem; background: var(--color-primary); color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 500;">
                                ✅ Valider l'architecture
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Échappe le HTML pour éviter les injections
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Affiche une erreur
     */
    renderError(message) {
        this.container.innerHTML = `
            <div class="workflow-monitor">
                <div class="workflow-header">
                    <h3>❌ Erreur</h3>
                    <button class="btn-close" onclick="document.getElementById('${this.container.id}').style.display='none'">×</button>
                </div>
                <div class="workflow-body">
                    <div class="error-section">
                        <p>${message}</p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Masque le composant
     */
    hide() {
        this.stopMonitoring();
        this.container.style.display = 'none';
    }
}
