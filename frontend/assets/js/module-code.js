(function() {
  let sessionId = null;
  let projectId = null;
  let pollInterval = null;
  let lastStatus = null;
  let currentSession = null;

  document.addEventListener('DOMContentLoaded', async () => {
    sessionId = window.getURLParam ? window.getURLParam('session') : new URLSearchParams(location.search).get('session');
    projectId = window.getURLParam ? window.getURLParam('project_id') : new URLSearchParams(location.search).get('project_id');

    if (!sessionId) {
      document.getElementById('page-module-code').innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center">Session non trouvée</p>';
      return;
    }

    await loadSession();

    if (projectId && window.initExplorer) {
      await window.initExplorer(projectId);
    }
  });

  async function loadSession() {
    try {
      const session = await window.API.getPipeline(sessionId);
      currentSession = session;
      renderSession(session);

      const ACTIVE_STATUSES = ['CREATED', 'RUNNING', 'WAITING', 'PENDING', 'WAITING_VALIDATION'];
      if (ACTIVE_STATUSES.includes(session.status)) {
        startPolling();
      } else if (['COMPLETED', 'ABORTED', 'ERROR'].includes(session.status)) {
        stopPolling();
      }
    } catch (error) {
      console.error('Erreur chargement session:', error);
      if (window.showToast) window.showToast('Erreur de chargement', 'error');
    }
  }

  function startPolling() {
    if (pollInterval) return;
    
    pollInterval = setInterval(async () => {
      try {
        const session = await window.API.getPipeline(sessionId);
        currentSession = session;
        renderSession(session);
        
        if (['COMPLETED', 'ABORTED', 'ERROR'].includes(session.status)) {
          stopPolling();
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    }, 2000);
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  }

  function renderSession(session) {
    renderHeader(session);
    renderSteps(session);
    renderActionZone(session);
  }

  async function renderHeader(session) {
    const workflowType = session.workflow_type.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    document.getElementById('mc-workflow-type').textContent = workflowType;

    const statusBadge = window.statusBadge ? window.statusBadge(session.status) : `<span class="badge">${session.status}</span>`;
    document.getElementById('mc-status-badge').innerHTML = statusBadge;

    // Afficher l'objectif initial
    const objectiveEl = document.getElementById('mc-objective');
    if (objectiveEl) {
        const rawInput = session.steps?.[0]?.input_data || '';
        let objectiveText = rawInput;
        if (rawInput && rawInput.trim().startsWith('{')) {
            try {
                const parsed = JSON.parse(rawInput);
                objectiveText = parsed.description || parsed.objective || parsed.input || rawInput;
            } catch(e) {}
        }
        if (objectiveText && objectiveText.length > 0) {
            const preview = objectiveText.length > 200 
                ? objectiveText.substring(0, 200) + '...' 
                : objectiveText;
            objectiveEl.innerHTML = `🎯 <em>${preview}</em>`;
            objectiveEl.style.display = 'block';
        }
    }

    const formatDate = window.formatDate || ((d) => new Date(d).toLocaleString('fr-FR'));
    document.getElementById('mc-start-time').textContent = formatDate(session.created_at);

    if (projectId) {
      try {
        const project = await window.API.getProject(projectId);
        document.getElementById('mc-project-link').innerHTML = `<a href="dossier.html?id=${projectId}" style="color:var(--accent);text-decoration:none">📁 ${project.name}</a>`;
      } catch (e) {
        console.warn('Projet non trouvé:', e);
      }
    }

    if (['COMPLETED', 'ABORTED', 'ERROR'].includes(session.status)) {
      try {
        const costs = await window.API.getPipelineCosts(sessionId);
        const totalCost = costs.total_cost_usd || 0;
        const costBadge = window.costBadge ? window.costBadge(totalCost) : `<span class="badge">$${totalCost.toFixed(4)}</span>`;
        document.getElementById('mc-total-cost').innerHTML = costBadge;
      } catch (e) {
        console.warn('Coûts non disponibles:', e);
      }
    }

    const btnAbort = document.getElementById('btn-abort');
    if (['COMPLETED', 'ABORTED', 'ERROR'].includes(session.status)) {
      btnAbort.style.display = 'none';
    } else {
      btnAbort.style.display = 'block';
      btnAbort.onclick = handleAbort;
    }
  }

  function renderSteps(session) {
    const container = document.getElementById('mc-steps-list');
    
    if (!session.steps || session.steps.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem">Aucun step</p>';
      return;
    }

    const sortedSteps = [...session.steps].sort((a, b) => a.step_index - b.step_index);
    container.innerHTML = sortedSteps.map(step => renderStepCard(step)).join('');
  }

  function renderStepCard(step) {
    const statusClass = getStepStatusClass(step.status);
    const indicator = getStepIndicator(step.status);
    
    let metaHTML = '';
    if (step.model_used || step.model_type) {
      metaHTML = `<span class="text-muted">${step.model_used || step.model_type}</span>`;
    }

    let outputHTML = '';
    if (step.status === 'COMPLETED' && step.output_data) {
      const preview = typeof step.output_data === 'string' 
        ? step.output_data.substring(0, 120) 
        : JSON.stringify(step.output_data).substring(0, 120);
      outputHTML = `<div class="step-output">${preview}${preview.length >= 120 ? '...' : ''}</div>`;
    }

    let errorHTML = '';
    if (step.status === 'ERROR' && step.error_message) {
      errorHTML = `<div class="step-error">❌ ${step.error_message}</div>`;
    }

    let buttonsHTML = '';
    if (step.status === 'ERROR') {
      buttonsHTML = `<button class="btn-icon" onclick="window.retryStep(${step.id})" title="Relancer">🔄</button>`;
    }

    return `
      <div class="step-card ${statusClass}" data-step-id="${step.id}">
        <div class="step-card-left">
          <div class="step-indicator">${indicator}</div>
          <div class="step-index">${step.step_index + 1}</div>
        </div>
        <div class="step-card-body">
          <div class="step-name">${step.step_display_name || step.step_type}</div>
          <div class="step-meta">${metaHTML}</div>
          ${outputHTML}
          ${errorHTML}
        </div>
        <div class="step-card-right">
          ${buttonsHTML}
        </div>
      </div>
    `;
  }

  function getStepStatusClass(status) {
    const map = {
      'PENDING': 'step-card--pending',
      'RUNNING': 'step-card--running',
      'COMPLETED': 'step-card--completed',
      'ERROR': 'step-card--error',
      'WAITING_VALIDATION': 'step-card--waiting'
    };
    return map[status] || '';
  }

  function getStepIndicator(status) {
    const map = {
      'PENDING': '<span style="color:var(--text-muted)">○</span>',
      'RUNNING': '<div class="spinner"></div>',
      'COMPLETED': '✅',
      'ERROR': '❌',
      'WAITING_VALIDATION': '⏸️'
    };
    return map[status] || '○';
  }

  function renderActionZone(session) {
    const actionZone = document.getElementById('mc-action-zone');

    // Cas terminal : session terminée, abandonnée ou en erreur
    const TERMINAL = ['COMPLETED', 'ABORTED', 'ERROR', 'FAILED'];
    if (TERMINAL.includes(session.status)) {
      actionZone.style.display = 'block';
      const isSuccess = session.status === 'COMPLETED';
      const emoji = isSuccess ? '✅' : '❌';
      const label = {
        COMPLETED: 'Session terminée avec succès',
        ABORTED: 'Session abandonnée',
        ERROR: 'Session en erreur',
        FAILED: 'Session échouée'
      }[session.status] || session.status;

      const backBtn = projectId
        ? `<a href="dossier.html?id=${projectId}" class="btn-secondary">📁 Retour au dossier</a>` 
        : `<a href="index.html" class="btn-secondary">🏠 Tableau de bord</a>`;

      const relanceBtn = !isSuccess && projectId && currentSession
        ? `<button class="btn-secondary" onclick="window._relancerSession()">🔄 Relancer ce workflow</button>` 
        : '';

      const nouvelleBtn = projectId
        ? `<button class="btn-primary" onclick="window._nouvelleSession()">⚡ Nouvelle session</button>` 
        : '';

      const deleteBtn = `<button class="btn-danger" onclick="window._deleterSession()" 
                    style="margin-left:auto">🗑 Supprimer cette session</button>`;

      actionZone.innerHTML = `
        <div class="mc-action-header">
          <h3>${emoji} ${label}</h3>
        </div>
        <div class="mc-validation-actions">
          ${backBtn}
          ${relanceBtn}
          ${nouvelleBtn}
          ${deleteBtn}
        </div>
      `;
      return;
    }
    
    const waitingStep = session.steps?.find(s => s.status === 'WAITING_VALIDATION');
    
    if (!waitingStep || !waitingStep.requires_validation) {
      actionZone.style.display = 'none';
      return;
    }

    actionZone.style.display = 'block';

    if (waitingStep.output_type === 'diff') {
      actionZone.innerHTML = renderDiffValidation(waitingStep);
    } else {
      actionZone.innerHTML = renderGenericValidation(waitingStep);
    }

    attachValidationHandlers(waitingStep);
  }

  function renderDiffValidation(step) {
    const renderDiffFn = window.renderDiff || ((text) => `<pre>${text}</pre>`);
    const diffContent = typeof step.output_data === 'string'
      ? renderDiffFn(step.output_data)
      : `<pre>${JSON.stringify(step.output_data, null, 2)}</pre>`;

    return `
      <div class="mc-action-header">
        <h3>⏸️ ${step.step_display_name || step.step_type} — Validation requise</h3>
        <p class="text-muted">L'IA propose les modifications suivantes :</p>
      </div>
      <div class="mc-diff-container">
        ${diffContent}
      </div>
      <div class="mc-validation-form">
        <label>Feedback (optionnel)</label>
        <textarea id="mc-feedback-input" placeholder="Commentaires pour l'IA..." rows="2"></textarea>
        <div class="mc-validation-actions">
          <button id="btn-approve" class="btn-primary">✅ Approuver et continuer</button>
          <button id="btn-reject" class="btn-danger">❌ Rejeter</button>
        </div>
      </div>
    `;
  }

  function renderGenericValidation(step) {
    const renderMarkdown = window.renderMarkdown || ((text) => `<pre>${text}</pre>`);
    let outputHTML = '';
    
    if (step.output_data) {
      const content = typeof step.output_data === 'string' 
        ? step.output_data 
        : JSON.stringify(step.output_data, null, 2);
      outputHTML = `<div class="mc-output-preview">${renderMarkdown(content)}</div>`;
    }

    return `
      <div class="mc-action-header">
        <h3>⏸️ ${step.step_display_name || step.step_type} — Validation requise</h3>
      </div>
      ${outputHTML}
      <div class="mc-validation-form">
        <label>Feedback (optionnel)</label>
        <textarea id="mc-feedback-input" placeholder="Commentaires..." rows="2"></textarea>
        <div class="mc-validation-actions">
          <button id="btn-approve" class="btn-primary">✅ Approuver et continuer</button>
          <button id="btn-reject" class="btn-danger">❌ Rejeter</button>
        </div>
      </div>
    `;
  }

  function attachValidationHandlers(step) {
    const btnApprove = document.getElementById('btn-approve');
    const btnReject = document.getElementById('btn-reject');

    if (btnApprove) {
      btnApprove.onclick = async () => {
        const feedback = document.getElementById('mc-feedback-input')?.value || '';
        await handleValidation(step.id, true, feedback);
      };
    }

    if (btnReject) {
      btnReject.onclick = async () => {
        const feedback = document.getElementById('mc-feedback-input')?.value || '';
        if (!feedback.trim()) {
          if (window.showToast) window.showToast('Un feedback est requis pour rejeter', 'warning');
          return;
        }
        await handleValidation(step.id, false, feedback);
      };
    }
  }

  async function handleValidation(stepId, approved, feedback) {
    disableValidationButtons();
    
    try {
      await window.API.validateStep(sessionId, stepId, { 
        approved, 
        feedback: feedback || '' 
      });
      await loadSession();
    } catch (error) {
      console.error('Erreur validation:', error);
      if (window.showToast) window.showToast(error.message || 'Erreur validation', 'error');
      enableValidationButtons();
    }
  }

  function disableValidationButtons() {
    const btnApprove = document.getElementById('btn-approve');
    const btnReject = document.getElementById('btn-reject');
    if (btnApprove) btnApprove.disabled = true;
    if (btnReject) btnReject.disabled = true;
  }

  function enableValidationButtons() {
    const btnApprove = document.getElementById('btn-approve');
    const btnReject = document.getElementById('btn-reject');
    if (btnApprove) btnApprove.disabled = false;
    if (btnReject) btnReject.disabled = false;
  }

  async function handleAbort() {
    if (!window.showModal) {
      if (!confirm('Abandonner le module code ? La session sera arrêtée définitivement.')) return;
      await performAbort();
      return;
    }

    window.showModal(
      'Abandonner le module code ?',
      'La session sera arrêtée définitivement.',
      [
        {
          label: 'Abandonner',
          type: 'danger',
          onClick: async () => {
            await performAbort();
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

  async function performAbort() {
    try {
      await window.API.abortPipeline(sessionId);
      if (window.showToast) window.showToast('Session abandonnée');
      if (window.closeModal) window.closeModal();
      await loadSession();
    } catch (error) {
      console.error('Erreur abandon:', error);
      if (window.showToast) window.showToast('Erreur abandon', 'error');
    }
  }

  window.retryStep = async function(stepId) {
    try {
      await window.API.retryStep(sessionId, stepId);
      if (window.showToast) window.showToast('Step relancé');
      await loadSession();
    } catch (error) {
      console.error('Erreur retry:', error);
      if (window.showToast) window.showToast('Erreur relance', 'error');
    }
  };

  window._relancerSession = function() {
    if (currentSession && projectId) {
      if (window.handleNewModulePreset) {
        window.handleNewModulePreset(projectId, currentSession.workflow_type);
      } else if (window.handleNewModule) {
        window.handleNewModule();
      }
    }
  };

  window._nouvelleSession = function() {
    if (window.handleNewModulePreset && projectId) {
      window.handleNewModulePreset(projectId, null);
    } else if (window.handleNewModule) {
      window.handleNewModule();
    }
  };

  window._deleterSession = async function() {
    if (!window.showModal) {
        if (!confirm('Supprimer définitivement cette session ?')) return;
    } else {
        window.showModal('Supprimer cette session ?', 
            'La session sera supprimée définitivement. Cette action est irréversible.',
            [
                { label: 'Supprimer', type: 'danger', onClick: async () => {
                    await _doDelete();
                }},
                { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() }
            ]
        );
        return;
    }
    await _doDelete();
  };

  async function _doDelete() {
    try {
        await window.API.deletePipeline(sessionId);
        if (window.closeModal) window.closeModal();
        if (window.showToast) window.showToast('Session supprimée');
        if (projectId) {
            window.location.href = `dossier.html?id=${projectId}`;
        } else {
            window.location.href = 'index.html';
        }
    } catch (error) {
        if (window.showToast) window.showToast('Erreur suppression', 'error');
    }
  }

  window.addEventListener('beforeunload', () => {
    stopPolling();
  });
})();
