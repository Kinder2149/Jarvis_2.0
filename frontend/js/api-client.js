import { API_BASE_URL } from './config.js';

class APIClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    async createProject(projectData) {
        return this.request('/api/projects', {
            method: 'POST',
            body: JSON.stringify(projectData)
        });
    }
    
    async listProjects() {
        return this.request('/api/projects');
    }
    
    async getProject(projectId) {
        return this.request(`/api/projects/${projectId}`);
    }
    
    async updateProject(projectId, updateData) {
        return this.request(`/api/projects/${projectId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }
    
    async deleteProject(projectId) {
        return this.request(`/api/projects/${projectId}`, {
            method: 'DELETE'
        });
    }
    
    async createConversation(projectId, conversationData) {
        return this.request(`/api/projects/${projectId}/conversations`, {
            method: 'POST',
            body: JSON.stringify(conversationData)
        });
    }
    
    async listConversations(projectId) {
        return this.request(`/api/projects/${projectId}/conversations`);
    }
    
    async getConversation(conversationId) {
        return this.request(`/api/conversations/${conversationId}`);
    }
    
    async deleteConversation(conversationId) {
        return this.request(`/api/conversations/${conversationId}`, {
            method: 'DELETE'
        });
    }
    
    async getMessages(conversationId, limit = 100) {
        return this.request(`/api/conversations/${conversationId}/messages?limit=${limit}`);
    }
    
    async sendMessage(conversationId, content) {
        return this.request(`/api/conversations/${conversationId}/messages`, {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }
    
    async getFileTree(projectId, maxDepth = 3) {
        return this.request(`/api/projects/${projectId}/files/tree?max_depth=${maxDepth}`);
    }
    
    async listFiles(projectId, path = '') {
        return this.request(`/api/projects/${projectId}/files/list?path=${encodeURIComponent(path)}`);
    }
    
    async readFile(projectId, path) {
        return this.request(`/api/projects/${projectId}/files/read?path=${encodeURIComponent(path)}`);
    }
    
    async searchFiles(projectId, pattern, maxResults = 50) {
        return this.request(`/api/projects/${projectId}/files/search?pattern=${encodeURIComponent(pattern)}&max_results=${maxResults}`);
    }
    
    async listAgents() {
        return this.request('/agents');
    }
    
    async listAgentsDetailed() {
        return this.request('/api/agents/detailed');
    }
}

const api = new APIClient();

// Export pour utilisation dans les modules
export const apiClient = api;
export default api;
