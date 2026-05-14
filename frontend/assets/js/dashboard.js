(function() {
  let allProjects = [];
  let allConversations = [];
  let allSessions = [];
  let allAtelierProspects = [];
  let allReflexions = [];
  let allSentinelleCycles = [];
  let currentPeriod = 'today';

  document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardData();
    renderDashboard();
    attachEventListeners();
  });

  async function loadDashboardData() {
    try {
      const [projects, conversations, atelierProspects, sentinelleCycles] = await Promise.all([
        window.API.getProjects(),
        window.API.getConversations(),
        window.API.getProspects().catch(() => []),
        window.API.getSentinelleCyclesRecent().catch(() => [])
      ]);

      allProjects = projects;
      allConversations = conversations;
      allAtelierProspects = atelierProspects;
      allSentinelleCycles = sentinelleCycles;

      const sessionPromises = projects.map(p => 
        window.API.getProjectSessions(p.id).catch(() => [])
      );
      const sessionsArrays = await Promise.all(sessionPromises);
      allSessions = sessionsArrays.flat();

      const reflexionPromises = projects.map(p => 
        window.API.getReflexions(p.id).catch(() => [])
      );
      const reflexionsArrays = await Promise.all(reflexionPromises);
      allReflexions = reflexionsArrays.flat();

    } catch (error) {
      console.error('Erreur chargement dashboard:', error);
      window.showToast('Erreur de chargement', 'error');
    }
  }

  function renderDashboard() {
    renderStats();
    renderActivePipelines();
    renderTimeline();
    updateSubtitle();
  }

  function renderActivePipelines() {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    // Filtrer les sessions actives (exclure COMPLETED, ABORTED et sessions Atelier)
    const activeSessions = allSessions.filter(s => {
      // Exclure les sessions terminées
      if (['COMPLETED', 'ABORTED'].includes(s.status)) return false;
      // Exclure les sessions Atelier (gérées via prospects)
      if (s.workflow_type && s.workflow_type.startsWith('atelier_')) return false;
      return true;
    });

    // WAITING_VALIDATION : Module Code uniquement (pas Atelier)
    const waitingModuleSessions = activeSessions.filter(s => s.status === 'WAITING_VALIDATION');

    // WAITING_VALIDATION : Atelier
    const waitingAtelierProspects = allAtelierProspects.filter(p => p.session_status === 'WAITING_VALIDATION');

    // RUNNING : Module Code uniquement
    const runningSessions = activeSessions.filter(s => s.status === 'RUNNING');

    // Créées récemment (< 1h) mais pas encore RUNNING (en démarrage)
    const startingSessions = activeSessions.filter(s => {
      if (s.status !== 'CREATED') return false;
      return new Date(s.created_at) > oneHourAgo;
    });

    // Bloquées (CREATED > 1h)
    const stuckSessions = activeSessions.filter(s => {
      if (['ERROR', 'FAILED', 'RUNNING', 'WAITING_VALIDATION'].includes(s.status)) return false;
      return new Date(s.created_at) <= oneHourAgo;
    });

    const hasAnything = waitingModuleSessions.length > 0 || waitingAtelierProspects.length > 0
      || runningSessions.length > 0 || startingSessions.length > 0 || stuckSessions.length > 0;

    const section = document.getElementById('active-pipeline-section');
    const list = document.getElementById('active-pipeline-list');

    if (!hasAnything) {
      section.style.display = 'none';
      return;
    }

    section.style.display = 'block';
    let html = '';

    // ── Partie 1 : En attente de TOI ──────────────────────────────
    const totalWaiting = waitingModuleSessions.length + waitingAtelierProspects.length;
    if (totalWaiting > 0) {
      html += `
        <div class="waiting-banner">
          <span class="waiting-banner-title">⏸️ ${totalWaiting} session${totalWaiting > 1 ? 's attendent' : ' attend'} ta validation</span>
        </div>
      `;

      // Afficher les sessions Module Code individuellement
      waitingModuleSessions.forEach(s => {
        const project = allProjects.find(p => p.id === s.project_id);
        const projectName = project ? project.name : 'Sans projet';
        html += `
          <div class="active-pipeline-card card card--waiting">
            <div class="active-pipeline-info">
              <span style="color:#f59e0b">⏸️</span>
              <strong>${s.workflow_type}</strong>
              <span class="text-muted">· ${projectName} · Step ${s.current_step_index + 1}</span>
            </div>
            <a href="mission.html?pipeline_session=${s.id}&project_id=${s.project_id}" class="btn-primary btn-sm">→ Valider</a>
          </div>
        `;
      });

      // Afficher UNE carte condensée pour tous les prospects Atelier
      if (waitingAtelierProspects.length > 0) {
        html += `
          <div class="active-pipeline-card card card--waiting" style="opacity:0.85">
            <div class="active-pipeline-info">
              <span style="color:#f59e0b">🏭</span>
              <strong>${waitingAtelierProspects.length} prospect${waitingAtelierProspects.length > 1 ? 's' : ''} Atelier en attente</strong>
            </div>
            <div style="display:flex;gap:8px;align-items:center">
              <a href="atelier.html" class="btn-secondary btn-sm">→ Atelier</a>
              <button class="btn-danger btn-sm" id="btn-purge-atelier">Tout supprimer</button>
            </div>
          </div>
        `;
      }
    }

    // ── Partie 2 : En cours (RUNNING) ─────────────────────────────
    const totalRunning = runningSessions.length + startingSessions.length;
    if (totalRunning > 0) {
      html += `<div class="running-section-title text-muted" style="font-size:0.8rem;padding:0.5rem 0 0.25rem">⚡ En cours</div>`;

      [...runningSessions, ...startingSessions].forEach(s => {
        const project = allProjects.find(p => p.id === s.project_id);
        const projectName = project ? project.name : 'Sans projet';
        html += `
          <div class="active-pipeline-card card card--interactive">
            <div class="active-pipeline-info">
              <span class="active-dot"></span>
              <strong>${s.workflow_type}</strong>
              <span class="text-muted">· ${projectName} · Step ${s.current_step_index + 1}</span>
            </div>
            <div style="display:flex;gap:8px;align-items:center">
              <a href="mission.html?pipeline_session=${s.id}&project_id=${s.project_id}" class="btn-secondary btn-sm">→ Voir</a>
              <button class="btn-danger btn-sm" onclick="abandonSession(${s.id})">Abandonner</button>
            </div>
          </div>
        `;
      });
    }

    // ── Cycles Sentinelle actifs ──────────────────────────────────
    const activeSentinelleCycles = allSentinelleCycles.filter(c => c.etat !== 'CLOTURE');
    if (activeSentinelleCycles.length > 0) {
      activeSentinelleCycles.forEach(cycle => {
        html += `
          <div class="active-pipeline-card card card--interactive">
            <div class="active-pipeline-info">
              <span>🛡</span>
              <strong>Cycle Sentinelle en cours</strong>
              <span class="text-muted">· Mois ${cycle.mois}</span>
            </div>
            <a href="sentinelle.html" class="btn-secondary btn-sm">→ Voir</a>
          </div>
        `;
      });
    }

    // ── Sessions bloquées ──────────────────────────────────────────
    if (stuckSessions.length > 0) {
      html += `
        <div class="stuck-sessions">
          <div class="stuck-sessions-header" onclick="toggleStuckSessions()" style="display:flex;align-items:center;gap:0.5rem">
            <span class="text-muted" style="font-size:0.85rem">⚠️ ${stuckSessions.length} session(s) bloquée(s)</span>
            <button class="btn-danger btn-sm" id="btn-abandon-all-stuck" style="margin-left:auto">Tout abandonner</button>
            <span id="stuck-sessions-toggle" style="color:var(--text-muted)">▼</span>
          </div>
          <div id="stuck-sessions-list" style="display:none">
      `;
      stuckSessions.forEach(s => {
        const project = allProjects.find(p => p.id === s.project_id);
        const projectName = project ? project.name : 'Sans projet';
        const daysAgo = Math.floor((now - new Date(s.created_at)) / (1000 * 60 * 60 * 24));
        html += `
          <div class="active-pipeline-card card" style="opacity:0.7">
            <div class="active-pipeline-info">
              <span style="color:var(--warning)">⚠️</span>
              <span class="text-muted">${s.workflow_type} · ${projectName} · il y a ${daysAgo}j</span>
            </div>
            <button class="btn-danger btn-sm" onclick="abandonSession(${s.id})">Abandonner</button>
          </div>
        `;
      });
      html += '</div></div>';
    }

    list.innerHTML = html;

    const btnAbandonAll = document.getElementById('btn-abandon-all-stuck');
    if (btnAbandonAll) {
      btnAbandonAll.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!confirm(`Abandonner les ${stuckSessions.length} sessions bloquées ?\n\nCette action est irréversible.`)) return;
        try {
          await Promise.all(stuckSessions.map(s => window.API.abortPipeline(s.id)));
          window.showToast && window.showToast('Sessions abandonnées', 'success');
          await loadDashboardData();
          renderDashboard();
        } catch(err) {
          window.showToast && window.showToast('Erreur : ' + err.message, 'error');
        }
      });
    }

    const btnPurgeAtelier = document.getElementById('btn-purge-atelier');
    if (btnPurgeAtelier) {
      btnPurgeAtelier.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!confirm(`Supprimer les ${waitingAtelierProspects.length} prospects Atelier en attente ?\n\nCette action est irréversible.`)) return;
        try {
          await Promise.all(waitingAtelierProspects.map(p => window.API.deleteProspect(p.id)));
          window.showToast && window.showToast('Prospects supprimés', 'success');
          await loadDashboardData();
          renderDashboard();
        } catch(err) {
          window.showToast && window.showToast('Erreur : ' + err.message, 'error');
        }
      });
    }
  }

  function renderTimeline() {
    const timeline = buildTimeline();
    const filtered = filterByPeriod(timeline, currentPeriod);
    
    const container = document.getElementById('activity-timeline');
    
    if (filtered.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem">Aucune activité pour cette période</p>';
      return;
    }

    container.innerHTML = filtered.map(item => renderTimelineItem(item)).join('');
  }

  function buildTimeline() {
    const items = [];

    allConversations.forEach(conv => {
      const project = allProjects.find(p => p.id === conv.project_id);
      items.push({
        type: 'chat',
        id: conv.id,
        title: conv.title || 'Conversation sans titre',
        project_id: conv.project_id,
        project_name: project ? project.name : null,
        date: conv.last_message_at || conv.created_at,
        preview: conv.last_message_preview || '',
        href: `chat.html?id=${conv.id}${conv.project_id ? '&project_id=' + conv.project_id : ''}`
      });
    });

    allSessions.forEach(session => {
      const project = allProjects.find(p => p.id === session.project_id);
      items.push({
        type: 'module',
        id: session.id,
        title: session.workflow_type,
        project_id: session.project_id,
        project_name: project ? project.name : null,
        date: session.updated_at || session.created_at,
        status: session.status,
        cost: session.total_cost_usd || 0,
        href: `mission.html?pipeline_session=${session.id}&project_id=${session.project_id}`
      });
    });

    allReflexions.forEach(r => {
      const project = allProjects.find(p => p.id === r.project_id);
      items.push({
        type: 'reflexion',
        id: r.id,
        title: r.titre || 'Réflexion #' + r.id,
        project_id: r.project_id,
        project_name: project ? project.name : null,
        date: r.updated_at || r.created_at,
        status: r.statut,
        href: `mission.html?session=${r.id}&project_id=${r.project_id}`
      });
    });

    allSentinelleCycles.forEach(cycle => {
      items.push({
        type: 'sentinelle',
        id: cycle.id,
        title: `Cycle Sentinelle ${cycle.mois}`,
        date: cycle.updated_at || cycle.created_at,
        status: cycle.etat,
        href: 'sentinelle.html'
      });
    });

    items.sort((a, b) => new Date(b.date) - new Date(a.date));
    return items;
  }

  function filterByPeriod(items, period) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    return items.filter(item => {
      const itemDate = new Date(item.date);
      
      if (period === 'today') {
        return itemDate >= today;
      } else if (period === 'yesterday') {
        return itemDate >= yesterday && itemDate < today;
      } else if (period === 'week') {
        return itemDate >= weekAgo;
      }
      return true;
    });
  }

  function renderTimelineItem(item) {
    let icon = '💬';
    if (item.type === 'module') icon = '⚙️';
    if (item.type === 'reflexion') icon = '🧠';
    if (item.type === 'sentinelle') icon = '🛡';
    
    const projectLabel = item.project_name || 'Sans projet';
    const dateStr = window.formatDate ? window.formatDate(item.date) : new Date(item.date).toLocaleString('fr-FR');
    
    let metaHTML = `
      <span class="timeline-project">${projectLabel}</span>
      <span class="timeline-date">${dateStr}</span>
    `;

    if (item.type === 'module') {
      metaHTML += window.statusBadge ? window.statusBadge(item.status) : `<span class="badge badge--${item.status.toLowerCase()}">${item.status}</span>`;
      if (item.cost > 0) {
        metaHTML += window.costBadge ? window.costBadge(item.cost) : `<span class="badge badge--cost">$${item.cost.toFixed(4)}</span>`;
      }
    }

    if (item.type === 'reflexion') {
      const statusLabels = {
        'OUVERTE': '● Ouverte',
        'EN_FIGEMENT': '⏳ En figement',
        'FIGEE': '🔒 Figée',
        'ABANDONNEE': '✕ Abandonnée'
      };
      const statusLabel = statusLabels[item.status] || item.status;
      metaHTML += `<span class="badge badge--${item.status.toLowerCase()}">${statusLabel}</span>`;
    }

    if (item.type === 'sentinelle') {
      const statusLabels = {
        'PHASE_1': 'Phase 1',
        'PHASE_2': 'Veille',
        'PHASE_3': 'Analyse',
        'PHASE_4': 'Décision',
        'PHASE_5': 'Ordre',
        'PHASE_6': 'Récap',
        'CLOTURE': 'Clôturé'
      };
      const statusLabel = statusLabels[item.status] || item.status;
      metaHTML += `<span class="badge badge--${item.status === 'CLOTURE' ? 'completed' : 'running'}">${statusLabel}</span>`;
    }

    let previewHTML = '';
    if (item.type === 'chat' && item.preview) {
      const truncated = item.preview.length > 80 ? item.preview.substring(0, 80) + '...' : item.preview;
      previewHTML = `<div class="timeline-preview">${truncated}</div>`;
    }

    return `
      <div class="timeline-item timeline-item--${item.type}" onclick="location.href='${item.href}'">
        <div class="timeline-icon">${icon}</div>
        <div class="timeline-content">
          <div class="timeline-title">${item.title}</div>
          <div class="timeline-meta">${metaHTML}</div>
          ${previewHTML}
        </div>
      </div>
    `;
  }

  function renderStats() {
    const timeline = buildTimeline();
    const filteredItems = filterByPeriod(timeline, currentPeriod);
    
    const sessionsCount = filteredItems.filter(i => i.type === 'module' || i.type === 'reflexion' || i.type === 'sentinelle').length;
    const chatsCount = filteredItems.filter(i => i.type === 'chat').length;
    const totalCost = filteredItems
      .filter(i => i.type === 'module')
      .reduce((sum, i) => sum + (i.cost || 0), 0);

    // Stats Module Code : missions lancées selon période
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);
    const monthAgo = new Date(today);
    monthAgo.setMonth(monthAgo.getMonth() - 1);

    const missionsCodeCount = allSessions.filter(s => {
      if (s.workflow_type !== 'code_mission') return false;
      const createdDate = new Date(s.created_at);
      if (currentPeriod === 'today') return createdDate >= today;
      if (currentPeriod === 'week') return createdDate >= weekAgo;
      if (currentPeriod === 'month') return createdDate >= monthAgo;
      return true;
    }).length;

    // Stats Module Réflexion : sessions figées selon période
    const reflexionsFigeesCount = allReflexions.filter(r => {
      if (r.statut !== 'FIGEE') return false;
      if (!r.frozen_at) return false;
      const frozenDate = new Date(r.frozen_at);
      if (currentPeriod === 'today') return frozenDate >= today;
      if (currentPeriod === 'week') return frozenDate >= weekAgo;
      if (currentPeriod === 'month') return frozenDate >= monthAgo;
      return true;
    }).length;

    const periodLabel = currentPeriod === 'today' ? "aujourd'hui" : currentPeriod === 'week' ? 'cette semaine' : 'ce mois';

    const container = document.getElementById('dashboard-stats');
    container.innerHTML = `
      <div class="stat-card card">
        <div class="stat-value">${sessionsCount}</div>
        <div class="stat-label">Sessions ${periodLabel}</div>
      </div>
      <div class="stat-card card">
        <div class="stat-value">${chatsCount}</div>
        <div class="stat-label">Conversations ${periodLabel}</div>
      </div>
      <div class="stat-card card">
        <div class="stat-value">${missionsCodeCount}</div>
        <div class="stat-label">Missions code</div>
      </div>
      <div class="stat-card card">
        <div class="stat-value">${reflexionsFigeesCount}</div>
        <div class="stat-label">Réflexions figées</div>
      </div>
      <div class="stat-card card">
        <div class="stat-value">$${totalCost.toFixed(3)}</div>
        <div class="stat-label">Coût ${periodLabel}</div>
      </div>
    `;
  }

  function updateSubtitle() {
    const timeline = buildTimeline();
    const filtered = filterByPeriod(timeline, currentPeriod);
    
    const sessionsCount = filtered.filter(i => i.type === 'module' || i.type === 'reflexion' || i.type === 'sentinelle').length;
    const chatsCount = filtered.filter(i => i.type === 'chat').length;
    const totalCost = filtered
      .filter(i => i.type === 'module')
      .reduce((sum, i) => sum + (i.cost || 0), 0);

    const subtitle = document.getElementById('dashboard-subtitle');
    
    if (filtered.length === 0) {
      subtitle.textContent = currentPeriod === 'today' 
        ? 'Aucune activité aujourd\'hui' 
        : 'Aucune activité pour cette période';
      return;
    }

    const parts = [];
    if (sessionsCount > 0) parts.push(`${sessionsCount} session${sessionsCount > 1 ? 's' : ''}`);
    if (chatsCount > 0) parts.push(`${chatsCount} chat${chatsCount > 1 ? 's' : ''}`);
    if (totalCost > 0) parts.push(`$${totalCost.toFixed(3)}`);
    subtitle.textContent = parts.length > 0 ? parts.join(' · ') : (currentPeriod === 'today' ? 'Aucune activité aujourd\'hui' : 'Aucune activité pour cette période');
  }

  function attachEventListeners() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        filterButtons.forEach(b => b.classList.remove('filter-btn--active'));
        btn.classList.add('filter-btn--active');
        currentPeriod = btn.dataset.period;
        renderTimeline();
        renderStats();
        updateSubtitle();
      });
    });
  }

  window.abandonSession = async function(sessionId) {
    if (!confirm('Abandonner cette session ?')) return;
    try {
      await window.API.abortPipeline(sessionId);
      window.showToast('Session abandonnée');
      await loadDashboardData();
      renderDashboard();
    } catch(e) {
      window.showToast('Erreur: ' + e.message, 'error');
    }
  };

  window.toggleStuckSessions = function() {
    const list = document.getElementById('stuck-sessions-list');
    const toggle = document.getElementById('stuck-sessions-toggle');
    if (list.style.display === 'none') {
      list.style.display = 'block';
      toggle.textContent = '▲';
    } else {
      list.style.display = 'none';
      toggle.textContent = '▼';
    }
  };
})();
