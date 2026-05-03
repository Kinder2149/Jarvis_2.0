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
    const reflexionsMap = {};
    
    const today = new Date().toDateString();
    let todayCost = 0;
    for (const project of projects) {
      try {
        const allSessions = await window.API.getProjectSessions(project.id);
        allSessions.forEach(s => {
          if (new Date(s.created_at).toDateString() === today) {
            todayCost += (s.total_cost_usd || 0);
          }
        });
        sessionsMap[project.id] = allSessions
          .filter(s => !['COMPLETED', 'ABORTED', 'FAILED'].includes(s.status))
          .slice(0, 5);
      } catch (e) {
        sessionsMap[project.id] = [];
      }
      try {
        const reflexions = await window.API.getReflexions(project.id);
        reflexionsMap[project.id] = reflexions.filter(s => s.statut !== 'ABANDONNEE').slice(0, 5);
      } catch (e) {
        reflexionsMap[project.id] = [];
      }
    }

    renderSidebar(projects, conversations, sessionsMap, atelierCount, prospects, reflexionsMap, todayCost);
  } catch (error) {
    console.error('Erreur chargement sidebar:', error);
    sidebar.innerHTML = '<p style="color:var(--danger);padding:1rem">Erreur chargement</p>';
  }
};

function renderSidebar(projects, conversations, sessionsMap, atelierCount = 0, prospects = [], reflexionsMap = {}, todayCost = 0) {
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
      <a href="index.html" class="sidebar-logo" title="Tableau de bord"><span class="sidebar-text" style="font-family:var(--mono);letter-spacing:0.1em">⚡ JARVIS</span></a>
      <button id="btn-sidebar-collapse" class="btn-icon" title="Réduire">
        <span class="sidebar-text">←</span><span class="sidebar-collapsed-text" style="display:none">→</span>
      </button>
    </div>
    <div class="sidebar-actions">
      <div class="sidebar-actions-grid">
        <button id="btn-new-chat" class="btn-create" title="Module Chat">
          <span class="btn-create-emoji">💬</span>
          <span class="sidebar-text btn-create-label">Chat</span>
        </button>
        <button id="btn-new-mission" class="btn-create" title="Module Code">
          <span class="btn-create-emoji">⚙️</span>
          <span class="sidebar-text btn-create-label">Code</span>
        </button>
        <button id="btn-new-prospect" class="btn-create" title="Module Atelier">
          <span class="btn-create-emoji">🏭</span>
          <span class="sidebar-text btn-create-label">Atelier</span>
        </button>
        <button id="btn-new-reflexion" class="btn-create" title="Module Réflexion">
          <span class="btn-create-emoji">🧠</span>
          <span class="sidebar-text btn-create-label">Réflexion</span>
        </button>
      </div>
    </div>
    <div class="sidebar-search">
      <input type="text" id="sidebar-search-input" placeholder="Rechercher..." class="sidebar-text">
    </div>
    <div class="sidebar-tabs sidebar-text">
      <button class="sidebar-tab" data-tab="projects">📁 Projets</button>
      <button class="sidebar-tab" data-tab="conversations">💬 Chats</button>
      <button class="sidebar-tab" data-tab="prospects">🏭 Atelier</button>
    </div>
    <div id="sidebar-tab-content" class="sidebar-nav">
  `;

  const filteredProjects = projects.filter(p => p.path !== '__atelier__');

  html += `
    </div>
    <div class="sidebar-footer">
      <div class="sidebar-cost">
        <span class="sidebar-text">� <span style="font-family:var(--mono)">$${todayCost.toFixed(3)}</span> aujourd'hui</span>
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
  document.getElementById('btn-new-chat').addEventListener('click', () => {
    window.location.href = 'chat.html';
  });
  document.getElementById('btn-new-mission').addEventListener('click', () => {
    window.location.href = 'code-projects.html';
  });
  document.getElementById('btn-new-prospect')?.addEventListener('click', () => {
    window.location.href = 'atelier.html';
  });
  document.getElementById('btn-new-reflexion')?.addEventListener('click', handleNewMission);

  const sidebarData = { projects, conversations, sessionsMap, reflexionsMap, prospects, filteredProjects };
  let activeTab = localStorage.getItem('sidebar_active_tab') || '';

  function renderTabContent(tab) {
    const container = document.getElementById('sidebar-tab-content');
    if (!container) return;

    document.querySelectorAll('.sidebar-tab').forEach(btn => {
      btn.classList.toggle('sidebar-tab--active', btn.dataset.tab === tab);
    });

    if (!tab) {
      container.innerHTML = '';
      return;
    }

    let html = '';
    const currentPath = window.location.pathname;
    const currentId = window.getURLParam ? window.getURLParam('id') : '';

    if (tab === 'projects') {
      const fp = sidebarData.filteredProjects;
      if (fp.length === 0) {
        html = '<div class="sidebar-empty sidebar-text">Aucun projet</div>';
      } else {
        html += '<div class="nav-section"><div class="nav-section-title sidebar-text">PROJETS</div>';
        fp.forEach(project => {
          const projectConvs = sidebarData.conversations.filter(c => c.project_id === project.id);
          const projectSessions = sidebarData.sessionsMap[project.id] || [];
          const projectReflexions = sidebarData.reflexionsMap[project.id] || [];
          const hasActivePipeline = projectSessions.length > 0;
          const isExpanded = localStorage.getItem(`project_${project.id}_expanded`) !== 'false';

          const allChildren = [
            ...projectConvs.map(c => ({ type: 'conv', data: c })),
            ...projectReflexions.map(r => ({ type: 'ref', data: r })),
            ...projectSessions.map(s => ({ type: 'session', data: s }))
          ];
          const total = allChildren.length;

          html += `
            <div class="nav-project">
              <div class="nav-project-header" data-project-id="${project.id}">
                <span class="nav-project-toggle nav-project-arrow" data-project-id="${project.id}">
                  ${isExpanded ? '▼' : '▶'}
                </span>
                <a class="nav-project-name sidebar-text ${currentPath.includes('dossier.html') && currentId == project.id ? 'nav-item--active' : ''}"
                   href="dossier.html?id=${project.id}">
                  ${project.name}
                </a>
                ${hasActivePipeline ? '<span class="active-dot"></span>' : ''}
                <span class="nav-project-actions">
                  <button class="nav-action-btn btn-rename-project" data-id="${project.id}" data-name="${project.name}" title="Renommer">✏️</button>
                  <button class="nav-action-btn btn-new-chat-project" data-id="${project.id}" title="Nouveau chat">💬</button>
                  <button class="nav-action-btn btn-delete-project" data-id="${project.id}" data-name="${project.name}" title="Supprimer">🗑️</button>
                </span>
              </div>
              <div class="nav-project-items" style="display:${isExpanded ? 'block' : 'none'}">
          `;

          allChildren.forEach((child, idx) => {
            const prefix = idx === total - 1 ? '└ ' : '├ ';
            if (child.type === 'conv') {
              const c = child.data;
              const isActive = currentPath.includes('chat.html') && window.getURLParam && window.getURLParam('id') == c.id;
              html += `
                <div class="nav-item-row nav-item ${isActive ? 'nav-item--active' : ''}">
                  <a href="chat.html?id=${c.id}&project_id=${project.id}" class="nav-item-label sidebar-text">
                    ${prefix}💬 ${c.title}
                  </a>
                  <button class="nav-action-btn btn-delete-conv" data-id="${c.id}" title="Supprimer">🗑️</button>
                </div>`;
            } else if (child.type === 'ref') {
              const r = child.data;
              const icons = { 'OUVERTE': '🧠', 'EN_FIGEMENT': '⏳', 'FIGEE': '🔒' };
              const icon = icons[r.statut] || '🧠';
              const isActive = currentPath.includes('mission.html') && window.getURLParam && window.getURLParam('session') == r.id;
              html += `
                <div class="nav-item-row nav-item ${isActive ? 'nav-item--active' : ''}">
                  <a href="mission.html?session=${r.id}&project_id=${project.id}" class="nav-item-label sidebar-text">
                    ${prefix}${icon} ${r.titre || 'Réflexion #' + r.id}
                  </a>
                  <button class="nav-action-btn btn-delete-reflexion" data-id="${r.id}" title="Supprimer">🗑️</button>
                </div>`;
            } else {
              const s = child.data;
              const isActive = currentPath.includes('mission.html') && window.getURLParam && window.getURLParam('pipeline_session') == s.id;
              html += `
                <div class="nav-item-row nav-item ${isActive ? 'nav-item--active' : ''}">
                  <a href="mission.html?pipeline_session=${s.id}&project_id=${project.id}" class="nav-item-label sidebar-text">
                    ${prefix}⚙ ${s.workflow_type}
                  </a>
                </div>`;
            }
          });

          html += '</div></div>';
        });
        html += '</div>';
      }

    } else if (tab === 'conversations') {
      const free = sidebarData.conversations.filter(c => !c.project_id);
      const withProject = sidebarData.conversations.filter(c => c.project_id);
      if (sidebarData.conversations.length === 0) {
        html = '<div class="sidebar-empty sidebar-text">Aucune conversation</div>';
      } else {
        if (withProject.length > 0) {
          html += '<div class="nav-section"><div class="nav-section-title sidebar-text">PAR PROJET</div>';
          withProject.forEach(conv => {
            const project = sidebarData.projects.find(p => p.id === conv.project_id);
            const isActive = window.location.href.includes('chat.html') && window.getURLParam && window.getURLParam('id') == conv.id;
            html += `
              <div class="nav-item-row nav-item ${isActive ? 'nav-item--active' : ''}">
                <a href="chat.html?id=${conv.id}&project_id=${conv.project_id}" class="nav-item-label sidebar-text">
                  💬 ${conv.title}
                  ${project ? '<span style="font-size:0.7rem;color:var(--text-muted)"> · ' + project.name + '</span>' : ''}
                </a>
                <button class="nav-action-btn btn-delete-conv" data-id="${conv.id}" title="Supprimer">🗑️</button>
              </div>`;
          });
          html += '</div>';
        }
        if (free.length > 0) {
          html += '<div class="nav-section"><div class="nav-section-title sidebar-text">LIBRES</div>';
          free.forEach(conv => {
            const isActive = window.location.href.includes('chat.html') && window.getURLParam && window.getURLParam('id') == conv.id;
            html += `
              <div class="nav-item-row nav-item ${isActive ? 'nav-item--active' : ''}">
                <a href="chat.html?id=${conv.id}" class="nav-item-label sidebar-text">💬 ${conv.title}</a>
                <button class="nav-action-btn btn-delete-conv" data-id="${conv.id}" title="Supprimer">🗑️</button>
              </div>`;
          });
          html += '</div>';
        }
      }

    } else if (tab === 'prospects') {
      if (sidebarData.prospects.length === 0) {
        html = '<div class="sidebar-empty sidebar-text">Aucun prospect</div>';
      } else {
        html += '<div class="nav-section"><div class="nav-section-title sidebar-text">ATELIER CONNECTÉ</div>';
        sidebarData.prospects.forEach(p => {
          const statusIcon = { 'WAITING_VALIDATION':'⏸️','RUNNING':'⚙️','COMPLETED':'✅','FAILED':'❌','ABORTED':'⛔' }[p.session_status] || '';
          html += `
            <div class="nav-item-row nav-item">
              <a href="atelier.html?prospect_id=${p.id}" class="nav-item-label sidebar-text">
                ${statusIcon} ${p.nom}
              </a>
              <button class="nav-action-btn btn-delete-prospect-sidebar" data-id="${p.id}" data-name="${p.nom}" title="Supprimer">🗑️</button>
            </div>`;
        });
        html += '</div>';
      }
    }

    container.innerHTML = html;
    attachTabContentListeners();

    container.querySelectorAll('.nav-project-arrow').forEach(arrow => {
      arrow.addEventListener('click', (e) => {
        e.preventDefault(); e.stopPropagation();
        const projectId = arrow.dataset.projectId;
        const header = arrow.closest('.nav-project-header');
        const items = header.nextElementSibling;
        const isExpanded = items.style.display !== 'none';
        items.style.display = isExpanded ? 'none' : 'block';
        arrow.textContent = isExpanded ? '▶' : '▼';
        localStorage.setItem(`project_${projectId}_expanded`, !isExpanded);
      });
    });
  }

  document.querySelectorAll('.sidebar-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      if (activeTab === tab) {
        activeTab = '';
      } else {
        activeTab = tab;
      }
      localStorage.setItem('sidebar_active_tab', activeTab);
      renderTabContent(activeTab);
    });
  });

  renderTabContent(activeTab);

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

