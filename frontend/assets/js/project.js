(function() {
  let projectId = null;
  let project = null;
  let conversations = [];
  let sessions = [];

  document.addEventListener('DOMContentLoaded', async () => {
    projectId = window.getURLParam ? window.getURLParam('id') : new URLSearchParams(location.search).get('id');

    if (!projectId) {
      document.getElementById('page-project').innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center">Dossier non trouvé</p>';
      return;
    }

    await loadProjectData();
    renderProject();
    attachEventListeners();
  });

  async function loadProjectData() {
    try {
      [project, conversations, sessions] = await Promise.all([
        window.API.getProject(projectId),
        window.API.getConversations(projectId),
        window.API.getProjectSessions(projectId)
      ]);
      
      // Charger les projets code liés
      await loadLinkedCodeProjects();
    } catch (error) {
      console.error('Erreur chargement dossier:', error);
      if (window.showToast) window.showToast('Erreur de chargement', 'error');
    }
  }

  function renderProject() {
    document.getElementById('project-name').textContent = project.name;
    document.getElementById('project-path').textContent = project.path;

    renderInstructions();
    renderLocalPath();
    renderConversations();
    initializeExplorer();
  }

  function renderInstructions() {
    const display = document.getElementById('instructions-display');
    const renderMarkdown = window.renderMarkdown || ((text) => text);

    if (project.instructions && project.instructions.trim()) {
      display.innerHTML = renderMarkdown(project.instructions);
    } else {
      display.innerHTML = '<span style="color:var(--text-muted);font-style:italic">Aucune instruction définie. Cliquer sur ✏️ pour ajouter le contexte de ce dossier.</span>';
    }
  }

  function renderLocalPath() {
    const display = document.getElementById('local-path-display');

    if (project.local_path && project.local_path.trim()) {
      display.innerHTML = `<span style="font-family:monospace;color:var(--text-primary)">${project.local_path}</span>`;
    } else {
      display.innerHTML = '<span style="color:var(--text-muted);font-style:italic">Aucun dossier lié</span>';
    }
  }

  function renderConversations() {
    const container = document.getElementById('conversations-list');
    const items = buildConversationsList();

    if (items.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem">Aucune conversation</p>';
      return;
    }

    container.innerHTML = items.map(item => renderConversationItem(item)).join('');
  }

  function buildConversationsList() {
    const items = [];

    conversations.forEach(conv => {
      items.push({
        type: 'chat',
        id: conv.id,
        title: conv.title || 'Conversation sans titre',
        date: conv.last_message_at || conv.created_at,
        preview: conv.last_message_preview || '',
        href: `chat.html?id=${conv.id}&project_id=${projectId}`
      });
    });

    sessions.forEach(session => {
      items.push({
        type: 'module',
        id: session.id,
        title: session.workflow_type,
        date: session.updated_at || session.created_at,
        status: session.status,
        cost: session.total_cost_usd || 0,
        href: `module-code.html?session=${session.id}&project_id=${projectId}`
      });
    });

    items.sort((a, b) => new Date(b.date) - new Date(a.date));
    return items;
  }

  function renderConversationItem(item) {
    const icon = item.type === 'chat' ? '💬' : '⚙️';
    const formatDate = window.formatDate || ((d) => new Date(d).toLocaleString('fr-FR'));
    
    let metaHTML = `<span>${formatDate(item.date)}</span>`;

    if (item.type === 'module') {
      metaHTML += window.statusBadge ? window.statusBadge(item.status) : `<span class="badge">${item.status}</span>`;
      if (item.cost > 0) {
        metaHTML += window.costBadge ? window.costBadge(item.cost) : `<span class="badge">$${item.cost.toFixed(4)}</span>`;
      }
    } else if (item.preview) {
      const truncated = item.preview.length > 60 ? item.preview.substring(0, 60) + '...' : item.preview;
      metaHTML += `<span class="text-muted">${truncated}</span>`;
    }

    const deleteBtn = item.type === 'chat' 
      ? `<button class="btn-icon btn-delete-conv" data-conv-id="${item.id}" title="Supprimer" onclick="event.stopPropagation()">🗑️</button>`
      : '';

    return `
      <div class="conversation-item card card--interactive" onclick="location.href='${item.href}'">
        <div class="conversation-item-icon">${icon}</div>
        <div class="conversation-item-content">
          <div class="conversation-item-title">${item.title}</div>
          <div class="conversation-item-meta">${metaHTML}</div>
        </div>
        ${deleteBtn}
      </div>
    `;
  }

  function attachEventListeners() {
    document.getElementById('btn-edit-instructions').addEventListener('click', toggleInstructionsEdit);
    document.getElementById('btn-save-instructions').addEventListener('click', saveInstructions);
    document.getElementById('btn-cancel-instructions').addEventListener('click', cancelInstructionsEdit);

    document.getElementById('btn-edit-local-path').addEventListener('click', toggleLocalPathEdit);
    document.getElementById('btn-save-local-path').addEventListener('click', saveLocalPath);
    document.getElementById('btn-cancel-local-path').addEventListener('click', cancelLocalPathEdit);

    document.getElementById('btn-project-new-chat').addEventListener('click', createNewChat);
    document.getElementById('btn-project-new-module').addEventListener('click', () => {
      if (typeof window.handleNewModulePreset === 'function') {
        window.handleNewModulePreset(parseInt(projectId), null);
      } else if (typeof window.handleNewModule === 'function') {
        window.handleNewModule();
      }
    });
    document.getElementById('btn-delete-project').addEventListener('click', deleteProject);

    // Onglets activité
    document.querySelectorAll('.activity-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.activity-tab').forEach(t => t.classList.remove('activity-tab--active'));
        tab.classList.add('activity-tab--active');
        const target = tab.dataset.activity;
        document.getElementById('activity-chats').style.display = target === 'chats' ? 'block' : 'none';
        document.getElementById('activity-projets-code').style.display = target === 'projets-code' ? 'block' : 'none';
      });
    });

    // Bouton associer projet code
    const btnAssociate = document.getElementById('btn-associate-code-project');
    if (btnAssociate) {
      btnAssociate.addEventListener('click', showAssociateCodeProjectModal);
    }

    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-delete-conv')) {
        const convId = e.target.dataset.convId;
        deleteConversation(convId);
      }
    });
  }

  function toggleInstructionsEdit() {
    const display = document.getElementById('instructions-display');
    const edit = document.getElementById('instructions-edit');
    const textarea = document.getElementById('instructions-input');

    display.style.display = 'none';
    edit.style.display = 'block';
    textarea.value = project.instructions || '';
    textarea.focus();
  }

  function cancelInstructionsEdit() {
    const display = document.getElementById('instructions-display');
    const edit = document.getElementById('instructions-edit');

    display.style.display = 'block';
    edit.style.display = 'none';
  }

  async function saveInstructions() {
    const textarea = document.getElementById('instructions-input');
    const newInstructions = textarea.value.trim();

    try {
      await window.API.updateProject(projectId, { instructions: newInstructions });
      project.instructions = newInstructions;
      renderInstructions();
      cancelInstructionsEdit();
      if (window.showToast) window.showToast('Instructions sauvegardées');
    } catch (error) {
      console.error('Erreur sauvegarde instructions:', error);
      if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
    }
  }

  function toggleLocalPathEdit() {
    const display = document.getElementById('local-path-display');
    const edit = document.getElementById('local-path-edit');
    const input = document.getElementById('local-path-input');

    display.style.display = 'none';
    edit.style.display = 'block';
    input.value = project.local_path || '';
    input.focus();
  }

  function cancelLocalPathEdit() {
    const display = document.getElementById('local-path-display');
    const edit = document.getElementById('local-path-edit');

    display.style.display = 'block';
    edit.style.display = 'none';
  }

  async function saveLocalPath() {
    const input = document.getElementById('local-path-input');
    const newPath = input.value.trim();

    try {
      await window.API.updateProject(projectId, { local_path: newPath || null });
      project.local_path = newPath;
      renderLocalPath();
      cancelLocalPathEdit();
      
      if (window.showToast) window.showToast('Dossier local sauvegardé');
      
      if (window.EventBus) {
        window.EventBus.emit('project:local-path-updated', { projectId, local_path: newPath });
      }

      location.reload();
    } catch (error) {
      console.error('Erreur sauvegarde local_path:', error);
      if (window.showToast) window.showToast('Erreur de sauvegarde', 'error');
    }
  }

  async function createNewChat() {
    try {
      const conv = await window.API.createConversation({
        project_id: parseInt(projectId),
        title: 'Nouvelle conversation'
      });
      location.href = `chat.html?id=${conv.id}&project_id=${projectId}`;
    } catch (error) {
      console.error('Erreur création chat:', error);
      if (window.showToast) window.showToast('Erreur création chat', 'error');
    }
  }

  async function deleteConversation(convId) {
    if (!window.showModal) {
      if (!confirm('Supprimer cette conversation ?')) return;
      await performDeleteConversation(convId);
      return;
    }

    window.showModal(
      'Supprimer cette conversation ?',
      'Cette conversation sera supprimée définitivement.',
      [
        {
          label: 'Supprimer',
          type: 'danger',
          onClick: async () => {
            await performDeleteConversation(convId);
          }
        },
        {
          label: 'Annuler',
          type: 'secondary',
          onClick: () => {
            if (window.closeModal) window.closeModal();
          }
        }
      ]
    );
  }

  async function performDeleteConversation(convId) {
    try {
      await window.API.deleteConversation(convId);
      conversations = conversations.filter(c => c.id !== parseInt(convId));
      renderConversations();
      if (window.showToast) window.showToast('Conversation supprimée');
      if (window.closeModal) window.closeModal();
    } catch (error) {
      console.error('Erreur suppression conversation:', error);
      if (window.showToast) window.showToast('Erreur suppression', 'error');
    }
  }

  async function deleteProject() {
    if (!window.showModal) {
      if (!confirm(`Supprimer le dossier '${project.name}' ? Toutes les conversations et sessions seront perdues définitivement.`)) return;
      await performDeleteProject();
      return;
    }

    window.showModal(
      `Supprimer le dossier '${project.name}' ?`,
      'Toutes les conversations et sessions seront perdues définitivement.',
      [
        {
          label: 'Supprimer',
          type: 'danger',
          onClick: async () => {
            await performDeleteProject();
          }
        },
        {
          label: 'Annuler',
          type: 'secondary',
          onClick: () => {
            if (window.closeModal) window.closeModal();
          }
        }
      ]
    );
  }

  async function performDeleteProject() {
    try {
      await window.API.deleteProject(projectId);
      if (window.showToast) window.showToast('Dossier supprimé');
      location.href = 'index.html';
    } catch (error) {
      console.error('Erreur suppression dossier:', error);
      if (window.showToast) window.showToast('Erreur suppression', 'error');
    }
  }

  async function loadLinkedCodeProjects() {
    try {
      const allProjects = await window.API.getProjects();
      const linkedProjects = allProjects.filter(p => 
        p.module_type === 'code' && p.parent_dossier_id === parseInt(projectId)
      );
      
      const container = document.getElementById('code-projects-list');
      
      if (linkedProjects.length === 0) {
        container.innerHTML = '<p class="text-muted" style="padding:1rem">Aucun projet code associé.</p>';
        return;
      }
      
      const categoryColors = {
        'applications_mobile': '#3b82f6',
        'applications_web': '#10b981',
        'Clients': '#f59e0b',
        'intelligence_artificielle': '#8b5cf6'
      };
      
      container.innerHTML = linkedProjects.map(p => {
        const categoryColor = categoryColors[p.category] || '#6b7280';
        return `
          <div class="conversation-item card card--interactive" onclick="location.href='code-project-detail.html?id=${p.id}'">
            <div class="conversation-item-icon">⚙️</div>
            <div class="conversation-item-content">
              <div class="conversation-item-title">${p.name}</div>
              <div class="conversation-item-meta">
                <span class="badge" style="background-color:${categoryColor}20;color:${categoryColor};border:1px solid ${categoryColor}40;font-size:0.75rem">
                  ${p.category}
                </span>
                <span class="text-muted" style="font-size:0.875rem;font-family:monospace">${p.path}</span>
              </div>
            </div>
          </div>
        `;
      }).join('');
      
    } catch (error) {
      console.error('Erreur chargement projets code liés:', error);
      document.getElementById('code-projects-list').innerHTML = '<p class="text-muted" style="padding:1rem">Erreur de chargement</p>';
    }
  }

  async function showAssociateCodeProjectModal() {
    try {
      const allProjects = await window.API.getProjects();
      const unlinkedProjects = allProjects.filter(p => 
        p.module_type === 'code' && !p.parent_dossier_id
      );
      
      if (unlinkedProjects.length === 0) {
        if (window.showToast) window.showToast('Aucun projet code disponible à associer', 'info');
        return;
      }
      
      const options = unlinkedProjects.map(p => 
        `<option value="${p.id}">${p.name} (${p.category})</option>`
      ).join('');
      
      const bodyHTML = `
        <div style="margin-bottom:1rem">
          <label style="display:block;margin-bottom:0.5rem;font-weight:500;color:var(--text-primary)">
            Sélectionner un projet code :
          </label>
          <select id="select-code-project" class="input-field" style="width:100%">
            ${options}
          </select>
        </div>
      `;
      
      if (window.showModal) {
        window.showModal(
          'Associer un Projet Code',
          bodyHTML,
          [
            {
              label: 'Associer',
              type: 'primary',
              onClick: async () => {
                const selectedId = parseInt(document.getElementById('select-code-project').value);
                await associateCodeProject(selectedId);
              }
            },
            {
              label: 'Annuler',
              type: 'secondary',
              onClick: () => {
                if (window.closeModal) window.closeModal();
              }
            }
          ]
        );
      }
      
    } catch (error) {
      console.error('Erreur affichage modal:', error);
      if (window.showToast) window.showToast('Erreur', 'error');
    }
  }

  async function associateCodeProject(codeProjectId) {
    try {
      await window.API.updateProject(codeProjectId, { parent_dossier_id: parseInt(projectId) });
      if (window.showToast) window.showToast('Projet code associé', 'success');
      if (window.closeModal) window.closeModal();
      await loadLinkedCodeProjects();
    } catch (error) {
      console.error('Erreur association projet:', error);
      if (window.showToast) window.showToast('Erreur d\'association', 'error');
    }
  }

  function initializeExplorer() {
    if (project.local_path && project.local_path.trim()) {
      const explorer = document.getElementById('explorer');
      if (explorer) {
        explorer.classList.remove('explorer--hidden');
      }
      
      if (window.initExplorer) {
        window.initExplorer(projectId);
      }
    }
  }
})();
