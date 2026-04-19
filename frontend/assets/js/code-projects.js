(function() {
  let codeProjects = [];
  let dossiers = [];

  document.addEventListener('DOMContentLoaded', async () => {
    await loadCodeProjects();
    renderProjects();
    attachEventListeners();
  });

  async function loadCodeProjects() {
    try {
      codeProjects = await window.API.getProjects();
      codeProjects = codeProjects.filter(p => p.module_type === 'code');
      
      for (const project of codeProjects) {
        try {
          const [conversations, sessions] = await Promise.all([
            window.API.getConversations(project.id),
            window.API.getProjectSessions(project.id)
          ]);
          project._conversations_count = conversations.length;
          project._sessions_count = sessions.length;
          project._last_activity = getLastActivity(conversations, sessions);
        } catch (e) {
          project._conversations_count = 0;
          project._sessions_count = 0;
          project._last_activity = project.created_at;
        }
      }
    } catch (error) {
      console.error('Erreur chargement projets code:', error);
      if (window.showToast) window.showToast('Erreur de chargement', 'error');
    }
  }

  function getLastActivity(conversations, sessions) {
    const dates = [];
    conversations.forEach(c => dates.push(new Date(c.updated_at || c.created_at)));
    sessions.forEach(s => dates.push(new Date(s.updated_at || s.created_at)));
    if (dates.length === 0) return null;
    return new Date(Math.max(...dates)).toISOString();
  }

  function renderProjects() {
    const container = document.getElementById('code-projects-grid');
    
    if (codeProjects.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:3rem;grid-column:1/-1">Aucun projet code. Cliquez sur "+ Nouveau Projet" pour commencer.</p>';
      return;
    }

    codeProjects.sort((a, b) => {
      const dateA = new Date(a._last_activity || a.created_at);
      const dateB = new Date(b._last_activity || b.created_at);
      return dateB - dateA;
    });

    container.innerHTML = codeProjects.map(project => renderProjectCard(project)).join('');
  }

  function renderProjectCard(project) {
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

    const categoryColor = categoryColors[project.category] || '#6b7280';
    const categoryLabel = categoryLabels[project.category] || project.category;
    
    const formatDate = window.formatDate || ((d) => new Date(d).toLocaleString('fr-FR'));
    const lastActivity = project._last_activity 
      ? formatDate(project._last_activity)
      : formatDate(project.created_at);

    return `
      <div class="code-project-card card card--interactive" onclick="location.href='code-project-detail.html?id=${project.id}'">
        <div class="code-project-card-header">
          <h3 class="code-project-card-title">${project.name}</h3>
          <span class="code-project-badge" style="background-color:${categoryColor}20;color:${categoryColor};border:1px solid ${categoryColor}40">
            ${categoryLabel}
          </span>
        </div>
        <div class="code-project-card-path">
          <span style="color:var(--text-muted);font-size:0.875rem;font-family:monospace">${project.path}</span>
        </div>
        <div class="code-project-card-stats">
          <span class="code-project-stat">💬 ${project._conversations_count}</span>
          <span class="code-project-stat">⚙️ ${project._sessions_count}</span>
          <span class="code-project-stat" style="color:var(--text-muted);font-size:0.8rem">${lastActivity}</span>
        </div>
      </div>
    `;
  }

  function attachEventListeners() {
    document.getElementById('btn-new-code-project').addEventListener('click', showNewProjectModal);
  }

  async function showNewProjectModal() {
    try {
      dossiers = await window.API.getProjects();
      dossiers = dossiers.filter(p => p.module_type === 'dossier');
    } catch (e) {
      dossiers = [];
    }

    let dossiersOptions = '<option value="">Aucun (optionnel)</option>';
    dossiers.forEach(d => {
      dossiersOptions += `<option value="${d.id}">${d.name}</option>`;
    });

    const modalHTML = `
      <div class="modal-header">
        <h2>Nouveau Projet Code</h2>
        <button class="modal-close" onclick="window.closeModal()">×</button>
      </div>
      <div class="modal-body">
        <div style="margin-bottom:1rem">
          <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary);font-weight:500">Nom du projet *</label>
          <input type="text" id="project-name" class="input-field" placeholder="MonProjet" required>
        </div>
        <div style="margin-bottom:1rem">
          <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary);font-weight:500">Catégorie *</label>
          <select id="project-category" class="input-field" required>
            <option value="">Sélectionner...</option>
            <option value="applications_mobile">Applications Mobile</option>
            <option value="applications_web">Applications Web</option>
            <option value="Clients">Clients</option>
            <option value="intelligence_artificielle">Intelligence Artificielle</option>
          </select>
        </div>
        <div style="margin-bottom:1rem">
          <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary);font-weight:500">Chemin auto-généré</label>
          <div id="path-preview" style="padding:0.5rem;background:var(--bg-secondary);border:1px solid var(--border);border-radius:6px;font-family:monospace;font-size:0.875rem;color:var(--text-muted);min-height:2.5rem;display:flex;align-items:center">
            Sélectionnez un nom et une catégorie
          </div>
        </div>
        <div style="margin-bottom:1rem">
          <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary);font-weight:500">
            Chemin personnalisé <span style="color:var(--text-muted);font-weight:400">(optionnel — remplace le chemin auto)</span>
          </label>
          <input type="text" id="path-override" class="input-field" 
                 placeholder="Ex: C:\\DEV\\CLIENTS\\MonClient\\AppMobile">
          <div style="margin-top:0.25rem;font-size:0.8rem;color:var(--text-muted)">
            Laissez vide pour utiliser le chemin auto-généré
          </div>
        </div>
        <div style="margin-bottom:1rem">
          <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary);font-weight:500">Dossier Jarvis associé</label>
          <select id="project-dossier" class="input-field">
            ${dossiersOptions}
          </select>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" onclick="window.closeModal()">Annuler</button>
        <button class="btn-primary" id="btn-create-project">Créer</button>
      </div>
    `;

    const overlay = document.getElementById('modal-overlay');
    const container = document.getElementById('modal-container');
    container.innerHTML = modalHTML;
    overlay.style.display = 'flex';

    document.getElementById('project-name').addEventListener('input', updatePathPreview);
    document.getElementById('project-category').addEventListener('change', updatePathPreview);
    document.getElementById('btn-create-project').addEventListener('click', handleCreateProject);
  }

  function updatePathPreview() {
    const name = document.getElementById('project-name').value.trim();
    const category = document.getElementById('project-category').value;
    const preview = document.getElementById('path-preview');
    
    if (name && category) {
      preview.textContent = `C:\\DEV\\PROJETS\\${category}\\${name}`;
      preview.style.color = 'var(--text-primary)';
    } else {
      preview.textContent = 'Sélectionnez un nom et une catégorie';
      preview.style.color = 'var(--text-muted)';
    }
  }

  async function handleCreateProject() {
    const name = document.getElementById('project-name').value.trim();
    const category = document.getElementById('project-category').value;
    const dossierId = document.getElementById('project-dossier').value;

    if (!name || !category) {
      if (window.showToast) window.showToast('Nom et catégorie requis', 'error');
      return;
    }
    const pathOverrideCheck = document.getElementById('path-override')?.value.trim() || '';
    if (pathOverrideCheck && !pathOverrideCheck.includes('\\') && !pathOverrideCheck.includes('/')) {
      if (window.showToast) window.showToast('Chemin personnalisé invalide — doit contenir \\ ou /', 'error');
      return;
    }

    const pathOverride = document.getElementById('path-override')?.value.trim() || '';
    const autoPath = `C:\\DEV\\PROJETS\\${category}\\${name}`;
    const finalPath = pathOverride || autoPath;

    const payload = {
      name: name,
      path: finalPath,
      type: 'code',
      module_type: 'code',
      category: category,
      parent_dossier_id: dossierId ? parseInt(dossierId) : null,
      local_path: finalPath,
      instructions: ''
    };

    try {
      const project = await window.API.createProject(payload);
      if (window.closeModal) window.closeModal();
      if (window.showToast) window.showToast(`Projet "${name}" créé`);
      location.href = `code-project-detail.html?id=${project.id}`;
    } catch (error) {
      console.error('Erreur création projet:', error);
      if (window.showToast) window.showToast(error.message || 'Erreur création projet', 'error');
    }
  }

  window.closeModal = function() {
    const overlay = document.getElementById('modal-overlay');
    overlay.style.display = 'none';
  };
})();