function attachTabContentListeners() {
  document.querySelectorAll('.btn-delete-project').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault(); e.stopPropagation();
      const id = parseInt(btn.dataset.id);
      const name = btn.dataset.name;
      if (!confirm(`Supprimer le projet "${name}" et tout son contenu ?\n\nCette action est irréversible.`)) return;
      try {
        await window.API.deleteProject(id);
        window.showToast && window.showToast(`Projet "${name}" supprimé`, 'success');
        await window.initSidebar();
      } catch(err) {
        window.showToast && window.showToast('Erreur : ' + err.message, 'error');
      }
    });
  });

  document.querySelectorAll('.btn-delete-conv').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault(); e.stopPropagation();
      const id = parseInt(btn.dataset.id);
      if (!confirm('Supprimer cette conversation ?')) return;
      try {
        await window.API.deleteConversation(id);
        window.showToast && window.showToast('Conversation supprimée', 'success');
        if (window.location.href.includes('chat.html')) {
          window.location.href = 'index.html';
        } else {
          await window.initSidebar();
        }
      } catch(err) {
        window.showToast && window.showToast('Erreur : ' + err.message, 'error');
      }
    });
  });

  document.querySelectorAll('.btn-delete-reflexion').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault(); e.stopPropagation();
      const id = parseInt(btn.dataset.id);
      if (!confirm('Supprimer cette session de réflexion ?')) return;
      try {
        await window.API.deleteReflexion(id);
        window.showToast && window.showToast('Réflexion supprimée', 'success');
        if (window.location.href.includes('mission.html')) {
          window.location.href = 'index.html';
        } else {
          await window.initSidebar();
        }
      } catch(err) {
        window.showToast && window.showToast('Erreur : ' + err.message, 'error');
      }
    });
  });

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
        await window.initSidebar();
        if (window.location.pathname.includes('atelier.html')) {
          window.location.href = 'atelier.html';
        }
      } catch (err) {
        console.error('Erreur suppression prospect:', err);
        window.showToast && window.showToast('Erreur suppression: ' + err.message, 'error');
      }
    });
  });

  document.querySelectorAll('.btn-rename-project').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault(); e.stopPropagation();
      const id = parseInt(btn.dataset.id);
      const currentName = btn.dataset.name;
      const newName = prompt('Nouveau nom (emoji accepté en début) :', currentName);
      if (!newName || newName.trim() === currentName) return;
      try {
        await window.API.updateProject(id, { name: newName.trim() });
        window.showToast && window.showToast('Projet renommé', 'success');
        await window.initSidebar();
      } catch(err) {
        window.showToast && window.showToast('Erreur : ' + err.message, 'error');
      }
    });
  });

  document.querySelectorAll('.btn-new-chat-project').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault(); e.stopPropagation();
      const projectId = parseInt(btn.dataset.id);
      try {
        const conv = await window.API.createConversation({ project_id: projectId, title: 'Nouvelle conversation' });
        window.location.href = `chat.html?id=${conv.id}&project_id=${projectId}`;
      } catch(err) {
        window.showToast && window.showToast('Erreur : ' + err.message, 'error');
      }
    });
  });
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




