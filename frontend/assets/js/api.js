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
  selectFolder: () => _get('/projects/select-folder'),
  getProjectSessions: (id) => _get(`/projects/${id}/sessions`),
  getActiveSession: (id) => _get(`/projects/${id}/active-session`),
  scanProject: (id) => _get(`/projects/${id}/scan`),
  initGraphify: (id) => _post(`/projects/${id}/init-graphify`, {}),
  parseMissionPrompt: (text) => _post('/pipelines/parse-mission', { text }),
  startPipeline: (data) => {
    // data peut contenir: project_id, workflow_type, initial_input, modele_override, source_mission_prompt_id, attachment_base64, attachment_filename
    return _post('/pipelines/start', data);
  },
  getPipeline: (sessionId) => _get(`/pipelines/${sessionId}`),
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
  getReglesGlobales: () => _get('/config/regles_globales'),
  saveReglesGlobales: (value) => _post('/config/regles_globales', { value }),
  getCouche1: (moduleKey) => _get(`/config/couche1/${moduleKey}`),
  saveCouche1: (moduleKey, value) => _post(`/config/couche1/${moduleKey}`, { value }),
  backupDatabase: () => _post('/config/backup', {}),
  getClientsExportPath: () => _get('/config/clients_export_path'),
  saveClientsExportPath: (value) => _post('/config/clients_export_path', { value }),

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
  visionExtract: (attachment_base64, attachment_filename) => _post('/chat/vision-extract', { attachment_base64, attachment_filename }),

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

  createReflexion: (projectId, livrableType) => _post('/reflexions', { project_id: projectId, livrable_type: livrableType }),
  getReflexions: (projectId) => _get(`/reflexions?project_id=${projectId}`),
  getReflexion: (id) => _get(`/reflexions/${id}`),
  deleteReflexion: (id) => _del(`/reflexions/${id}`),
  abandonReflexion: (id) => _post(`/reflexions/${id}/abandon`, {}),
  sendReflexionMessage: (id, bodyOrContent) => {
    const body = typeof bodyOrContent === 'string' ? { content: bodyOrContent } : bodyOrContent;
    return _post(`/reflexions/${id}/messages`, body);
  },
  getReflexionMessages: (id, includeCompacted = false) => _get(`/reflexions/${id}/messages?include_compacted=${includeCompacted}`),
  checkCadrageHealth: (id) => _post(`/reflexions/${id}/sante-cadrage`, {}),
  proposeEdit: (id, filePath, newContent) => _post(`/reflexions/${id}/proposer-edit`, { file_path: filePath, new_content: newContent }),
  applyEdit: (id, filePath, newContent) => _post(`/reflexions/${id}/appliquer-edit`, { file_path: filePath, new_content: newContent, confirmed: true }),
  detectLivrableType: (sessionId) => _post(`/reflexions/${sessionId}/detect-livrable`, {}),
  figerReflexion: (id, livrableType = null) => _post(`/reflexions/${id}/figer`, livrableType ? { livrable_type: livrableType } : {}),
  getLivrable: (id) => _get(`/reflexions/${id}/livrable`),
  marquerConsomme: (id) => _post(`/reflexions/${id}/marquer-consomme`, {}),

  // Sentinelle
  getPositions: () => _get('/sentinelle/positions'),
  getPositionsValorisation: () => _get('/sentinelle/positions/valorisation'),
  createPosition: (data) => _post('/sentinelle/positions', data),
  upsertPosition: (data) => _post('/sentinelle/positions/upsert', data),
  updatePosition: (id, data) => _request('PUT', `/sentinelle/positions/${id}`, data),
  deletePosition: (id) => _del(`/sentinelle/positions/${id}`),
  getWatchlist: () => _get('/sentinelle/watchlist'),
  createWatchlist: (data) => _post('/sentinelle/watchlist', data),
  deleteWatchlist: (id) => _del(`/sentinelle/watchlist/${id}`),
  getCycles: () => _get('/sentinelle/cycles'),
  getCycleActif: () => _get('/sentinelle/cycles/actif'),
  createCycle: (data) => _post('/sentinelle/cycles', data),
  updateCycleEtat: (id, data) => _patch(`/sentinelle/cycles/${id}/etat`, data),
  updateCycleDecision: (id, data) => _patch(`/sentinelle/cycles/${id}/decision`, data),
  cloturerCycle: (id, data) => _patch(`/sentinelle/cycles/${id}/cloture`, data),
  getTransactions: (cycleId = null) => _get(`/sentinelle/transactions${cycleId ? `?cycle_id=${cycleId}` : ''}`),
  createTransaction: (data) => _post('/sentinelle/transactions', data),
  getBudgetMois: (mois) => _get(`/sentinelle/budget/${mois}`),
  runVeille: (cycleId) => _post(`/sentinelle/cycles/${cycleId}/veille`, {}),
  runAnalyse: (cycleId) => _post(`/sentinelle/cycles/${cycleId}/analyse`, {}),
  runPropositions: (cycleId) => _post(`/sentinelle/cycles/${cycleId}/propositions`, {}),
  runOrdre: (cycleId, data) => _post(`/sentinelle/cycles/${cycleId}/ordre`, data),
  getSentinelleCyclesRecent: () => _get('/sentinelle/cycles/recent'),
  getSentinelleActifCount: () => _get('/sentinelle/cycles/actif/count'),
  getSentinelleAlertesCount: () => _get('/sentinelle/alertes/count'),
  getSentinelleAlertes: () => _get('/sentinelle/alertes'),
  markAlerteLue: (id) => _patch(`/sentinelle/alertes/${id}/lu`),

  // JARVIS multi-agents
  createJarvisConversation: (data) => _post('/jarvis/conversations', data),
  getJarvisConversations: () => _get('/jarvis/conversations'),
  getJarvisConversation: (id) => _get(`/jarvis/conversations/${id}`),
  sendJarvisMessage: (id, content, forceAgent = null) => _post(`/jarvis/conversations/${id}/chat`, { message: content, force_agent: forceAgent }),
  deleteJarvisConversation: (id) => _del(`/jarvis/conversations/${id}`),
  startJarvisForge: (missionPromptId, conversationId) => _post('/jarvis/forge/start', { mission_prompt_id: missionPromptId, conversation_id: conversationId }),
  getJarvisPipelineProgress: (sessionId) => _get(`/jarvis/pipeline/${sessionId}/progress`),
  resetJarvisForge: (projectId) => _post(`/jarvis/project/${projectId}/reset-forge`, {}),
  verifyJarvisForge: (sessionId) => _post(`/jarvis/verify/${sessionId}`),
  getJarvisPipelinesOverview: (activeOnly = false) =>
    _get(`/jarvis/pipelines/overview${activeOnly ? '?active_only=true' : ''}`),
  getMediaStats: () => _get('/media/stats'),
  getMediaHistory: (limit = 20) => _get('/media/history?limit=' + limit),
};
