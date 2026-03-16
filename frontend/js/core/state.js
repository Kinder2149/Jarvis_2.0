/**
 * State Manager Simple - JARVIS 2.0
 * Gestion état global avec système de souscription
 */

class StateManager {
    constructor() {
        this.state = {
            // Navigation
            currentView: 'home',
            
            // Agents
            agents: [],
            currentAgent: localStorage.getItem('current_agent') || 'JARVIS_Maître',
            
            // Conversations
            conversations: [],
            currentConversation: null,
            
            // Projets
            projects: [],
            currentProject: null,
            
            // UI
            loading: false,
            error: null
        };

        this.subscribers = {};
    }

    /**
     * Récupère une valeur de l'état
     * @param {string} key - Clé de l'état
     * @returns {*}
     */
    get(key) {
        return this.state[key];
    }

    /**
     * Définit une valeur dans l'état
     * @param {string} key - Clé de l'état
     * @param {*} value - Nouvelle valeur
     */
    set(key, value) {
        const oldValue = this.state[key];
        this.state[key] = value;

        // Notifier les souscripteurs
        if (this.subscribers[key]) {
            this.subscribers[key].forEach(callback => {
                callback(value, oldValue);
            });
        }

        // Persister certaines valeurs
        this.persist(key, value);
    }

    /**
     * Souscrit aux changements d'une clé
     * @param {string} key - Clé à surveiller
     * @param {Function} callback - Fonction appelée lors du changement
     * @returns {Function} Fonction de désinscription
     */
    subscribe(key, callback) {
        if (!this.subscribers[key]) {
            this.subscribers[key] = [];
        }
        this.subscribers[key].push(callback);

        // Retourne fonction de désinscription
        return () => {
            this.subscribers[key] = this.subscribers[key].filter(cb => cb !== callback);
        };
    }

    /**
     * Met à jour plusieurs valeurs en une fois
     * @param {Object} updates - Objet clé-valeur
     */
    update(updates) {
        Object.keys(updates).forEach(key => {
            this.set(key, updates[key]);
        });
    }

    /**
     * Réinitialise l'état
     */
    reset() {
        const defaultState = {
            currentView: 'home',
            agents: [],
            currentAgent: 'JARVIS_Maître',
            conversations: [],
            currentConversation: null,
            projects: [],
            currentProject: null,
            loading: false,
            error: null
        };

        Object.keys(defaultState).forEach(key => {
            this.set(key, defaultState[key]);
        });
    }

    /**
     * Persiste certaines valeurs en localStorage
     * @param {string} key - Clé
     * @param {*} value - Valeur
     */
    persist(key, value) {
        const persistKeys = ['currentAgent'];
        
        if (persistKeys.includes(key)) {
            if (value !== null && value !== undefined) {
                localStorage.setItem(key, JSON.stringify(value));
            } else {
                localStorage.removeItem(key);
            }
        }
    }

    /**
     * Récupère l'état complet (pour debug)
     * @returns {Object}
     */
    getState() {
        return { ...this.state };
    }
}

// Instance globale
const state = new StateManager();

export default state;
