(function() {
  const projectId = parseInt(new URLSearchParams(location.search).get('id'));
  let currentProject = null;
  let routingResult = null;
  let allSessions = [];
  let showAllSessions = false;

  document.addEventListener('DOMContentLoaded', async () => {
    await init();
    attachEventListeners();
  });

  async function init() {
    try {
      currentProject = await window.API.getProject(projectId);

      document.title = `JARVIS — ${currentProject.name}`;
      document.getElementById('project-name').textContent = currentProject.name;
      document.getElementById('project-path').textContent = currentProject.path;

      const categoryColors = {
        'applications_mobile': '#3b82f6',
        'applications_web': '#10b981',
        'Clients': '#f59e0b',
        'intelligence_artificielle': '#8b5cf6'
      };
      const categoryLabels = {
        'applications_mobile': 'App Mobile',
        'applications_web': 'App Web',
        'Clients': 'Client',
        'intelligence_artificielle': 'IA'
      };
      const categoryColor = categoryColors[currentProject.category] || '#6b7280';
      const categoryLabel = categoryLabels[currentProject.category] || currentProject.category;
      const badge = document.getElementById('project-category-badge');
      badge.textContent = categoryLabel;
      badge.style.backgroundColor = `${categoryColor}20`;
      badge.style.color = categoryColor;
      badge.style.border = `1px solid ${categoryColor}40`;

      // Instructions
      const instructionsEl = document.getElementById('instructions-input');
      instructionsEl.value = currentProject.instructions || '';

      await Promise.all([runScan(), loadSessions(), loadConversations()]);

    } catch (error) {
      console.error('Erreur chargement projet:', error);
      if (window.showToast) window.showToast('Erreur de chargement', 'error');
    }
  }

  function attachEventListeners() {
    // Instructions
    const instructionsEl = document.getElementById('instructions-input');
    const btnSave = document.getElementById('btn-save-instructions');
    instructionsEl.addEventListener('input', () => {
      btnSave.style.display = 'inline-flex';
    });
    btnSave.addEventListener('click', saveInstructions);

    // Scan
    document.getElementById('btn-rescan').addEventListener('click', () => runScan(true));

    // Mission
    document.getElementById('btn-analyze').addEventListener('click', analyzeAndRoute);
    document.getElementById('btn-launch').addEventListener('click', launchMission);
    document.getElementById('btn-back-mission').addEventListener('click', () => {
      document.getElementById('mission-step-b').style.display = 'none';
      document.getElementById('mission-step-a').style.display = 'block';
    });

    // Sessions toggle
    document.getElementById('btn-toggle-sessions').addEventListener('click', () => {
      showAllSessions = !showAllSessions;
      renderSessions();
    });

    // Chats
    document.getElementById('btn-new-chat').addEventListener('click', createNewChat);
  }

  // ── INSTRUCTIONS ────────────────────────────────────────────────

  async function saveInstructions() {
    const value = document.getElementById('instructions-input').value;
    try {
      await window.API.updateProject(projectId, { instructions: value });
      document.getElementById('btn-save-instructions').style.display = 'none';
      if (window.showToast) window.showToast('Instructions sauvegardées', 'success');
    } catch (e) {
      if (window.showToast) window.showToast('Erreur sauvegarde', 'error');
    }
  }

  // ── SCAN ────────────────────────────────────────────────────────

  async function runScan(force = false) {
    const zone = document.getElementById('scan-zone');
    zone.innerHTML = '<div style="color:var(--text-muted);font-size:0.875rem">Scan en cours…</div>';
    try {
      const data = await window.API.scanProject(projectId);
      renderScan(data);
    } catch (e) {
      zone.innerHTML = '<div style="color:#ef4444;font-size:0.875rem">Erreur lors du scan</div>';
    }
  }

  function renderScan(data) {
    const zone = document.getElementById('scan-zone');

    const checks = [
      { key: 'has_projet_contexte', label: 'PROJET_CONTEXTE.md' },
      { key: 'has_stack_standard',  label: 'STACK_STANDARD.md' },
      { key: 'has_graphify',        label: 'Graphify (GRAPH_REPORT.md)' },
      { key: 'has_changelog',       label: 'CHANGELOG.md' },
    ];

    const checksHtml = checks.map(c => {
      const ok = data[c.key];
      const icon = ok ? '✅' : '⚠️';
      return `<div style="font-size:0.875rem;margin-bottom:0.25rem">${icon} ${c.label}</div>`;
    }).join('');

    const graphifyBtn = !data.has_graphify
      ? `<button onclick="window._initGraphify()" class="btn-secondary btn-sm" style="margin-top:0.5rem">
           ⚡ Initialiser Graphify
         </button>`
      : '';

    const workflowShortcut = data.suggested_workflow
      ? `<div style="margin-top:1rem;padding-top:1rem;border-top:1px solid var(--border)">
           <span style="font-size:0.875rem;color:var(--text-muted)">Workflow suggéré : </span>
           <button onclick="window._launchSuggestedWorkflow('${data.suggested_workflow}')"
             class="btn-secondary btn-sm" style="margin-left:0.5rem">
             ${data.suggested_workflow === 'nouveau_projet' ? '✨ Nouveau projet' : '📦 Projet existant'}
           </button>
         </div>`
      : '';

    const summary = data.session_summary
      ? `<div style="margin-top:1rem;padding:0.75rem;background:var(--bg-secondary);border-radius:6px;font-size:0.875rem;color:var(--text-primary);line-height:1.5">
           ${data.session_summary}
         </div>`
      : '';

    zone.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.25rem 2rem;margin-bottom:0.5rem">
        ${checksHtml}
      </div>
      ${graphifyBtn}
      ${workflowShortcut}
      ${summary}
    `;
  }

  window._initGraphify = async function() {
    if (window.showToast) window.showToast('Initialisation Graphify lancée…', 'info');
    try {
      await window.API.initGraphify(projectId);
      if (window.showToast) window.showToast('Graphify en cours (peut prendre 1-2 min)', 'success');
    } catch (e) {
      if (window.showToast) window.showToast('Erreur init Graphify', 'error');
    }
  };

  window._launchSuggestedWorkflow = function(workflowType) {
    // Passer directement à l'étape B avec mission vide
    routingResult = { workflow_type: workflowType, confidence: 'high', reasoning: 'Workflow suggéré par le scan.', mission_structured: '' };
    document.getElementById('mission-step-a').style.display = 'none';
    showRoutingResult(routingResult);
    document.getElementById('mission-step-b').style.display = 'block';
    // Permettre saisie de la mission dans structured-text
    const el = document.getElementById('mission-structured-text');
    el.contentEditable = 'true';
    el.style.border = '1px solid var(--border)';
    el.style.padding = '0.25rem';
    el.style.borderRadius = '4px';
    el.textContent = '';
    el.focus();
  };

  // ── MISSION ─────────────────────────────────────────────────────

  async function analyzeAndRoute() {
    const mission = document.getElementById('mission-input').value.trim();
    if (!mission) {
      if (window.showToast) window.showToast('Décrivez votre mission d\'abord', 'error');
      return;
    }
    const btn = document.getElementById('btn-analyze');
    btn.disabled = true;
    btn.textContent = '⏳ Analyse…';
    try {
      routingResult = await window.API.routeMission(projectId, mission);
      showRoutingResult(routingResult);
      document.getElementById('mission-step-a').style.display = 'none';
      document.getElementById('mission-step-b').style.display = 'block';
    } catch (error) {
      console.error('Erreur analyse:', error);
      if (window.showToast) window.showToast('Erreur lors de l\'analyse', 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = '🔍 Analyser →';
    }
  }

  function showRoutingResult(result) {
    const workflowColors = {
      'bug_simple': '#ef4444',
      'mission_complexe': '#3b82f6',
      'nouveau_projet': '#10b981',
      'projet_existant': '#10b981'
    };
    const workflowLabels = {
      'bug_simple': '🐛 Bug Simple',
      'mission_complexe': '🎯 Mission Complexe',
      'nouveau_projet': '✨ Nouveau Projet',
      'projet_existant': '📦 Projet Existant'
    };
    const confidenceColors = { 'high': '#10b981', 'medium': '#f59e0b', 'low': '#ef4444' };
    const confidenceLabels = { 'high': '✓ Haute confiance', 'medium': '~ Moyenne confiance', 'low': '⚠ Faible confiance' };

    const color = workflowColors[result.workflow_type] || '#6b7280';
    const wb = document.getElementById('workflow-badge');
    wb.textContent = workflowLabels[result.workflow_type] || result.workflow_type;
    wb.style.backgroundColor = `${color}20`;
    wb.style.color = color;
    wb.style.border = `1px solid ${color}40`;

    const confColor = confidenceColors[result.confidence] || '#6b7280';
    const cb = document.getElementById('confidence-badge');
    cb.textContent = confidenceLabels[result.confidence] || result.confidence;
    cb.style.backgroundColor = `${confColor}20`;
    cb.style.color = confColor;
    cb.style.border = `1px solid ${confColor}40`;

    document.getElementById('reasoning-text').textContent = result.reasoning || '';
    document.getElementById('mission-structured-text').textContent = result.mission_structured || result.mission || '';
    document.getElementById('workflow-override').value = result.workflow_type;
  }

  async function launchMission() {
    const workflowType = document.getElementById('workflow-override').value;
    const missionEl = document.getElementById('mission-structured-text');
    const missionStructured = missionEl.textContent.trim();

    if (!missionStructured) {
      if (window.showToast) window.showToast('La mission reformulée est vide', 'error');
      return;
    }
    const btn = document.getElementById('btn-launch');
    btn.disabled = true;
    btn.textContent = '⏳ Lancement…';
    try {
      const session = await window.API.startPipeline({
        project_id: projectId,
        workflow_type: workflowType,
        initial_input: missionStructured
      });
      const sessionId = session.session?.id || session.session_id || session.id;
      window.location.href = `module-code.html?session=${sessionId}`;
    } catch (error) {
      console.error('Erreur lancement:', error);
      if (window.showToast) window.showToast('Erreur lancement mission', 'error');
      btn.disabled = false;
      btn.textContent = '▶ Lancer la mission';
    }
  }

  // ── SESSIONS ────────────────────────────────────────────────────

  async function loadSessions() {
    try {
      allSessions = await window.API.getProjectSessions(projectId);
      renderSessions();
    } catch (error) {
      document.getElementById('sessions-list').innerHTML =
        '<p style="color:var(--text-muted);padding:0.5rem">Erreur de chargement</p>';
    }
  }

  function renderSessions() {
    const container = document.getElementById('sessions-list');
    const toggleBtn = document.getElementById('btn-toggle-sessions');

    if (allSessions.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);padding:0.5rem">Aucune session</p>';
      toggleBtn.style.display = 'none';
      return;
    }

    const LIMIT = 5;
    const sessions = showAllSessions ? allSessions : allSessions.slice(0, LIMIT);

    if (allSessions.length > LIMIT) {
      toggleBtn.style.display = 'inline-flex';
      toggleBtn.textContent = showAllSessions
        ? `Voir moins` 
        : `Voir tout (${allSessions.length})`;
    } else {
      toggleBtn.style.display = 'none';
    }

    const statusIcons = {
      'COMPLETED':           '✅',
      'WAITING_VALIDATION':  '⏸️',
      'RUNNING':             '🔄',
      'FAILED':              '❌',
      'ABORTED':             '🚫',
      'CREATED':             '🕐'
    };
    const statusColors = {
      'COMPLETED':           '#10b981',
      'WAITING_VALIDATION':  '#f59e0b',
      'RUNNING':             '#3b82f6',
      'FAILED':              '#ef4444',
      'ABORTED':             '#6b7280',
      'CREATED':             '#6b7280'
    };
    const statusLabels = {
      'COMPLETED':           'Terminée',
      'WAITING_VALIDATION':  'En attente',
      'RUNNING':             'En cours',
      'FAILED':              'Échouée',
      'ABORTED':             'Annulée',
      'CREATED':             'Créée'
    };
    const workflowLabels = {
      'bug_simple':      '🐛 Bug Simple',
      'mission_complexe':'🎯 Mission Complexe',
      'nouveau_projet':  '✨ Nouveau Projet',
      'projet_existant': '📦 Projet Existant'
    };

    const formatDate = window.formatDate || ((d) => new Date(d).toLocaleString('fr-FR'));

    container.innerHTML = sessions.map(s => {
      const icon = statusIcons[s.status] || '•';
      const color = statusColors[s.status] || '#6b7280';
      const label = statusLabels[s.status] || s.status;
      const wfLabel = workflowLabels[s.workflow_type] || s.workflow_type;
      return `
        <div class="card card--interactive"
             onclick="location.href='module-code.html?session=${s.id}'"
             style="margin-bottom:0.5rem;padding:0.75rem 1rem;cursor:pointer">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-weight:500;color:var(--text-primary);margin-bottom:0.2rem">
                ${icon} ${wfLabel}
              </div>
              <div style="font-size:0.8rem;color:var(--text-muted)">${formatDate(s.created_at)}</div>
            </div>
            <span class="badge"
              style="background-color:${color}20;color:${color};border:1px solid ${color}40">
              ${label}
            </span>
          </div>
        </div>`;
    }).join('');
  }

  // ── CHATS ───────────────────────────────────────────────────────

  async function loadConversations() {
    try {
      const conversations = await window.API.getConversations(projectId);
      const container = document.getElementById('conversations-list');
      if (conversations.length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted);padding:0.5rem">Aucun chat lié</p>';
        return;
      }
      const formatDate = window.formatDate || ((d) => new Date(d).toLocaleString('fr-FR'));
      container.innerHTML = conversations.map(conv => `
        <div class="card card--interactive"
             onclick="location.href='chat.html?id=${conv.id}'"
             style="margin-bottom:0.5rem;padding:0.75rem 1rem;cursor:pointer">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-weight:500;color:var(--text-primary);margin-bottom:0.2rem">
                ${conv.title || 'Sans titre'}
              </div>
              <div style="font-size:0.8rem;color:var(--text-muted)">
                ${formatDate(conv.updated_at || conv.created_at)}
              </div>
            </div>
            <span style="color:var(--text-muted);font-size:0.875rem">💬 ${conv.message_count || 0}</span>
          </div>
        </div>`).join('');
    } catch (error) {
      document.getElementById('conversations-list').innerHTML =
        '<p style="color:var(--text-muted);padding:0.5rem">Erreur de chargement</p>';
    }
  }

  async function createNewChat() {
    try {
      const conversation = await window.API.createConversation({
        project_id: projectId,
        title: `Chat ${currentProject.name}`,
        model: null
      });
      window.location.href = `chat.html?id=${conversation.id}`;
    } catch (error) {
      if (window.showToast) window.showToast('Erreur création chat', 'error');
    }
  }

})();
