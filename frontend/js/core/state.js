/**
 * State Management - JARVIS 2.0
 * Gestion simple de l'état global de l'application
 */

class State {
    constructor() {
        this.data = {
            currentAgent: 'JARVIS_MAITRE',
            currentConversation: null,
            agents: []
        };
    }

    get(key) {
        return this.data[key];
    }

    set(key, value) {
        this.data[key] = value;
    }

    clear() {
        this.data = {
            currentAgent: 'JARVIS_MAITRE',
            currentConversation: null,
            agents: []
        };
    }
}

// Instance globale
const state = new State();

export default state;