async function handleNewMission() {
  const projects = await window.API.getProjects();
  const filtered = projects.filter(p => p.path !== '__atelier__');

  let optionsHTML = '<option value="">Sans projet</option>';
  filtered.forEach(p => {
    optionsHTML += `<option value="${p.id}">${p.name}</option>`;
  });

  const bodyHTML = `
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Projet associé</label>
      <select id="modal-mission-project" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
        ${optionsHTML}
      </select>
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Type de livrable</label>
      <div style="display:flex;flex-direction:column;gap:0.5rem">
        <label style="cursor:pointer;color:var(--text-primary)">
          <input type="radio" name="mission_livrable_type" value="mission_code" checked> 🎯 Mission Code — génère un prompt pour exécution pipeline
        </label>
        <label style="cursor:pointer;color:var(--text-primary)">
          <input type="radio" name="mission_livrable_type" value="decision_figee"> 📌 Décision figée — documente une décision dans PROJET_CONTEXTE
        </label>
        <label style="cursor:pointer;color:var(--text-primary)">
          <input type="radio" name="mission_livrable_type" value="plan_multi_missions"> 📋 Plan multi-missions — décompose en plusieurs missions code
        </label>
      </div>
    </div>
  `;

  window.showModal('Nouvelle Réflexion', bodyHTML, [
    { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
    { label: '🧠 Créer', type: 'primary', onClick: () => {
      const projectId = document.getElementById('modal-mission-project').value;
      const livrableType = document.querySelector('input[name="mission_livrable_type"]:checked').value;
      window.closeModal();
      const params = new URLSearchParams();
      if (projectId) params.set('project_id', projectId);
      params.set('new', livrableType);
      window.location.href = `mission.html?${params.toString()}`;
    }}
  ]);
}

async function handleNewProject() {
  const bodyHTML = `
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Nom du projet *</label>
      <input type="text" id="modal-project-name"
        style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)"
        placeholder="Mon Projet">
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Dossier local lié *</label>
      <input type="text" id="modal-project-path"
        style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)"
        placeholder="C:\\DEV\\MON_PROJET">
      <div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px">
        Le dossier doit déjà exister sur votre disque
      </div>
    </div>
  `;

  window.showModal('Nouveau Projet', bodyHTML, [
    { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
    { label: '+ Créer', type: 'primary', onClick: async () => {
      const name = document.getElementById('modal-project-name').value.trim();
      const path = document.getElementById('modal-project-path').value.trim();
      if (!name || !path) {
        window.showToast('Nom et chemin sont requis', 'error');
        return;
      }
      try {
        const project = await window.API.createProject({
          name, path, module_type: 'dossier', instructions: ''
        });
        window.closeModal();
        window.showToast(`Projet "${name}" créé`, 'success');
        window.location.href = `dossier.html?id=${project.id}`;
      } catch(error) {
        window.showToast(error.message, 'error');
      }
    }}
  ]);
}

async function handleLinkFolder() {
  const bodyHTML = `
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Nom du dossier *</label>
      <input type="text" id="modal-project-name" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)" placeholder="Mon Dossier">
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Chemin du dossier local existant *</label>
      <input type="text" id="modal-project-path" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)" placeholder="C:\\DEV\\MON_PROJET">
      <div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px">Ce dossier doit déjà exister sur votre disque</div>
    </div>
  `;

  window.showModal('Lier un dossier local', bodyHTML, [
    { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
    { label: '📁 Créer', type: 'primary', onClick: async () => {
      const name = document.getElementById('modal-project-name').value.trim();
      const path = document.getElementById('modal-project-path').value.trim();
      
      if (!name || !path) {
        window.showToast('Nom et chemin sont requis', 'error');
        return;
      }
      
      try {
        const project = await window.API.createProject({ name, path, module_type: 'dossier', instructions: '' });
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
    'FAILED': '<span class="badge badge--error">💀</span>',
    'ABORTED': '<span class="badge badge--aborted">⛔</span>',
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
