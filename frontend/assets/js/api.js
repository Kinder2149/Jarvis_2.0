const BASE_URL = window.location.origin;

async function _request(method, path, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE_URL}/api${path}`, opts);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { 
      const d = await res.json(); 
      if (d.detail) msg = d.detail; 
    } catch(e) {}
    throw new Error(msg);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

const _get = (path) => _request('GET', path);
const _post = (path, body) => _request('POST', path, body);
const _patch = (path, body) => _request('PATCH', path, body);
const _del = (path) => _request('DELETE', path);

window.API = {
  // Méthodes génériques
  get: (url) => fetch(BASE_URL + url).then(r => r.json()),
  post: (url, data) => fetch(BASE_URL + url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  }).then(r => r.json()),
  patch: (url, data) => fetch(BASE_URL + url, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  }).then(r => r.json()),

  getProjects: () => _get('/projects/'),
  getProject: (id) => _get(`/projects/${id}`),
  createProject: (data) => _post('/projects/', data),
  updateProject: (id, data) => _patch(`/projects/${id}`, data),
  deleteProject: (id) => _del(`/projects/${id}`),
  getProjectSessions: (id) => _get(`/projects/${id}/sessions`),
  getActiveSession: (id) => _get(`/projects/${id}/active-session`),
  scanProject: (id) => _get(`/projects/${id}/scan`),
  initGraphify: (id) => _post(`/projects/${id}/init-graphify`, {}),
  routeMission: (projectId, mission) => _post(`/projects/${projectId}/route-mission`, { mission }),

  startPipeline: (data) => _post('/pipelines/start', data),
  getPipeline: (sessionId) => _get(`/pipelines/${sessionId}`),
  nextStep: (sessionId) => _post(`/pipelines/${sessionId}/next`),
  validateStep: (sessionId, stepId, data) => _post(`/pipelines/${sessionId}/validate/${stepId}`, data),
  retryStep: (sessionId, stepId) => _post(`/pipelines/${sessionId}/retry/${stepId}`),
  abortPipeline: (sessionId) => _post(`/pipelines/${sessionId}/abort`),
  deletePipeline: (sessionId) => _del(`/pipelines/${sessionId}`),
  getPipelineCosts: (sessionId) => _get(`/pipelines/${sessionId}/costs`),
  getLogs: (params = {}) => _get(`/pipelines/logs?${new URLSearchParams(params)}`),

  getConfig: () => _get('/config'),
  saveConfig: (data) => _post('/config', data),
  testConnection: (data) => _post('/config/test', data),
  getAvailableModels: () => _get('/config/models/available'),
  getGlobalContext: () => _get('/config/global_context'),
  saveGlobalContext: (value) => _post('/config/global_context', { value }),

  listProjectFiles: (projectId) => _get(`/files/${projectId}/list`),
  readFile: (projectId, filepath) => _post(`/files/${projectId}/read`, { filepath }),
  diffFile: (projectId, filepath, new_content) => _post(`/files/${projectId}/diff`, { filepath, new_content }),
  applyFiles: (projectId, changes) => _post(`/files/${projectId}/apply`, { changes }),
  listLocalFiles: (projectId) => _get(`/files/${projectId}/local-list`),

  createConversation: (data) => _post('/chat/conversations', data),
  getConversations: (projectId = null) => _get(`/chat/conversations${projectId ? `?project_id=${projectId}` : ''}`),
  getConversation: (id) => _get(`/chat/conversations/${id}`),
  sendMessage: (conversationId, content, model = null) => {
    const body = { content };
    if (model) body.model = model;
    return _post(`/chat/conversations/${conversationId}/messages`, body);
  },
  updateConversationFolder: (id, folder_path) => _patch(`/chat/conversations/${id}/folder`, { folder_path }),
  updateConvSummary: (convId) => _post(`/chat/conversations/${convId}/update-summary`, {}),
  deleteConversation: (id) => _del(`/chat/conversations/${id}`),

  // Atelier
  getProspects: () => _get('/atelier/prospects'),
  createProspect: (data) => _post('/atelier/prospects', data),
  getProspect: (id) => _get(`/atelier/prospects/${id}`),
  patchProspect: (id, data) => _patch(`/atelier/prospects/${id}`, data),
  deleteProspect: (id) => _del(`/atelier/prospects/${id}`),
  deleteAllProspects: () => _del('/atelier/prospects'),
  startAtelierPipeline: (prospectId) => _post(`/atelier/prospects/${prospectId}/start`, {}),
  listProspectFiles: (prospectId) => _get(`/atelier/prospects/${prospectId}/files`),
  exportProspectZip: (prospectId) => `${BASE_URL}/api/atelier/prospects/${prospectId}/export`,
};
