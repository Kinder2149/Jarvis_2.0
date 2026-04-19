window.initSidebar = async () => {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  const collapsed = localStorage.getItem('sidebar_collapsed') === 'true';
  if (collapsed) sidebar.classList.add('sidebar--collapsed');

  try {
    const [projects, conversations, atelierCount, prospects] = await Promise.all([
      window.API.getProjects(),
      window.API.getConversations(),
      getAtelierActiveCount(),
      window.API.getProspects().catch(() => [])
    ]);

    const sessionsMap = {};
    for (const project of projects) {
      try {
        const sessions = await window.API.getProjectSessions(project.id);
        sessionsMap[project.id] = sessions.filter(s => s.status !== 'COMPLETED' && s.status !== 'ABORTED').slice(0, 5);
      } catch (e) {
        sessionsMap[project.id] = [];
      }
    }

    renderSidebar(projects, conversations, sessionsMap, atelierCount, prospects);
  } catch (error) {
    console.error('Erreur chargement sidebar:', error);
    sidebar.innerHTML = '<p style="color:var(--danger);padding:1rem">Erreur chargement</p>';
  }
};

function renderSidebar(projects, conversations, sessionsMap, atelierCount = 0, prospects = []) {
  const sidebar = document.getElementById('sidebar');
  const currentPath = window.location.pathname;
  const currentId = window.getURLParam('id');
  const currentSession = window.getURLParam('session');

  const conversationsByProject = {};
  const freeConversations = [];
  
  conversations.forEach(conv => {
    if (conv.project_id) {
      if (!conversationsByProject[conv.project_id]) conversationsByProject[conv.project_id] = [];
      conversationsByProject[conv.project_id].push(conv);
    } else {
      freeConversations.push(conv);
    }
  });

  let html = `
    <div class="sidebar-header">
      <a href="index.html" class="sidebar-logo" title="Tableau de bord">⚡ <span class="sidebar-text">JARVIS</span></a>
      <button id="btn-sidebar-collapse" class="btn-icon" title="Réduire">
        <span class="sidebar-text">←</span><span class="sidebar-collapsed-text" style="display:none">→</span>
      </button>
    </div>
    <div class="sidebar-actions">
      <button id="btn-new-chat" class="btn-sidebar-action">
        <span class="sidebar-text">💬 Nouveau Chat</span>
        <span class="sidebar-collapsed-text" style="display:none">💬</span>
      </button>
      <a href="code-projects.html" id="btn-module-code" class="btn-sidebar-action" style="text-decoration:none;display:flex;align-items:center;gap:0.5rem">
        <span class="sidebar-text">⚙️ Module Code</span>
        <span class="sidebar-collapsed-text" style="display:none">⚙️</span>
      </a>
      <a href="atelier.html" id="btn-atelier" class="btn-sidebar-action" style="text-decoration:none;display:flex;align-items:center;gap:0.5rem">
        <span class="sidebar-text">🏭 Atelier</span>
        <span class="sidebar-collapsed-text" style="display:none">🏭</span>
      </a>
      <button id="btn-new-project" class="btn-sidebar-action btn-sidebar-action--secondary" title="Nouveau dossier">
        <span class="sidebar-text">📁 Nouveau Dossier</span>
        <span class="sidebar-collapsed-text" style="display:none">📁</span>
      </button>
    </div>
    <div class="sidebar-search">
      <input type="text" id="sidebar-search-input" placeholder="Rechercher..." class="sidebar-text">
    </div>
    <div class="sidebar-nav">
  `;

  const isAtelierActive = currentPath.includes('atelier.html');
  const atelierBadge = atelierCount > 0
    ? `<span class="atelier-active-badge sidebar-text">${atelierCount}</span>` 
    : '';
  
  // Détecter le prospect actif (param URL)
  const currentProspectId = window.getURLParam ? window.getURLParam('prospect_id') : 
                            new URLSearchParams(location.search).get('prospect_id');
  
  let prospectsHTML = '';
  if (prospects.length > 0) {
    prospects.forEach(p => {
      const isActive = isAtelierActive && currentProspectId == p.id;
      const statusIcon = {
        'WAITING_VALIDATION': '⏸️',
        'RUNNING': '⚙️',
        'COMPLETED': '✅',
        'FAILED': '❌',
        'ABORTED': '⛔'
      }[p.session_status] || '';
      prospectsHTML += `
        <div class="nav-item nav-item--chat ${isActive ? 'nav-item--active' : ''}" style="display:flex;align-items:center;justify-content:space-between;padding-right:0.5rem">
          <a href="atelier.html?prospect_id=${p.id}" style="flex:1;text-decoration:none;color:inherit">
            <span class="sidebar-text">${statusIcon} ${p.nom}</span>
          </a>
          <button class="btn-delete-prospect-sidebar" data-id="${p.id}" data-name="${p.nom}" title="Supprimer ce prospect" style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:0.25rem;font-size:0.9rem;opacity:0.6">🗑</button>
        </div>
      `;
    });
  }
  
  const isAtelierExpanded = localStorage.getItem('atelier_expanded') !== 'false';
  
  html += `
    <div class="nav-section nav-section--atelier">
      <div class="nav-project">
        <div class="nav-project-header" data-atelier="true">
          <span class="nav-project-toggle nav-project-arrow" 
                data-atelier="true" 
                title="Déplier/Replier">
            ${isAtelierExpanded ? '▼' : '▶'}
          </span>
          <a href="atelier.html" class="nav-atelier-link nav-project-name ${isAtelierActive && !currentProspectId ? 'nav-item--active' : ''}">
            <span class="sidebar-text">🏭 Atelier Connecté</span>
            ${atelierBadge}
          </a>
        </div>
        <div class="nav-project-items" style="display:${isAtelierExpanded ? 'block' : 'none'}">
          ${prospectsHTML || '<div class="nav-item" style="opacity:0.6;pointer-events:none"><span class="sidebar-text"><em>Aucun prospect</em></span></div>'}
        </div>
      </div>
    </div>
  `;

  const filteredProjects = projects.filter(p => p.path !== '__atelier__');
  
  if (filteredProjects.length > 0) {
    html += '<div class="nav-section"><div class="nav-section-title">DOSSIERS</div>';
    filteredProjects.forEach(project => {
      const projectConvs = conversationsByProject[project.id] || [];
      const projectSessions = sessionsMap[project.id] || [];
      const hasActivePipeline = projectSessions.length > 0;
      const isExpanded = localStorage.getItem(`project_${project.id}_expanded`) !== 'false';

      html += `
        <div class="nav-project">
          <div class="nav-project-header" data-project-id="${project.id}">
            <span class="nav-project-toggle nav-project-arrow" 
                  data-project-id="${project.id}" 
                  title="Déplier/Replier">
              ${isExpanded ? '▼' : '▶'}
            </span>
            <a class="nav-project-name sidebar-text ${currentPath.includes('dossier.html') && currentId == project.id ? 'nav-item--active' : ''}" 
               href="dossier.html?id=${project.id}" 
               title="Ouvrir le dossier">
              ${project.name}
            </a>
            ${hasActivePipeline ? '<span class="active-dot"></span>' : ''}
          </div>
          <div class="nav-project-items" style="display:${isExpanded ? 'block' : 'none'}">
      `;

      projectConvs.forEach(conv => {
        const isActive = currentPath.includes('chat.html') && currentId == conv.id;
        html += `
          <a href="chat.html?id=${conv.id}&project_id=${project.id}" 
             class="nav-item nav-item--chat ${isActive ? 'nav-item--active' : ''}">
            <span class="sidebar-text">💬 ${conv.title}</span>
            <span class="sidebar-collapsed-text" style="display:none">💬</span>
          </a>
        `;
      });

      projectSessions.forEach(session => {
        const isActive = currentPath.includes('module-code.html') && currentSession == session.id;
        const statusBadge = getStatusBadge(session.status);
        html += `
          <a href="module-code.html?session=${session.id}&project_id=${project.id}" 
             class="nav-item nav-item--module ${isActive ? 'nav-item--active' : ''}">
            <span class="sidebar-text">⚙️ ${session.workflow_type} ${statusBadge}</span>
            <span class="sidebar-collapsed-text" style="display:none">⚙️</span>
          </a>
        `;
      });

      html += '</div></div>';
    });
    html += '</div>';
  }

  if (freeConversations.length > 0) {
    html += '<div class="nav-section"><div class="nav-section-title">LIBRES</div>';
    freeConversations.forEach(conv => {
      const isActive = currentPath.includes('chat.html') && currentId == conv.id;
      html += `
        <a href="chat.html?id=${conv.id}" 
           class="nav-item nav-item--chat ${isActive ? 'nav-item--active' : ''}">
          <span class="sidebar-text">💬 ${conv.title}</span>
          <span class="sidebar-collapsed-text" style="display:none">💬</span>
        </a>
      `;
    });
    html += '</div>';
  }

  html += `
    </div>
    <div class="sidebar-footer">
      <div class="sidebar-cost">
        <span class="sidebar-text">💰 $0.000 aujourd'hui</span>
        <span class="sidebar-collapsed-text" style="display:none">💰</span>
      </div>
      <a href="settings.html" class="sidebar-settings">
        <span class="sidebar-text">⚙️ Paramètres</span>
        <span class="sidebar-collapsed-text" style="display:none">⚙️</span>
      </a>
    </div>
  `;

  sidebar.innerHTML = html;

  document.getElementById('btn-sidebar-collapse').addEventListener('click', toggleSidebar);
  document.getElementById('btn-new-chat').addEventListener('click', handleNewChat);
  document.getElementById('btn-new-project').addEventListener('click', handleNewProject);

  document.querySelectorAll('.nav-project-arrow').forEach(arrow => {
    arrow.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const projectId = arrow.dataset.projectId;
      const isAtelier = arrow.dataset.atelier === 'true';
      const header = arrow.closest('.nav-project-header');
      const items = header.nextElementSibling;
      const isExpanded = items.style.display !== 'none';
      items.style.display = isExpanded ? 'none' : 'block';
      arrow.textContent = isExpanded ? '▶' : '▼';
      
      if (isAtelier) {
        localStorage.setItem('atelier_expanded', !isExpanded);
      } else {
        localStorage.setItem(`project_${projectId}_expanded`, !isExpanded);
      }
    });
  });

  // Handlers pour les boutons de suppression des prospects dans la sidebar
  document.querySelectorAll('.btn-delete-prospect-sidebar').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const prospectId = parseInt(btn.dataset.id);
      const prospectName = btn.dataset.name;
      
      if (!confirm(`Supprimer "${prospectName}" et toute sa progression ?\n\nCette action est irréversible.`)) return;
      
      try {
        await window.API.deleteProspect(prospectId);
        window.showToast && window.showToast('Prospect supprimé', 'success');
        
        // Recharger la sidebar
        await renderSidebar();
        
        // Si on est sur la page atelier, recharger
        if (window.location.pathname.includes('atelier.html')) {
          window.location.href = 'atelier.html';
        }
      } catch (err) {
        console.error('Erreur suppression prospect:', err);
        window.showToast && window.showToast('Erreur suppression: ' + err.message, 'error');
      }
    });
  });

  const searchInput = document.getElementById('sidebar-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      document.querySelectorAll('.nav-item').forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query) ? 'flex' : 'none';
      });
    });
  }
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const isCollapsed = sidebar.classList.toggle('sidebar--collapsed');
  localStorage.setItem('sidebar_collapsed', isCollapsed);
  
  document.querySelectorAll('.sidebar-text').forEach(el => {
    el.style.display = isCollapsed ? 'none' : '';
  });
  document.querySelectorAll('.sidebar-collapsed-text').forEach(el => {
    el.style.display = isCollapsed ? '' : 'none';
  });
}

