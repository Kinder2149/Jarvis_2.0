(function () {
  // ── État ────────────────────────────────────────────────────────────
  let currentProspectId = null;
  let currentSessionId = null;
  let pollInterval = null;
  let attachedImageSaisie = null;

  // Colonnes kanban (ordre affiché)
  const KANBAN_COLS = [
    { key: 'identifie',   label: 'Identifié',   color: '#64748b' },
    { key: 'en_analyse',  label: 'En analyse',  color: '#6366f1' },
    { key: 'demo_ok',     label: 'Démo OK',     color: '#f59e0b' },
    { key: 'contacte',    label: 'Contacté',    color: '#3b82f6' },
    { key: 'relance',     label: 'Relancé',     color: '#f97316' },
    { key: 'conclu',      label: 'Conclu',      color: '#22c55e' },
  ];

  // ── Init ─────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', async () => {
    const prospectId = window.getURLParam('prospect_id');
    if (prospectId) {
      currentProspectId = parseInt(prospectId);
      await showPipelineView(currentProspectId);
    } else {
      await showProspectsView();
    }

    document.getElementById('btn-new-prospect')?.addEventListener('click', handleNewProspect);
    document.getElementById('btn-reset-atelier')?.addEventListener('click', handleResetAtelier);
    document.getElementById('btn-back-kanban')?.addEventListener('click', () => {
      stopPolling();
      window.location.href = 'atelier.html';
    });

    // Event delegation kanban (une seule fois)
    const kanbanBoard = document.getElementById('kanban-board');
    if (kanbanBoard && !kanbanBoard._delegated) {
      kanbanBoard._delegated = true;
      kanbanBoard.addEventListener('click', async (e) => {
        // Clic sur carte prospect
        const card = e.target.closest('.prospect-card');
        if (card && !e.target.closest('.btn-prospect-delete')) {
          const id = parseInt(card.dataset.id);
          window.location.href = `atelier.html?prospect_id=${id}`;
          return;
        }
        // Clic sur bouton suppression
        const deleteBtn = e.target.closest('.btn-prospect-delete');
        if (deleteBtn) {
          e.stopPropagation();
          const id = parseInt(deleteBtn.dataset.id);
          const prospectCard = deleteBtn.closest('.prospect-card');
          const prospectName = prospectCard?.querySelector('.prospect-name')?.textContent?.trim() || 'ce prospect';
          if (!confirm(`Supprimer "${prospectName}" et toute sa progression ?\n\nCette action est irréversible.`)) return;
          try {
            await window.API.deleteProspect(id);
            window.showToast && window.showToast('Prospect supprimé', 'success');
            await loadKanban();
          } catch (err) {
            window.showToast && window.showToast('Erreur suppression: ' + err.message, 'error');
          }
        }
      });
    }
  });

  // ── Vue Prospects ─────────────────────────────────────────────
  async function showProspectsView() {
    document.getElementById('view-prospects').style.display = '';
    document.getElementById('view-pipeline').style.display = 'none';
    await loadKanban();
  }

  async function loadKanban() {
    try {
      const prospects = await window.API.getProspects();
      renderKanban(prospects);
    } catch (e) {
      document.getElementById('kanban-board').innerHTML =
        '<p style="color:var(--danger);padding:2rem">Erreur chargement prospects</p>';
    }
  }

  function renderKanban(prospects) {
    const board = document.getElementById('kanban-board');

    // Regrouper par statut
    const byStatus = {};
    KANBAN_COLS.forEach(col => { byStatus[col.key] = []; });
    prospects.forEach(p => {
      const key = p.statut || 'identifie';
      if (!byStatus[key]) byStatus[key] = [];
      byStatus[key].push(p);
    });

    board.innerHTML = KANBAN_COLS.map(col => `
      <div class="kanban-col">
        <div class="kanban-col-header" style="border-top:3px solid ${col.color}">
          <span class="kanban-col-title">${col.label}</span>
          <span class="kanban-col-count">${byStatus[col.key].length}</span>
        </div>
        <div class="kanban-col-body" data-status="${col.key}">
          ${byStatus[col.key].map(p => renderProspectCard(p)).join('')}
          ${byStatus[col.key].length === 0 ? '<div class="kanban-empty">—</div>' : ''}
        </div>
      </div>
    `).join('');

    // Event listeners gérés par delegation (voir DOMContentLoaded)
  }

  function getSessionIndicator(sessionStatus) {
    const map = {
      'WAITING_VALIDATION': '<span title="En attente de validation" style="color:#f59e0b">⏸️</span> ',
      'RUNNING': '<span title="IA en cours..." class="session-running-icon" style="color:#6366f1">⚙️</span> ',
      'COMPLETED': '<span title="Terminé" style="color:#22c55e">✅</span> ',
      'FAILED': '<span title="Erreur" style="color:#ef4444">❌</span> ',
      'ERROR': '<span title="Erreur" style="color:#ef4444">❌</span> ',
      'ABORTED': '<span title="Abandonné" style="color:#64748b">⛔</span> ',
    };
    return map[sessionStatus] || '';
  }

  function renderProspectCard(prospect) {
    const scoreBadge = prospect.score
      ? `<span class="score-badge">${prospect.score}</span>` 
      : '';
    const url = prospect.url
      ? `<span class="prospect-url text-muted">${prospect.url}</span>` 
      : '';
    const sessionIndicator = getSessionIndicator(prospect.session_status);
    return `
      <div class="prospect-card" data-id="${prospect.id}">
        <div class="prospect-card-header">
          <span class="prospect-name">${sessionIndicator}${prospect.nom}</span>
          ${scoreBadge}
        </div>
        ${url}
        <div class="prospect-card-footer">
          <span class="text-muted prospect-date">${window.formatDate ? window.formatDate(prospect.updated_at) : ''}</span>
          <button class="btn-icon btn-prospect-delete" data-id="${prospect.id}" title="Supprimer">🗑</button>
        </div>
      </div>
    `;
  }

  // ── Modal Nouveau Prospect ────────────────────────────────────
  function handleNewProspect() {
    const bodyHTML = `
      <div style="margin-bottom:1rem">
        <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Nom du restaurant *</label>
        <input type="text" id="modal-prospect-nom" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)" placeholder="Le Bistrot du Coin">
      </div>
      <div style="margin-bottom:1rem">
        <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Site web (optionnel)</label>
        <input type="url" id="modal-prospect-url" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)" placeholder="https://...">
      </div>
    `;

    window.showModal('Nouveau prospect', bodyHTML, [
      { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
      { label: 'Créer', type: 'primary', onClick: async () => {
        const nom = document.getElementById('modal-prospect-nom').value.trim();
        const url = document.getElementById('modal-prospect-url').value.trim() || null;
        if (!nom) { window.showToast && window.showToast('Le nom est requis', 'error'); return; }
        try {
          const newProspect = await window.API.createProspect({ nom, url, categorie: 'restauration' });
          window.showToast && window.showToast(`Prospect "${nom}" créé — lancement analyse...`);
          // Démarrer la pipeline (step 0 saisie, sans appel LLM = rapide)
          try {
            await window.API.startAtelierPipeline(newProspect.id);
          } catch(e) {
            // Si déjà une session, pas bloquant — on navigue quand même
            console.warn('startAtelierPipeline:', e.message);
          }
          window.closeModal();
          // Naviguer directement vers la vue pipeline du nouveau prospect
          window.location.href = `atelier.html?prospect_id=${newProspect.id}`;
        } catch (err) {
          window.showToast && window.showToast(err.message, 'error');
        }
      }}
    ]);
  }

  // ── Vue Pipeline ─────────────────────────────────────────────
  async function showPipelineView(prospectId) {
    document.getElementById('view-prospects').style.display = 'none';
    document.getElementById('view-pipeline').style.display = '';

    // Attacher le handler du bouton de suppression
    const btnDeleteProspect = document.getElementById('btn-delete-prospect');
    if (btnDeleteProspect) {
      btnDeleteProspect.onclick = handleDeleteProspect;
    }

    try {
      const { prospect, session } = await window.API.getProspect(prospectId);
      document.getElementById('pipeline-prospect-name').textContent = prospect.nom;
      document.getElementById('pipeline-prospect-meta').textContent =
        prospect.url || prospect.categorie || '';

      if (!session) {
        renderNoSession(prospectId);
        return;
      }

      currentSessionId = session.id;
      renderPipeline(session);

      const ACTIVE = ['CREATED', 'RUNNING', 'WAITING', 'PENDING', 'WAITING_VALIDATION'];
      if (ACTIVE.includes(session.status)) startPolling();

    } catch (e) {
      document.getElementById('pipeline-steps-list').innerHTML =
        `<p style="color:var(--danger);padding:2rem">Erreur: ${e.message}</p>`;
    }
  }

  function renderNoSession(prospectId) {
    document.getElementById('pipeline-steps-list').innerHTML = `
      <div style="text-align:center;padding:3rem;color:var(--text-muted)">
        <p style="margin-bottom:1.5rem">Aucun pipeline lancé pour ce prospect.</p>
        <button id="btn-start-pipeline" class="btn-primary">Lancer l'analyse</button>
      </div>
    `;
    document.getElementById('btn-start-pipeline')?.addEventListener('click', async () => {
      try {
        const result = await window.API.startAtelierPipeline(prospectId);
        currentSessionId = result.session_id;
        await showPipelineView(prospectId);
      } catch (err) {
        window.showToast && window.showToast(err.message, 'error');
      }
    });
  }

  function renderPipeline(session) {
    renderPipelineSteps(session);
    renderPipelineActionZone(session);

    const btnAbort = document.getElementById('btn-pipeline-abort');
    const btnDeleteProspect = document.getElementById('btn-delete-prospect');
    const TERMINAL = ['COMPLETED', 'ABORTED', 'FAILED'];
    
    if (btnAbort) {
      btnAbort.style.display = TERMINAL.includes(session.status) ? 'none' : 'block';
      btnAbort.onclick = handlePipelineAbort;
    }
    
    // Bouton de suppression toujours visible et actif
    if (btnDeleteProspect) {
      btnDeleteProspect.onclick = handleDeleteProspect;
    }
  }

  function renderPipelineSteps(session) {
    const container = document.getElementById('pipeline-steps-list');
    if (!session.steps?.length) {
      container.innerHTML = '<p style="color:var(--text-muted);padding:2rem">Aucun step</p>';
      return;
    }
    const sorted = [...session.steps].sort((a, b) => a.step_index - b.step_index);
    container.innerHTML = sorted.map(step => renderAtlierStepCard(step)).join('');

    // Vérifier si la qualification a retourné STOP
    const qualifStep = (session.steps || []).find(s => s.name === 'qualification');
    if (qualifStep && qualifStep.status === 'COMPLETED') {
      let qualifOutput = null;
      try {
        qualifOutput = typeof qualifStep.output_data === 'string'
          ? JSON.parse(qualifStep.output_data)
          : qualifStep.output_data;
      } catch(e) {}

      if (qualifOutput && qualifOutput.decision === 'STOP') {
        const stopBanner = document.createElement('div');
        stopBanner.style.cssText = `
          background: rgba(166, 72, 72, 0.15);
          border: 1px solid #a64848;
          border-radius: 8px;
          padding: 1rem 1.5rem;
          margin: 1rem 0;
          color: #e08080;
        `;
        stopBanner.innerHTML = `
          <strong>⚠️ Prospect qualifié STOP</strong><br>
          <span style="font-size:0.9rem">${qualifOutput.raison_stop || 'Ce prospect ne correspond pas aux critères.'}</span>
          <br><span style="font-size:0.85rem;opacity:0.7">La pipeline continue mais ce prospect est signalé comme non prioritaire.</span>
        `;
        // Insérer le bandeau en haut de la zone pipeline
        const pipelineZone = document.getElementById('pipeline-progress') 
          || document.getElementById('pipeline-zone')
          || document.querySelector('.pipeline-steps');
        if (pipelineZone) pipelineZone.prepend(stopBanner);
      }
    }

    // Expand au clic
    container.querySelectorAll('.step-card--expandable').forEach(card => {
      card.addEventListener('click', () => {
        const previewEl = card.querySelector('.step-output--preview');
        if (!previewEl) return;
        const isExpanded = card.classList.toggle('step-card--expanded');
        if (isExpanded) {
          const full = decodeURIComponent(previewEl.dataset.full);
          const md = window.renderMarkdown || ((t) => t.replace(/\n/g, '<br>'));
          previewEl.innerHTML = md(full);
        } else {
          const full = decodeURIComponent(previewEl.dataset.full);
          const preview = full.substring(0, 100);
          previewEl.innerHTML = `${preview}${full.length > 100 ? '...' : ''}<span class="step-expand-hint text-muted"> ▶ voir plus</span>`;
          previewEl.dataset.full = encodeURIComponent(full);
        }
      });
    });
  }

  function renderAtlierStepCard(step) {
    const statusClass = getStepStatusClass(step.status);
    const indicator = getStepIndicator(step.status);
    const isExpandable = step.status === 'COMPLETED' && step.output_data && step.output_data.length > 80;

    let outputPreview = '';
    if (step.status === 'COMPLETED' && step.output_data) {
      const preview = step.output_data.substring(0, 100);
      outputPreview = `
        <div class="step-output step-output--preview" data-full="${encodeURIComponent(step.output_data)}">
          ${preview}${step.output_data.length > 100 ? '...' : ''}
          ${isExpandable ? '<span class="step-expand-hint text-muted"> ▶ voir plus</span>' : ''}
        </div>
      `;
    }

    let errorHTML = '';
    if ((step.status === 'FAILED' || step.status === 'ERROR') && step.error_message) {
      errorHTML = `<div class="step-error">❌ ${step.error_message}</div>`;
    }

    let retryBtnHTML = '';
    if (step.status === 'FAILED' || step.status === 'ERROR') {
      retryBtnHTML = `
        <div class="step-card-right">
          <button class="btn-icon" onclick="window.retryAtelierStep(${step.id})" title="Relancer ce step">🔄</button>
        </div>
      `;
    }

    return `
      <div class="step-card ${statusClass} ${isExpandable ? 'step-card--expandable' : ''}" data-step-id="${step.id}">
        <div class="step-card-left">
          <div class="step-indicator">${indicator}</div>
          <div class="step-index">${step.step_index + 1}</div>
        </div>
        <div class="step-card-body">
          <div class="step-name">${step.step_display_name || step.step_name}</div>
          <div class="step-meta"><span class="text-muted">${step.model_used || step.model_type || ''}</span></div>
          ${outputPreview}
          ${errorHTML}
        </div>
        ${retryBtnHTML}
      </div>
    `;
  }

  function getStepStatusClass(status) {
    return { PENDING: 'step-card--pending', RUNNING: 'step-card--running', COMPLETED: 'step-card--completed', FAILED: 'step-card--error', WAITING_VALIDATION: 'step-card--waiting' }[status] || '';
  }

  function getStepIndicator(status) {
    return { 
      PENDING: '<span style="color:var(--text-muted)">○</span>', 
      RUNNING: '<div class="spinner spinner--sm"></div>', 
      COMPLETED: '✅', 
      FAILED: '❌', 
      WAITING_VALIDATION: '⏸️' 
    }[status] || '○';
  }

  function renderPipelineActionZone(session) {
    const zone = document.getElementById('pipeline-action-zone');

    // Cas 1 : step en WAITING_VALIDATION
    const waiting = session.steps?.find(s => s.status === 'WAITING_VALIDATION');
    if (waiting) {
      zone.style.display = 'block';
      switch (waiting.output_type) {
        case 'form':
          zone.innerHTML = renderSaisieForm(waiting);
          attachSaisieHandlers(waiting);
          break;
        case 'checkpoint':
          zone.innerHTML = renderCheckpointZone(waiting, session);
          attachCheckpointHandlers(waiting);
          break;
        default:
          zone.innerHTML = renderGenericWaiting(waiting);
          attachGenericHandlers(waiting);
      }
      return;
    }

    // Cas 2 : session COMPLETED → afficher zone export si step 8 completed
    if (session.status === 'COMPLETED') {
      const exportStep = session.steps?.find(s => s.step_name === 'export' && s.status === 'COMPLETED');
      if (exportStep) {
        zone.style.display = 'block';
        zone.innerHTML = renderExportZone();
        attachExportHandlers();
        return;
      }
    }

    // Cas 3 : session FAILED ou ABORTED → zone d'état
    if (['FAILED', 'ABORTED'].includes(session.status)) {
      zone.style.display = 'block';
      const isAborted = session.status === 'ABORTED';
      const emoji = isAborted ? '⛔' : '❌';
      const label = isAborted ? 'Pipeline abandonné' : 'Pipeline échoué';
      zone.innerHTML = `
        <div class="mc-action-header">
          <h3>${emoji} ${label}</h3>
          <p class="text-muted">
            ${isAborted
              ? 'Ce pipeline a été interrompu.'
              : 'Une ou plusieurs étapes ont échoué. Consultez les steps en erreur ci-dessus.'}
          </p>
        </div>
        <div class="mc-validation-actions">
          <button class="btn-secondary" onclick="document.getElementById('btn-back-kanban').click()">← Retour kanban</button>
          <button class="btn-primary" id="btn-restart-pipeline">🔄 Relancer l'analyse</button>
        </div>
      `;
      // Attacher le handler relance
      document.getElementById('btn-restart-pipeline')?.addEventListener('click', async () => {
        const btn = document.getElementById('btn-restart-pipeline');
        btn.disabled = true;
        btn.textContent = 'Lancement...';
        try {
          const result = await window.API.startAtelierPipeline(currentProspectId);
          currentSessionId = result.session_id;
          window.showToast && window.showToast('Nouvelle analyse lancée !');
          await showPipelineView(currentProspectId);
          startPolling();
        } catch (err) {
          window.showToast && window.showToast(err.message || 'Erreur relance', 'error');
          btn.disabled = false;
          btn.textContent = '🔄 Relancer l\'analyse';
        }
      });
      return;
    }

    // Cas 4 : session RUNNING (IA en train de traiter)
    if (session.status === 'RUNNING') {
        const runningStep = session.steps?.find(s => s.status === 'RUNNING');
        const stepName = runningStep?.step_display_name || 'Analyse en cours';
        const completedSteps = session.steps?.filter(s => s.status === 'COMPLETED').length || 0;
        const totalSteps = session.steps?.length || 0;
        const progressPercent = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;
        
        zone.style.display = 'block';
        zone.innerHTML = `
            <div class="action-card action-card--running">
                <div class="running-indicator">
                    <div class="spinner spinner--md"></div>
                    <div style="flex:1">
                        <p><strong>Pipeline en cours d'exécution...</strong></p>
                        <p class="text-muted">Étape actuelle : <em>${stepName}</em></p>
                        <p class="text-muted" style="font-size:0.85em;margin-top:0.5rem">
                            🕒 Cette étape peut prendre 1 à 3 minutes. Ne pas fermer la page.
                        </p>
                        <div class="progress-bar" style="margin-top:1rem">
                            <div class="progress-bar-fill" style="width:${progressPercent}%"></div>
                        </div>
                        <p class="text-muted" style="font-size:0.8em;margin-top:0.25rem">
                            ${completedSteps} / ${totalSteps} étapes terminées (${progressPercent}%)
                        </p>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    zone.style.display = 'none';
  }

  // ── Renderers de zones d'action (détail en AC_04) ─────────────
  // Placeholder minimal pour cette mission — AC_04 remplace ces fonctions

  function renderSaisieForm(step) {
    return `
      <div class="mc-action-header">
        <h3>📋 Saisie prospect</h3>
        <p class="text-muted">L'IA va analyser le site web du prospect. Vous pouvez ajouter du contexte optionnel.</p>
      </div>
      <div id="saisie-form-body" style="display:flex;flex-direction:column;gap:1rem;margin-top:1rem">
        <div>
          <label class="form-label">Site analysé</label>
          <div class="url-display" id="saisie-url-display" style="padding:0.75rem;background:var(--bg-input);border-radius:6px;color:var(--text-primary);font-size:0.95rem">
            🌐 <span id="saisie-url-value">Chargement...</span>
          </div>
        </div>
        <div>
          <label class="form-label">Contexte optionnel</label>
          <textarea id="saisie-observations" rows="4" class="form-input"
            placeholder="Observations de ta visite terrain, contexte particulier... (facultatif)"
            style="width:100%;resize:vertical"></textarea>
          <div class="form-hint">Informations complémentaires pour enrichir l'analyse IA</div>
        </div>
        <div id="saisie-attach-zone" style="display:flex;align-items:center;gap:0.5rem;margin-top:0.5rem">
          <button id="attach-btn-saisie" class="attach-btn" type="button" title="Joindre une image">📎</button>
          <input id="attach-input-saisie" type="file" accept="image/png,image/jpeg,image/webp" style="display:none">
          <div id="attach-preview-saisie" class="attach-preview" style="display:none">
            <span id="attach-filename-saisie" class="attach-filename"></span>
            <button id="attach-clear-saisie" class="attach-clear" type="button">✕</button>
          </div>
        </div>
        <div class="mc-validation-actions">
          <button id="btn-saisie-submit" class="btn-primary">Lancer l'analyse ➜</button>
        </div>
      </div>
    `;
  }

  async function attachSaisieHandlers(step) {
    // Pré-remplir avec les données du prospect
    try {
      const { prospect } = await window.API.getProspect(currentProspectId);
      
      // Afficher l'URL
      const urlDisplay = document.getElementById('saisie-url-value');
      if (urlDisplay) {
        urlDisplay.textContent = prospect.url || 'URL non renseignée';
      }
      
      // Pré-remplir les observations si déjà sauvées
      if (prospect.form_data) {
        try {
          const saved = JSON.parse(prospect.form_data);
          if (saved.observations) {
            document.getElementById('saisie-observations').value = saved.observations;
          }
        } catch (e) { /* form_data pas encore JSON */ }
      }
    } catch (e) { /* pas bloquant */ }

    // Event listeners pour l'attachement d'image
    const attachBtn = document.getElementById('attach-btn-saisie');
    const attachInput = document.getElementById('attach-input-saisie');
    const attachPreview = document.getElementById('attach-preview-saisie');
    const attachFilename = document.getElementById('attach-filename-saisie');
    const attachClear = document.getElementById('attach-clear-saisie');

    if (attachBtn && attachInput) {
      attachBtn.addEventListener('click', () => {
        attachInput.click();
      });

      attachInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
          const dataUrl = event.target.result;
          const base64 = dataUrl.split(',')[1];
          attachedImageSaisie = {
            base64: base64,
            filename: file.name
          };
          if (attachFilename) attachFilename.textContent = file.name;
          if (attachPreview) attachPreview.style.display = 'flex';
        };
        reader.readAsDataURL(file);
      });

      if (attachClear) {
        attachClear.addEventListener('click', () => {
          attachedImageSaisie = null;
          if (attachPreview) attachPreview.style.display = 'none';
          if (attachInput) attachInput.value = '';
        });
      }
    }

    document.getElementById('btn-saisie-submit')?.addEventListener('click', async () => {
      let observations = document.getElementById('saisie-observations')?.value.trim() || '';

      const btn = document.getElementById('btn-saisie-submit');
      btn.disabled = true;
      btn.textContent = 'Envoi...';

      const { prospect } = await window.API.getProspect(currentProspectId).catch(() => ({ prospect: {} }));

      // Si une image est attachée, appeler l'endpoint vision pour obtenir la description
      if (attachedImageSaisie) {
        try {
          const visionResult = await window.API.visionExtract(
            attachedImageSaisie.base64,
            attachedImageSaisie.filename
          );
          const imageDescription = visionResult.description || '';
          observations += `\n\n[Image jointe : ${attachedImageSaisie.filename}]\n${imageDescription}`;
        } catch (visionError) {
          console.warn('Erreur extraction vision:', visionError);
          observations += `\n\n[Image jointe : ${attachedImageSaisie.filename}]`;
        }
      }

      const formData = {
        nom: prospect.nom || '',
        url: prospect.url || '',
        categorie: 'restauration',
        observations,
        outils: {
          reservations: true,
          menu_ardoise: true
        }
      };

      try {
        // Sauvegarder form_data sur le prospect
        await window.API.patchProspect(currentProspectId, { form_data: JSON.stringify(formData) });

        // Valider le step 0 avec le JSON comme edited_output
        await window.API.validateStep(currentSessionId, step.id, {
          approved: true,
          edited_output: JSON.stringify(formData)
        });

        // Reset attachement après soumission réussie
        attachedImageSaisie = null;

        window.showToast && window.showToast('Analyse lancée !');
        await showPipelineView(currentProspectId);
        startPolling();
      } catch (err) {
        window.showToast && window.showToast(err.message || 'Erreur soumission', 'error');
        btn.disabled = false;
        btn.textContent = 'Lancer l\'analyse ➜';
      }
    });
  }

  function renderCheckpointZone(waitingStep, session) {
    // Récupérer le contenu de la proposition (step index 3)
    const propositionStep = (session?.steps || []).find(s => s.name === 'proposition');
    const propositionContent = propositionStep?.output_data || propositionStep?.output || '';

    return `
      <div class="checkpoint-zone">
        <h3 style="margin-bottom:1rem">✅ Valider la proposition</h3>
        ${propositionContent ? `
          <div class="proposition-preview" style="
            background: var(--bg-alt, #1a1a2e);
            border: 1px solid var(--border, #333);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            white-space: pre-wrap;
            font-size: 0.9rem;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.6;
          ">${propositionContent}</div>
        ` : '<p style="color:var(--text-secondary);margin-bottom:1rem">Chargement de la proposition...</p>'}
        <div style="display:flex;gap:1rem">
          <button class="btn-primary" id="btn-checkpoint-approve">✅ Valider — Lancer la génération</button>
          <button class="btn-danger" id="btn-checkpoint-reject">✗ Refuser — Arrêter</button>
        </div>
      </div>
    `;
  }

  function attachCheckpointHandlers(step) {
    document.getElementById('btn-checkpoint-approve')?.addEventListener('click', async () => {
      const btn = document.getElementById('btn-checkpoint-approve');
      btn.disabled = true;
      btn.textContent = 'Validation...';
      try {
        await window.API.validateStep(currentSessionId, step.id, { approved: true });
        window.showToast && window.showToast('Génération lancée !');
        await showPipelineView(currentProspectId);
        startPolling();
      } catch (err) {
        window.showToast && window.showToast(err.message, 'error');
        btn.disabled = false;
        btn.textContent = '✅ Valider — Lancer la génération';
      }
    });

    document.getElementById('btn-checkpoint-reject')?.addEventListener('click', async () => {
      if (!confirm('Abandonner ce pipeline ? La session sera terminée.')) return;
      try {
        await window.API.validateStep(currentSessionId, step.id, { approved: false });
        window.showToast && window.showToast('Pipeline abandonné');
        stopPolling();
        await showPipelineView(currentProspectId);
      } catch (err) {
        window.showToast && window.showToast(err.message, 'error');
      }
    });
  }

  function renderGenericWaiting(step) {
    return `<div class="mc-action-header"><h3>⏸️ ${step.step_display_name} — En attente</h3></div>`;
  }

  function attachGenericHandlers(step) { /* AC_04 */ }

  function renderExportZone() {
    return `
      <div class="mc-action-header">
        <h3>🎉 Démo générée avec succès !</h3>
        <p class="text-muted">Les fichiers sont prêts à être exportés.</p>
      </div>
      <div id="export-files-list" style="margin:1rem 0">
        <div class="spinner" style="margin:1rem auto"></div>
      </div>
      <div class="mc-validation-actions">
        <a id="btn-export-zip" class="btn-primary" style="text-decoration:none;display:inline-block">
          ⬇️ Télécharger le ZIP
        </a>
        <button id="btn-mark-contacted" class="btn-secondary">Marquer comme contacté</button>
      </div>
    `;
  }

  async function attachExportHandlers() {
    // Charger la liste des fichiers
    try {
      const { files } = await window.API.listProspectFiles(currentProspectId);
      const listEl = document.getElementById('export-files-list');
      if (!listEl) return;
      if (!files || files.length === 0) {
        listEl.innerHTML = '<p class="text-muted">Aucun fichier trouvé</p>';
      } else {
        listEl.innerHTML = `
          <div class="export-file-list">
            ${files.map(f => `
              <div class="export-file-row">
                <span class="export-file-name">📄 ${f.name}</span>
                <span class="text-muted export-file-size">${f.size_kb} KB</span>
              </div>
            `).join('')}
          </div>
        `;
      }
    } catch (e) {
      const listEl = document.getElementById('export-files-list');
      if (listEl) listEl.innerHTML = '<p class="text-muted">Impossible de charger la liste</p>';
    }

    // Lien ZIP
    const zipBtn = document.getElementById('btn-export-zip');
    if (zipBtn) {
      zipBtn.href = window.API.exportProspectZip(currentProspectId);
    }

    // Marquer contacté
    document.getElementById('btn-mark-contacted')?.addEventListener('click', async () => {
      try {
        await window.API.patchProspect(currentProspectId, { statut: 'contacte' });
        window.showToast && window.showToast('Statut mis à jour : Contacté');
      } catch (err) {
        window.showToast && window.showToast(err.message, 'error');
      }
    });
  }

  // ── Polling ──────────────────────────────────────────────────
  function startPolling() {
    if (pollInterval) return;
    
    pollInterval = setInterval(async () => {
      try {
        const { session } = await window.API.getProspect(currentProspectId);
        if (!session) { stopPolling(); return; }
        
        renderPipeline(session);
        if (['COMPLETED', 'ABORTED', 'FAILED'].includes(session.status)) {
          stopPolling();
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    }, 5000);
  }

  function stopPolling() {
    if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
  }

  // ── Abandon pipeline ─────────────────────────────────────────
  async function handlePipelineAbort() {
    if (!confirm('Abandonner ce pipeline ?')) return;
    try {
      await window.API.abortPipeline(currentSessionId);
      window.showToast && window.showToast('Pipeline abandonné');
      await showPipelineView(currentProspectId);
    } catch (err) {
      window.showToast && window.showToast(err.message, 'error');
    }
  }

  // ── Supprimer prospect ─────────────────────────────────────────
  async function handleDeleteProspect() {
    const prospectName = document.getElementById('pipeline-prospect-name')?.textContent || 'ce prospect';
    
    // Vérifier si le pipeline est en cours
    let confirmMessage = `Supprimer "${prospectName}" et toute sa progression ?\n\nCette action est irréversible.`;
    
    try {
      const prospectData = await window.API.getProspect(currentProspectId);
      if (prospectData.session && prospectData.session.status === 'RUNNING') {
        confirmMessage = `⚠️ ATTENTION : Le pipeline est EN COURS !\n\nSupprimer "${prospectName}" maintenant va interrompre l'analyse en cours.\n\nÊtes-vous sûr de vouloir continuer ?`;
      }
    } catch (e) {
      // Session non trouvée, continuer normalement
    }
    
    if (!confirm(confirmMessage)) return;
    
    try {
      await window.API.deleteProspect(currentProspectId);
      window.showToast && window.showToast('Prospect supprimé', 'success');
      stopPolling();
      window.location.href = 'atelier.html';
    } catch (err) {
      window.showToast && window.showToast('Erreur suppression: ' + err.message, 'error');
    }
  }

  // ── Retry step ───────────────────────────────────────────────
  window.retryAtelierStep = async function(stepId) {
    if (!currentSessionId) {
      window.showToast && window.showToast('Session non trouvée', 'error');
      return;
    }
    try {
      await window.API.retryStep(currentSessionId, stepId);
      window.showToast && window.showToast('Step relancé');
      await showPipelineView(currentProspectId);
      startPolling();
    } catch (err) {
      window.showToast && window.showToast(err.message || 'Erreur relance', 'error');
    }
  };

  // ── Réinitialiser l'atelier ───────────────────────────────────
  async function handleResetAtelier() {
    if (!confirm('⚠️ Supprimer TOUS les prospects de l\'atelier ?\n\nCette action est irréversible. Tous les prospects et leurs pipelines seront supprimés.')) {
      return;
    }

    try {
      const result = await window.API.deleteAllProspects();
      
      if (result.deleted === 0) {
        window.showToast && window.showToast('Aucun prospect à supprimer', 'info');
      } else {
        window.showToast && window.showToast(`${result.deleted} prospect(s) supprimé(s)`, 'success');
      }

      await loadKanban();

    } catch (err) {
      console.error('Erreur réinitialisation atelier:', err);
      window.showToast && window.showToast('Erreur lors de la réinitialisation', 'error');
    }
  }

  window.addEventListener('beforeunload', stopPolling);
})();
