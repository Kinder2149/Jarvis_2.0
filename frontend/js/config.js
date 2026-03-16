/**
 * Configuration globale - JARVIS 2.0
 * Constantes pour les URLs des APIs
 */

// URL de base pour l'API backend JARVIS
export const API_BASE_URL = 'http://localhost:8000';

// URL de base pour l'API RAG
export const RAG_API_URL = 'http://localhost:5001';

// Configuration par défaut
export const CONFIG = {
    // Polling intervals (en millisecondes)
    WORKFLOW_POLL_INTERVAL: 2000,  // 2 secondes
    MISSION_POLL_INTERVAL: 3000,   // 3 secondes
    
    // Limites
    MAX_LOGS: 100,
    MAX_MESSAGE_LENGTH: 10000,
    
    // Timeouts (en millisecondes)
    API_TIMEOUT: 30000,  // 30 secondes
};