async function handleNewChat() {
  const projects = await window.API.getProjects();
  const dossiers = projects.filter(p => p.module_type === 'dossier');
  
  let optionsHTML = '<option value="">Sans dossier</option>';
  dossiers.forEach(p => {
    optionsHTML += `<option value="${p.id}">${p.name}</option>`;
  });

  const bodyHTML = `
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Titre (optionnel)</label>
      <input type="text" id="modal-chat-title" placeholder="Nouvelle conversation" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Dossier associé (optionnel)</label>
      <select id="modal-project-select" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
        ${optionsHTML}
      </select>
    </div>
  `;

  window.showModal('Nouveau Chat', bodyHTML, [
    { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
    { label: 'Créer', type: 'primary', onClick: async () => {
      const title = document.getElementById('modal-chat-title').value.trim() || 'Nouvelle conversation';
      const projectId = document.getElementById('modal-project-select').value;
      try {
        const conv = await window.API.createConversation({
          project_id: projectId || null,
          title: title
        });
        window.closeModal();
        window.location.href = `chat.html?id=${conv.id}${projectId ? `&project_id=${projectId}` : ''}`;
      } catch (error) {
        window.showToast(error.message, 'error');
      }
    }}
  ]);
}

async function handleNewModule() {
  const projects = await window.API.getProjects();
  
  let projectOptionsHTML = '';
  projects.forEach(p => {
    projectOptionsHTML += `<option value="${p.id}">${p.name}</option>`;
  });

  const workflowOptions = [
    { value: 'session_start',    label: 'Session Start — démarrer une session de dev' },
    { value: 'session_end',      label: 'Session End — clôturer, commit, docs' },
    { value: 'bug_simple',       label: 'Bug Simple — analyser et corriger un bug' },
    { value: 'mission_complexe', label: 'Mission Complexe — feature multi-fichiers' },
    { value: 'nouveau_projet',   label: 'Nouveau Projet Code — initialiser un projet code' },
    { value: 'projet_existant',  label: 'Projet Code Existant — reprendre un projet code' },
  ];

  let workflowOptionsHTML = '';
  workflowOptions.forEach(w => {
    workflowOptionsHTML += `<option value="${w.value}">${w.label}</option>`;
  });

  const bodyHTML = `
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Dossier *</label>
      <select id="modal-module-project" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
        ${projectOptionsHTML}
      </select>
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Workflow *</label>
      <select id="modal-module-workflow" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
        ${workflowOptionsHTML}
      </select>
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Demande initiale *</label>
      <textarea id="modal-module-input" rows="4" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);resize:vertical" placeholder="Décrivez votre demande..."></textarea>
    </div>
  `;

  window.showModal('Nouveau Module Code', bodyHTML, [
    { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
    { label: 'Lancer', type: 'primary', onClick: async () => {
      const projectId = document.getElementById('modal-module-project').value;
      const workflow = document.getElementById('modal-module-workflow').value;
      const input = document.getElementById('modal-module-input').value.trim();

      if (!projectId || !workflow || !input) {
        window.showToast('Tous les champs sont requis', 'error');
        return;
      }

      try {
        const result = await window.API.startPipeline({
          project_id: parseInt(projectId),
          workflow_type: workflow,
          initial_input: input
        });
        const sessionId = result.session?.id || result.id;
        if (!sessionId) throw new Error('Session ID non trouvé dans la réponse');
        window.closeModal();
        window.location.href = `module-code.html?session=${sessionId}&project_id=${projectId}`;
      } catch (error) {
        window.showToast(error.message, 'error');
      }
    }}
  ]);
}

async function handleNewModulePreset(presetProjectId, presetWorkflow) {
  const projects = await window.API.getProjects();

  const workflowOptions = [
    { value: 'session_start',    label: 'Session Start — démarrer une session de dev' },
    { value: 'session_end',      label: 'Session End — clôturer, commit, docs' },
    { value: 'bug_simple',       label: 'Bug Simple — analyser et corriger un bug' },
    { value: 'mission_complexe', label: 'Mission Complexe — feature multi-fichiers' },
    { value: 'nouveau_projet',   label: 'Nouveau Projet Code — initialiser un projet code' },
    { value: 'projet_existant',  label: 'Projet Code Existant — reprendre un projet code' },
  ];

  let projectOptionsHTML = '';
  projects.forEach(p => {
    const selected = String(p.id) === String(presetProjectId) ? 'selected' : '';
    projectOptionsHTML += `<option value="${p.id}" ${selected}>${p.name}</option>`;
  });

  let workflowOptionsHTML = '';
  workflowOptions.forEach(w => {
    const selected = w.value === presetWorkflow ? 'selected' : '';
    workflowOptionsHTML += `<option value="${w.value}" ${selected}>${w.label}</option>`;
  });

  const bodyHTML = `
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Dossier *</label>
      <select id="modal-module-project" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)"
              ${presetProjectId ? 'disabled' : ''}>
        ${projectOptionsHTML}
      </select>
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Workflow *</label>
      <select id="modal-module-workflow" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
        ${workflowOptionsHTML}
      </select>
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Demande initiale *</label>
      <textarea id="modal-module-input" rows="4" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);resize:vertical" placeholder="Décrivez votre demande..."></textarea>
    </div>
  `;

  window.showModal('Nouvelle session', bodyHTML, [
    { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
    { label: 'Lancer', type: 'primary', onClick: async () => {
      const projId = presetProjectId || document.getElementById('modal-module-project').value;
      const workflow = document.getElementById('modal-module-workflow').value;
      const input = document.getElementById('modal-module-input').value.trim();
      if (!projId || !workflow || !input) {
        window.showToast('Tous les champs sont requis', 'error');
        return;
      }
      try {
        const result = await window.API.startPipeline({
          project_id: parseInt(projId),
          workflow_type: workflow,
          initial_input: input
        });
        const sessionId = result.session?.id || result.id;
        if (!sessionId) throw new Error('Session ID non trouvé');
        window.closeModal();
        window.location.href = `module-code.html?session=${sessionId}&project_id=${projId}`;
      } catch (error) {
        window.showToast(error.message, 'error');
      }
    }}
  ]);
}

window.handleNewModulePreset = handleNewModulePreset;

async function handleNewProject() {
  const bodyHTML = `
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Nom du dossier *</label>
      <input type="text" id="modal-project-name" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)" placeholder="Mon Dossier">
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Chemin du dossier *</label>
      <input type="text" id="modal-project-path" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)" placeholder="C:\\DEV\\MON_PROJET">
      <div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px">Le dossier doit exister sur le disque</div>
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Type</label>
      <select id="modal-project-type" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
        <option value="dev">Développement</option>
        <option value="research">Recherche</option>
        <option value="business">Business</option>
        <option value="other">Autre</option>
      </select>
    </div>
  `;

  window.showModal('Nouveau Dossier', bodyHTML, [
    { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
    { label: '📁 Créer', type: 'primary', onClick: async () => {
      const name = document.getElementById('modal-project-name').value.trim();
      const path = document.getElementById('modal-project-path').value.trim();
      const type = document.getElementById('modal-project-type').value;
      
      if (!name || !path) {
        window.showToast('Nom et chemin sont requis', 'error');
        return;
      }
      
      try {
        const project = await window.API.createProject({ name, path, type, instructions: '' });
        window.closeModal();
        window.showToast(`Dossier "${name}" créé`);
        window.location.href = `dossier.html?id=${project.id}`;
      } catch(error) {
        window.showToast(error.message, 'error');
      }
    }}
  ]);
}

function getStatusBadge(status) {
  const badges = {
    'PENDING': '<span class="badge badge--pending">En attente</span>',
    'RUNNING': '<span class="badge badge--running">⏳</span>',
    'COMPLETED': '<span class="badge badge--success">✅</span>',
    'ERROR': '<span class="badge badge--error">❌</span>',
    'WAITING_VALIDATION': '<span class="badge badge--waiting">⏸️</span>'
  };
  return badges[status] || '';
}

async function getAtelierActiveCount() {
  try {
    const prospects = await window.API.getProspects();
    return prospects.filter(p => p.session_status === 'WAITING_VALIDATION').length;
  } catch (e) {
    return 0;
  }
}
