(function () {
  // ── State ──────────────────────────────────────────────────
  let reflexionSessionId = null;
  let reflexionSession = null;
  let projectId = null;
  let pipelineSessionId = null;
  let pendingEdit = null;
  let pollInterval = null;
  let sourceMissionPromptId = null;
  let currentPipelineSession = null;
  let currentLivrableContent = null;
  let currentLivrableType = null;
  let currentStep = 1;
  let attachedImageReflexion = null;

  // ── Bootstrap ─────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', async () => {
    await init();
    setupEventListeners();
  });

  async function init() {
    const sessionParam = window.getURLParam('session');
    const pipelineParam = window.getURLParam('pipeline_session');
    const projectParam = window.getURLParam('project_id');
    const newParam = window.getURLParam('new');

    projectId = projectParam ? parseInt(projectParam) : null;

    const VALID_TYPES = ['mission_code', 'decision_figee', 'plan_multi_missions'];

    if (sessionParam) {
      await loadReflexionSession(parseInt(sessionParam));
    } else if (pipelineParam) {
      pipelineSessionId = parseInt(pipelineParam);
      showPipelineOnly();
      await loadPipelineSession();
    } else if (projectParam && newParam) {
      const livrableType = VALID_TYPES.includes(newParam) ? newParam : 'mission_code';
      await autoCreateSession(parseInt(projectParam), livrableType);
      
      // Gestion du préfill depuis un livrable mission_code
      const prefillParam = window.getURLParam('prefill');
      if (prefillParam && newParam === 'mission_code') {
        sessionStorage.setItem('reflexion_prefill', decodeURIComponent(prefillParam));
      }
    } else {
      showEmptyState();
    }
  }

  // ── Empty state ───────────────────────────────────────────────────
  function showEmptyState() {
    document.getElementById('mission-empty-state').style.display = 'block';
  }

  async function autoCreateSession(projId, livrableType) {
    projectId = projId;
    try {
      const session = await window.API.createReflexion(projectId, livrableType);
      history.replaceState(null, '', `mission.html?session=${session.id}&project_id=${projectId}`);
      reflexionSessionId = session.id;
      await loadReflexionSession(session.id);
    } catch (error) {
      window.showToast('Erreur création session : ' + error.message, 'error');
      showEmptyState();
    }
  }

  // ── Zone 1 : Chargement session Réflexion ─────────────────────────
  async function loadReflexionSession(sessionId) {
    try {
      const session = await window.API.getReflexion(sessionId);
      reflexionSessionId = sessionId;
      reflexionSession = session;
      projectId = projectId || session.project_id;

      updateMissionHeader(session);
      showMissionFlow();
      renderSessionState(session);
      await loadCadrageHealth(sessionId);

      if (session.input_tokens_total > 700000) {
        showTokenWarning(session.input_tokens_total);
      }
    } catch (error) {
      console.error('Erreur chargement session:', error);
      window.showToast('Erreur de chargement : ' + error.message, 'error');
    }
  }

  async function updateMissionHeader(session) {
    const livrableLabels = {
      'mission_code': '🎯 Mission Code',
      'decision_figee': '📌 Décision figée',
      'plan_multi_missions': '📋 Plan multi-missions'
    };
    const statusLabels = {
      'OUVERTE': '● Ouverte',
      'EN_FIGEMENT': '⏳ En figement',
      'FIGEE': '🔒 Figée',
      'ABANDONNEE': '✕ Abandonnée'
    };
    const statusColors = {
      'OUVERTE': 'var(--success)',
      'EN_FIGEMENT': 'var(--warning)',
      'FIGEE': 'var(--accent)',
      'ABANDONNEE': 'var(--text-muted)'
    };

    document.getElementById('mission-title').textContent = session.titre || '🎯 Mission';

    if (projectId) {
      try {
        const project = await window.API.getProject(projectId);
        document.getElementById('mission-project-name').textContent = `📁 ${project.name}`;
      } catch (e) {}
    }

    const livradeBadge = document.getElementById('mission-livrable-badge');
    livradeBadge.textContent = livrableLabels[session.livrable_type] || session.livrable_type;
    livradeBadge.style.display = 'inline-flex';

    const statusBadge = document.getElementById('mission-status-badge');
    statusBadge.textContent = statusLabels[session.statut] || session.statut;
    statusBadge.style.color = statusColors[session.statut] || 'var(--text-muted)';
    statusBadge.style.display = 'inline';

    document.getElementById('livrable-type-display').textContent =
      livrableLabels[session.livrable_type] || session.livrable_type;
  }

  function showMissionFlow() {
    document.getElementById('mission-flow').style.display = 'flex';
  }

  function setActiveStep(n) {
    currentStep = n;
    for (let i = 1; i <= 4; i++) {
      const card = document.getElementById(`step-${i}`);
      const status = document.getElementById(`step-${i}-status`);
      if (!card) continue;
      card.classList.remove('step-active', 'step-passed', 'step-future');
      if (i < n)      { card.classList.add('step-passed');  if (status) status.textContent = '✓ Terminée'; }
      else if (i === n) { card.classList.add('step-active');  if (status) status.textContent = '● En cours'; }
      else            { card.classList.add('step-future');  if (status) status.textContent = 'En attente'; }
    }
    setTimeout(() => {
      const target = document.getElementById(`step-${n}`);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }

  function renderRecapFichiers(containerId, fichiers, titre) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (!fichiers || fichiers.length === 0) { el.style.display = 'none'; return; }
    const items = fichiers.map(f => `<span class="recap-fichier-item">📄 ${f}</span>`).join('');
    el.innerHTML = `<div class="recap-fichiers-title">${titre}</div><div>${items}</div>`;
    el.style.display = 'block';
  }

  function renderSessionState(session) {
    const inputArea = document.getElementById('reflexion-input-area');
    const input = document.getElementById('reflexion-input');
    const btnSend = document.getElementById('btn-send-message');
    const btnFiger = document.getElementById('btn-figer');
    const messagesContainer = document.getElementById('reflexion-messages');

    messagesContainer.innerHTML = '';
    if (session.messages && session.messages.length > 0) {
      session.messages.forEach(msg => renderMessage(msg));
    }

    if (session.statut === 'FIGEE') {
      inputArea.style.display = 'none';
      loadAndRenderLivrable(session.id, session.livrable_type);
    } else if (session.statut === 'ABANDONNEE') {
      inputArea.style.display = 'none';
      setActiveStep(1);
      
      // Afficher le bouton retour pour les sessions abandonnées
      const btnBack = document.getElementById('btn-back-project');
      if (btnBack) btnBack.href = projectId ? `dossier.html?id=${projectId}` : 'index.html';
      const footerEl = document.getElementById('step-4-footer');
      if (footerEl) footerEl.style.display = 'block';
    } else if (session.statut === 'EN_FIGEMENT') {
      inputArea.style.opacity = '0.5';
      input.disabled = true;
      btnSend.disabled = true;
      btnFiger.disabled = true;
      setActiveStep(1);
    } else {
      // OUVERTE
      inputArea.style.display = 'block';
      inputArea.style.opacity = '1';
      input.disabled = false;
      btnSend.disabled = false;
      btnFiger.disabled = false;
      setActiveStep(1);
      scrollMessages();
      
      // Pré-remplir l'input depuis sessionStorage si présent (pont Réflexion → Code)
      const prefillContent = sessionStorage.getItem('reflexion_prefill');
      if (prefillContent) {
        input.value = prefillContent;
        input.focus();
        sessionStorage.removeItem('reflexion_prefill');
      }
    }
  }

  function renderMessage(message) {
    const container = document.getElementById('reflexion-messages');
    const div = document.createElement('div');
    div.className = `message message-${message.role}`;

    const roleLabels = {
      'user': '💬 Vous',
      'assistant': '🤖 Assistant',
      'system': '⚙️ Système',
      'sante_cadrage': '🩺 Santé du cadrage'
    };

    const roleEl = document.createElement('div');
    roleEl.className = 'message-role';
    roleEl.textContent = roleLabels[message.role] || message.role;

    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    if (message.role === 'assistant' || message.role === 'sante_cadrage') {
      contentEl.innerHTML = window.renderMarkdown(message.content);
    } else {
      contentEl.textContent = message.content;
    }

    div.appendChild(roleEl);
    div.appendChild(contentEl);
    
    // Afficher badge d'attachement si présent
    if (message.role === 'user' && message.attachment_filename) {
      const badge = document.createElement('span');
      badge.className = 'msg-attachment-badge';
      badge.textContent = `📎 ${message.attachment_filename}`;
      div.appendChild(badge);
    }
    
    container.appendChild(div);
  }

  function scrollMessages() {
    const container = document.getElementById('reflexion-messages');
    if (container) container.scrollTop = container.scrollHeight;
  }

  // ── Zone 1 : Envoi de message ─────────────────────────────────────
  async function sendMessage() {
    const input = document.getElementById('reflexion-input');
    if (!input) return;
    const content = input.value.trim();
    if (!reflexionSessionId) {
      window.showToast('Aucune session active', 'error');
      return;
    }
    if (!content) return;

    const btnSend = document.getElementById('btn-send-message');
    btnSend.disabled = true;
    btnSend.textContent = '⏳';

    try {
      const body = { content };
      if (attachedImageReflexion) {
        body.attachment_base64 = attachedImageReflexion.base64;
        body.attachment_filename = attachedImageReflexion.filename;
      }
      
      const messages = await window.API.sendReflexionMessage(reflexionSessionId, body);
      const container = document.getElementById('reflexion-messages');
      container.innerHTML = '';
      messages.forEach(msg => renderMessage(msg));
      input.value = '';
      scrollMessages();

      // Reset attachement après envoi réussi
      if (attachedImageReflexion) {
        attachedImageReflexion = null;
        const preview = document.getElementById('attach-preview-reflexion');
        const inputFile = document.getElementById('attach-input-reflexion');
        if (preview) preview.style.display = 'none';
        if (inputFile) inputFile.value = '';
      }

      // Rafraîchir le titre si première session
      if (!reflexionSession.titre) {
        await loadReflexionSession(reflexionSessionId);
      }
    } catch (error) {
      console.error('Erreur envoi message:', error);
      window.showToast('Erreur envoi : ' + error.message, 'error');
    } finally {
      btnSend.disabled = false;
      btnSend.textContent = 'Envoyer';
    }
  }

  // ── Zone 1 : Santé cadrage ────────────────────────────────────────
  async function loadCadrageHealth(sessionId) {
    try {
      const health = await window.API.checkCadrageHealth(sessionId);
      renderCadrageHealth(health);
    } catch (error) {
      console.error('Erreur cadrage health:', error);
    }
  }

  function renderCadrageHealth(health) {
    const panel = document.getElementById('zone-cadrage');
    const verdict = document.getElementById('cadrage-verdict');
    const details = document.getElementById('cadrage-details');

    const icons = { vert: '🟢', orange: '🟠', rouge: '🔴' };
    const labels = {
      vert: 'Cadrage OK',
      orange: 'Point d\'attention',
      rouge: 'Problème détecté'
    };

    verdict.textContent = `${icons[health.verdict_global] || '❓'} ${labels[health.verdict_global] || health.verdict_global}`;

    details.innerHTML = '';
    (health.checks || []).forEach(check => {
      const div = document.createElement('div');
      div.className = 'cadrage-check';
      const icon = check.statut === 'vert' ? '✓' : check.statut === 'orange' ? '⚠' : '✗';
      div.innerHTML = `
        <span class="check-icon check-${check.statut}">${icon}</span>
        <span class="check-name">${check.nom}</span>
        <span class="check-message">${check.message}</span>
      `;
      details.appendChild(div);
    });

    panel.style.display = 'block';
  }

  // ── Zone 1 : Token warning ────────────────────────────────────────
  function showTokenWarning(tokens) {
    const el = document.getElementById('token-warning');
    if (!el) return;
    el.style.display = 'block';
    el.innerHTML = `
      <span>⚠️ ${Math.round(tokens / 1000)}k tokens utilisés (70%+ de la fenêtre). Considérez de figer cette session.</span>
      <button onclick="document.getElementById('token-warning').style.display='none'" style="background:none;border:none;color:var(--text-muted);cursor:pointer;margin-left:auto">×</button>
    `;
  }

  // ── Zone 1 : Abandon session ──────────────────────────────────────
  function abandonSession() {
    if (!reflexionSessionId) return;
    window.showModal(
      'Abandonner cette session ?',
      '<p>Cette action est <strong>irréversible</strong>. La session passera en statut ABANDONNÉE.</p>',
      [
        { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
        { label: 'Abandonner', type: 'danger', onClick: async () => {
          window.closeModal();
          try {
            await window.API.abandonReflexion(reflexionSessionId);
            window.showToast('Session abandonnée');
            window.location.href = projectId
              ? `dossier.html?id=${projectId}` 
              : 'code-projects.html';
          } catch (error) {
            window.showToast('Erreur abandon : ' + error.message, 'error');
          }
        }}
      ]
    );
  }

  // ── Transition Zone 1 → Zone 2 : Figement ────────────────────────
  async function openFigerModal() {
    if (!reflexionSessionId) {
      window.showToast('Aucune session active', 'error');
      return;
    }
    
    const modal = document.getElementById('modal-figer');
    const detectionZone = document.getElementById('figer-detection-zone');
    const loadingDiv = document.getElementById('figer-detection-loading');
    const resultDiv = document.getElementById('figer-detection-result');
    const suggestionP = document.getElementById('figer-detection-suggestion');
    const selectEl = document.getElementById('figer-livrable-type-select');
    
    modal.style.display = 'flex';
    detectionZone.style.display = 'block';
    loadingDiv.style.display = 'flex';
    resultDiv.style.display = 'none';
    
    try {
      const detection = await window.API.detectLivrableType(reflexionSessionId);
      const typeLabels = {
        mission_code: '🎯 Mission Code',
        decision_figee: '📌 Décision figée',
        plan_multi_missions: '📋 Plan multi-missions'
      };
      suggestionP.textContent = `🤖 L'IA suggère : ${typeLabels[detection.livrable_type]} — ${detection.justification}`;
      selectEl.value = detection.livrable_type;
      loadingDiv.style.display = 'none';
      resultDiv.style.display = 'block';
    } catch (error) {
      console.error('Erreur détection type:', error);
      loadingDiv.style.display = 'none';
      resultDiv.style.display = 'block';
      suggestionP.textContent = '⚠️ Détection impossible, veuillez sélectionner le type manuellement';
      selectEl.value = 'mission_code';
    }
  }

  async function confirmFiger() {
    const selectEl = document.getElementById('figer-livrable-type-select');
    const livrableTypeChoisi = selectEl ? selectEl.value : null;
    
    document.getElementById('modal-figer').style.display = 'none';
    const btnFiger = document.getElementById('btn-figer');
    btnFiger.disabled = true;
    btnFiger.textContent = '⏳ Figement…';
    window.showToast('🔒 Figement en cours… Cela peut prendre jusqu\'a 30 secondes', 'info');

    try {
      const livrable = await window.API.figerReflexion(reflexionSessionId, livrableTypeChoisi);
      window.showToast('Mission figée et cadrage écrit', 'success');
      renderRecapFichiers(
        'recap-fichiers-figement',
        livrable.fichiers_modifies || [],
        '✓ Cadrage écrit dans :'
      );
      await loadReflexionSession(reflexionSessionId);
    } catch (error) {
      console.error('Erreur figement:', error);
      window.showToast('Erreur figement : ' + error.message, 'error');
      btnFiger.disabled = false;
      btnFiger.textContent = '🔒 Figer la mission';
    }
  }

  // ── Zone 2 : Chargement + rendu livrable ────────────────────
  async function loadAndRenderLivrable(sessionId, livrableType) {
    try {
      const livrable = await window.API.getLivrable(sessionId);
      currentLivrableContent = livrable.content;
      currentLivrableType = livrable.livrable_type;
      sourceMissionPromptId = livrable.id || null;
      // Révéler le contenu de l'étape 2
      document.getElementById('step-2-placeholder').style.display = 'none';
      document.getElementById('step-2-content').style.display = 'block';
      renderLivrable(livrable);
      setActiveStep(2);
    } catch (error) {
      console.error('Erreur chargement livrable:', error);
      document.getElementById('figee-content').innerHTML =
        '<p style="color:var(--danger)">Erreur lors du chargement du livrable.</p>';
    }
  }

  function renderLivrable(livrable) {
    const content = document.getElementById('figee-content');

    const htmlContent = livrable.content
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/^### (.+)$/gm, '<h4>$1</h4>')
      .replace(/^## (.+)$/gm, '<h3>$1</h3>')
      .replace(/^# (.+)$/gm, '<h2>$1</h2>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/\n\n/g, '<br><br>');

    content.innerHTML = htmlContent;

    // Bandeau si livrable déjà consommé
    if (livrable.consumed_at) {
      const formattedDate = window.formatDate 
        ? window.formatDate(livrable.consumed_at)
        : new Date(livrable.consumed_at).toLocaleDateString('fr-FR');
      
      const banner = document.createElement('div');
      banner.className = 'consumed-banner';
      banner.textContent = `⚠ Ce livrable a déjà été consommé le ${formattedDate}`;
      banner.style.cssText = 'background-color: #fff3cd; color: #856404; padding: 8px; border-radius: 4px; margin-bottom: 12px; font-size: 0.9rem;';
      
      content.insertBefore(banner, content.firstChild);
    }

    // mission_code : bouton Exécuter + preview parsing
    if (livrable.livrable_type === 'mission_code') {
      const zoneExec = document.getElementById('zone-execution-launch');
      zoneExec.style.display = 'block';
      // Déclencher le preview parsing sur le contenu du livrable
      previewParsingFromLivrable(livrable.content);
      
      // Bouton "Lancer en mission Code"
      const btnLaunchCode = document.getElementById('btn-launch-code-mission');
      if (btnLaunchCode) {
        btnLaunchCode.style.display = 'inline-flex';
        btnLaunchCode.onclick = () => {
          let promptContent = livrable.content;
          
          // Limiter à 4000 caractères pour éviter les URLs trop longues
          if (promptContent.length > 4000) {
            promptContent = promptContent.substring(0, 4000);
            window.showToast('⚠️ Prompt tronqué à 4000 caractères — vérifiez le contenu avant de lancer', 'warning');
          }
          
          const encodedPrompt = encodeURIComponent(promptContent);
          const params = new URLSearchParams();
          if (projectId) params.set('project_id', projectId);
          params.set('prefill', encodedPrompt);
          params.set('new', 'mission_code');
          window.location.href = `mission.html?${params.toString()}`;
        };
      }
    }

    // decision_figee : bouton Appliquer PROJET_CONTEXTE
    if (livrable.livrable_type === 'decision_figee') {
      document.getElementById('zone-apply-decision').style.display = 'block';
    }

    // plan_multi_missions : boutons copie individuels
    if (livrable.livrable_type === 'plan_multi_missions') {
      const headers = content.querySelectorAll('h3, h4');
      headers.forEach((header) => {
        if (header.textContent.includes('Mission') || header.textContent.match(/^\d+\./)) {
          const btn = document.createElement('button');
          btn.className = 'btn-secondary btn-sm';
          btn.textContent = '✂️ Copier cette mission';
          btn.style.marginTop = '0.25rem';
          btn.onclick = () => copyMissionBlock(header);
          header.parentNode.insertBefore(btn, header.nextSibling);
        }
      });
    }
  }

  async function previewParsingFromLivrable(text) {
    if (!text || text.length < 20) return;
    try {
      const result = await window.API.parseMissionPrompt(text);
      const fichierCount = result.fichiers_concernes ? result.fichiers_concernes.length : 0;
      const titre = result.titre || '(titre non détecté)';
      const inner = document.getElementById('mission-preview-inner');
      const previewEl = document.getElementById('mission-preview');
      let html = `<strong>📋 ${titre}</strong>`;
      html += `<span style="margin-left:1rem;color:var(--text-muted)">📁 ${fichierCount} fichier(s)</span>`;
      if (result.modele_recommande) {
        html += `<span style="margin-left:1rem;color:var(--accent)">🤖 ${formatModelName(result.modele_recommande)}</span>`;
      }
      inner.innerHTML = html;
      previewEl.style.display = 'block';
      applyModelRecommendation(result);
      const warningEl = document.getElementById('mission-warning');
      if (result.parse_warnings && result.parse_warnings.length > 0) {
        warningEl.innerHTML = '⚠️ ' + result.parse_warnings.join(' — ');
        warningEl.style.display = 'block';
      } else {
        warningEl.style.display = 'none';
      }
    } catch (e) {
      // Parsing non critique, pas de blocage
    }
  }

  function formatModelName(slug) {
    const names = {
      'anthropic/claude-haiku-4.5': 'Claude Haiku 4.5',
      'anthropic/claude-sonnet-4.5': 'Claude Sonnet 4.5',
      'google/gemini-2.5-flash': 'Gemini 2.5 Flash',
      'google/gemini-2.5-pro': 'Gemini 2.5 Pro'
    };
    return names[slug] || slug;
  }

  function applyModelRecommendation(parseResult) {
    const select = document.getElementById('model-override-select');
    if (!select) return;
    let targetSlug = 'anthropic/claude-haiku-4.5';
    if (parseResult.modele_recommande) {
      targetSlug = parseResult.modele_recommande;
    } else if (parseResult.fichiers_concernes) {
      const count = parseResult.fichiers_concernes.length;
      if (count > 5) targetSlug = 'google/gemini-2.5-pro';
      else if (count > 2) targetSlug = 'anthropic/claude-sonnet-4.5';
    }
    if (select.querySelector(`option[value="${targetSlug}"]`)) select.value = targetSlug;
  }

  function copyMissionBlock(header) {
    let text = header.textContent + '\n';
    let node = header.nextSibling;
    while (node && (!node.tagName || !['H2', 'H3', 'H4'].includes(node.tagName))) {
      if (node.textContent) text += node.textContent + '\n';
      node = node.nextSibling;
    }
    navigator.clipboard.writeText(text.trim())
      .then(() => window.showToast('Mission copiée', 'success'))
      .catch(() => window.showToast('Erreur copie', 'error'));
  }

  function copyLivrable() {
    const text = currentLivrableContent || document.getElementById('figee-content').innerText;
    navigator.clipboard.writeText(text)
      .then(() => window.showToast('Livrable copié', 'success'))
      .catch(() => window.showToast('Erreur copie', 'error'));
  }

  // ── Zone 2 : Appliquer décision (decision_figee) ──────────────────
  async function applyDecision() {
    if (!reflexionSessionId || !projectId) {
      window.showToast('Session ou projet manquant', 'error');
      return;
    }
    try {
      // Récupérer le diff proposé
      const livrable = await window.API.getLivrable(reflexionSessionId);
      const result = await window.API.proposeEdit(reflexionSessionId, 'PROJET_CONTEXTE.md', livrable.content);
      if (result && result.diff) {
        showDiffModal('PROJET_CONTEXTE.md', result.diff, livrable.content);
      } else {
        window.showToast('Aucun diff généré', 'warning');
      }
    } catch (error) {
      window.showToast('Erreur proposition édition : ' + error.message, 'error');
    }
  }

  function showDiffModal(filePath, diffText, newContent) {
    pendingEdit = { file_path: filePath, new_content: newContent };
    document.getElementById('diff-file-name').textContent = filePath;
    const diffContent = document.getElementById('diff-content');
    diffContent.innerHTML = window.renderDiff ? window.renderDiff(diffText) : diffText;
    document.getElementById('modal-diff').style.display = 'flex';
  }

  // ── Transition Zone 2 → Zone 3 : Exécuter mission code ───────────
  async function executeMission() {
    if (!projectId) {
      window.showToast('Projet non trouvé', 'error');
      return;
    }

    // Récupérer le contenu du livrable
    let missionText = '';
    try {
      const livrable = await window.API.getLivrable(reflexionSessionId);
      missionText = livrable.content;
    } catch (e) {
      window.showToast('Erreur lecture livrable', 'error');
      return;
    }

    if (!missionText || missionText.length < 50) {
      window.showToast('Livrable trop court (min 50 caractères)', 'error');
      return;
    }

    const modelOverride = document.getElementById('model-override-select')?.value || null;
    const btn = document.getElementById('btn-execute-mission');
    btn.disabled = true;
    btn.textContent = '⏳ Lancement…';

    try {
      const result = await window.API.startPipeline({
        project_id: projectId,
        workflow_type: 'code_mission',
        initial_input: missionText,
        modele_override: modelOverride,
        source_mission_prompt_id: sourceMissionPromptId || null
      });

      pipelineSessionId = result.session?.id || result.session_id || result.id;
      if (!pipelineSessionId) throw new Error('Session ID non trouvé dans la réponse');

      // Marquer le livrable comme consommé
      try { await window.API.marquerConsomme(reflexionSessionId); } catch (e) { console.warn('marquerConsomme non critique:', e.message); }

      // Passer à l'étape 3 et démarrer le polling
      document.getElementById('step-3-placeholder').style.display = 'none';
      document.getElementById('step-3-content').style.display = 'block';
      setActiveStep(3);
      await loadPipelineSession();
      window.showToast('Mission lancée', 'success');
    } catch (error) {
      window.showToast('Erreur lancement : ' + error.message, 'error');
      btn.disabled = false;
      btn.textContent = '▶ Exécuter la mission';
    }
  }

  // ── Zone 3 : Pipeline ───────────────────────────────────────────
  function showPipelineOnly() {
    // Mode lecture pipeline historique (pas de session réflexion)
    const step1 = document.getElementById('step-1');
    if (step1) step1.style.display = 'none';
    showMissionFlow();
    document.getElementById('step-3-placeholder').style.display = 'none';
    document.getElementById('step-3-content').style.display = 'block';
    setActiveStep(3);
    document.getElementById('mission-title').textContent = '⚙️ Exécution pipeline';
  }

  async function loadPipelineSession() {
    try {
      const session = await window.API.getPipeline(pipelineSessionId);
      currentPipelineSession = session;
      renderPipelineSession(session);

      const ACTIVE = ['CREATED', 'RUNNING', 'WAITING', 'PENDING', 'WAITING_VALIDATION'];
      if (ACTIVE.includes(session.status)) {
        startPolling();
      } else {
        stopPolling();
      }
    } catch (error) {
      console.error('Erreur chargement pipeline:', error);
      window.showToast('Erreur chargement pipeline', 'error');
    }
  }

  function startPolling() {
    if (pollInterval) return;
    pollInterval = setInterval(async () => {
      try {
        const session = await window.API.getPipeline(pipelineSessionId);
        currentPipelineSession = session;
        renderPipelineSession(session);
        if (['COMPLETED', 'ABORTED', 'ERROR', 'FAILED'].includes(session.status)) {
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

  function renderPipelineSession(session) {
    renderPipelineHeader(session);
    renderSteps(session);
    renderActionZone(session);
  }

  async function renderPipelineHeader(session) {
    const wfType = (session.workflow_type || '').replace(/_/g, ' ')
      .split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    document.getElementById('mc-workflow-type').textContent = wfType;

    const statusBadge = window.statusBadge ? window.statusBadge(session.status) : `<span class="badge">${session.status}</span>`;
    document.getElementById('mc-status-badge-pipeline').innerHTML = statusBadge;

    const formatDate = window.formatDate || ((d) => new Date(d).toLocaleString('fr-FR'));
    document.getElementById('mc-start-time').textContent = formatDate(session.created_at);

    const TERMINAL = ['COMPLETED', 'ABORTED', 'ERROR', 'FAILED'];
    if (TERMINAL.includes(session.status)) {
      try {
        const costs = await window.API.getPipelineCosts(pipelineSessionId);
        const total = Array.isArray(costs)
          ? costs.reduce((sum, c) => sum + (c.cost_usd || 0), 0)
          : (costs.total_cost_usd || 0);
        const costBadge = window.costBadge ? window.costBadge(total) : `<span class="badge">$${total.toFixed(4)}</span>`;
        document.getElementById('mc-total-cost').innerHTML = ' — ' + costBadge;
      } catch (e) {}
    }

    const btnAbort = document.getElementById('btn-abort-pipeline');
    if (TERMINAL.includes(session.status)) {
      btnAbort.style.display = 'none';
    } else {
      btnAbort.style.display = 'block';
    }
  }

  function renderSteps(session) {
    const container = document.getElementById('mc-steps-list');
    if (!session.steps || session.steps.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:1rem">Aucun step</p>';
      return;
    }

    const mainSteps = session.steps.filter(s => s.sub_step_index == null);
    const subStepsByIndex = {};
    session.steps.filter(s => s.sub_step_index != null).forEach(s => {
      if (!subStepsByIndex[s.step_index]) subStepsByIndex[s.step_index] = [];
      subStepsByIndex[s.step_index].push(s);
    });

    const sorted = [...mainSteps].sort((a, b) => a.step_index - b.step_index);
    container.innerHTML = sorted.map(step => renderStepCard(step, subStepsByIndex[step.step_index] || [])).join('');
  }

  function renderStepCard(step, subSteps) {
    const statusClass = {
      PENDING: 'step-card--pending', RUNNING: 'step-card--running',
      COMPLETED: 'step-card--completed', ERROR: 'step-card--error',
      FAILED: 'step-card--error', WAITING_VALIDATION: 'step-card--waiting'
    }[step.status] || '';

    const indicator = {
      PENDING: '<span style="color:var(--text-muted)">○</span>',
      RUNNING: '<div class="spinner"></div>',
      COMPLETED: '✅', ERROR: '<span style="color:var(--danger)">✕</span>',
      FAILED: '<span style="color:var(--danger)">✕</span>',
      WAITING_VALIDATION: '⏸️'
    }[step.status] || '○';

    let chunkingHTML = '';
    if (subSteps.length > 0) {
      const done = subSteps.filter(s => s.status === 'COMPLETED').length;
      if (step.status === 'RUNNING') {
        chunkingHTML = `<div class="chunking-progress">⚡ Découpage actif — ${done}/${subSteps.length} traité(s)…</div>`;
      } else if (step.status === 'COMPLETED') {
        chunkingHTML = `<div class="chunking-info">⚡ Découpé en ${subSteps.length} appel(s) LLM</div>`;
      }
    }

    let outputHTML = '';
    if (step.status === 'COMPLETED' && step.output_data) {
      if (step.output_type === 'cadrage_report') {
        outputHTML = renderCadrageReportInline(step.output_data, step.id);
      } else {
        const preview = typeof step.output_data === 'string'
          ? step.output_data.substring(0, 120)
          : JSON.stringify(step.output_data).substring(0, 120);
        outputHTML = `<div class="step-output">${preview}${preview.length >= 120 ? '…' : ''}</div>`;
      }
    }

    let errorHTML = '';
    if ((step.status === 'ERROR' || step.status === 'FAILED') && step.error_message) {
      errorHTML = `<div class="step-error">❌ ${step.error_message}</div>`;
    }

    let buttonsHTML = '';
    if (step.status === 'ERROR' || step.status === 'FAILED') {
      buttonsHTML = `<button class="btn-icon" onclick="window._missionRetryStep(${step.id})" title="Relancer">🔄</button>`;
    }

    return `
      <div class="step-card ${statusClass}" data-step-id="${step.id}">
        <div class="step-card-left">
          <div class="step-indicator">${indicator}</div>
          <div class="step-index">${step.step_index + 1}</div>
        </div>
        <div class="step-card-body">
          <div class="step-name">${step.step_display_name || step.step_type}</div>
          <div class="step-meta"><span class="text-muted">${step.model_used || step.model_type || ''}</span></div>
          ${chunkingHTML}${outputHTML}${errorHTML}
        </div>
        <div class="step-card-right">${buttonsHTML}</div>
      </div>`;
  }

  function renderCadrageReportInline(outputData, stepId) {
    let report;
    try { report = typeof outputData === 'string' ? JSON.parse(outputData) : outputData; } catch (e) {
      return `<div class="step-output">${String(outputData).substring(0, 120)}</div>`;
    }
    if (!report || !report.verdict_global) return '';

    const icons = { vert: '🟢', orange: '🟠', rouge: '🔴' };
    const labels = { vert: 'Cadrage OK', orange: 'Point d\'attention', rouge: 'Problème détecté' };
    const icon = icons[report.verdict_global] || '❓';
    const label = labels[report.verdict_global] || report.verdict_global;
    const warnings = (report.checks || []).filter(c => c.statut === 'orange' || c.statut === 'rouge').length;
    const summary = warnings > 0 ? `${warnings} point(s) d'attention` : 'tout vert';

    const checksHtml = (report.checks || []).map(c => {
      const ci = { vert: '✓', orange: '⚠', rouge: '✗' }[c.statut] || '?';
      const cc = { vert: '#10b981', orange: '#f59e0b', rouge: '#ef4444' }[c.statut] || '#6b7280';
      return `<div style="font-size:0.8rem;margin-top:0.4rem;color:${cc}">${ci} ${c.nom || c.id} — ${c.message || ''}</div>`;
    }).join('');

    const detailId = `cadrage-detail-${stepId}`;
    return `
      <div class="step-output" style="padding:0">
        <div style="display:flex;align-items:center;gap:0.5rem;cursor:pointer;padding:0.5rem 0"
             onclick="(function(){var d=document.getElementById('${detailId}');d.style.display=d.style.display==='none'?'block':'none'})()">
          <span>${icon} ${label}</span>
          <span style="color:var(--text-muted);font-size:0.8rem">(${summary})</span>
          <span style="margin-left:auto;color:var(--text-muted);font-size:0.75rem">▾ détails</span>
        </div>
        <div id="${detailId}" style="display:none;border-top:1px solid var(--border);padding-top:0.5rem">
          ${checksHtml || '<span style="color:var(--text-muted);font-size:0.8rem">Aucun check</span>'}
        </div>
      </div>`;
  }

  function renderActionZone(session) {
    const actionZone = document.getElementById('mc-action-zone');
    const TERMINAL = ['COMPLETED', 'ABORTED', 'ERROR', 'FAILED'];

    if (TERMINAL.includes(session.status)) {
      if (session.status === 'COMPLETED') {
        // Passer à l'étape ④ Suivi
        setActiveStep(4);
        document.getElementById('step-4-placeholder').style.display = 'none';
        document.getElementById('step-4-content').style.display = 'block';

        // Récap final dans step-4
        const recapFinal = document.getElementById('recap-final');
        if (recapFinal) {
          const formatDate = window.formatDate || ((d) => new Date(d).toLocaleString('fr-FR'));
          recapFinal.innerHTML = `
            <div class="mc-action-header" style="margin-bottom:0.75rem">
              <h3>✅ Pipeline terminé</h3>
            </div>
            <div style="font-size:0.875rem;color:var(--text-muted)">
              Démarré le ${formatDate(session.created_at)}
            </div>
            <p style="color:var(--text-muted);font-size:0.875rem">
              Consultez le dossier projet pour voir les fichiers générés.
            </p>`;
        }

        // Bouton retour au dossier
        const btnBack = document.getElementById('btn-back-project');
        if (btnBack) btnBack.href = projectId ? `dossier.html?id=${projectId}` : 'index.html';
        const footerEl = document.getElementById('step-4-footer');
        if (footerEl) footerEl.style.display = 'block';

        actionZone.style.display = 'none';
        return;
      }

      // ABORTED / ERROR / FAILED : garder le récap dans mc-action-zone
      actionZone.style.display = 'block';
      const emoji = '❌';
      const label = { ABORTED: 'Session abandonnée', ERROR: 'Session en erreur', FAILED: 'Session échouée' }[session.status] || session.status;

      const failedStep = session.steps?.find(s => s.status === 'FAILED' || s.status === 'ERROR');
      const errorDetail = failedStep?.error_message
        ? `<div class="mc-error-detail"><strong>Étape :</strong> ${failedStep.step_display_name || failedStep.step_type}<br><code>${failedStep.error_message}</code></div>`
        : '';

      const backLink = projectId
        ? `<a href="dossier.html?id=${projectId}" class="btn-secondary">📁 Retour au dossier</a>`
        : `<a href="index.html" class="btn-secondary">🏠 Tableau de bord</a>`;

      actionZone.innerHTML = `
        <div class="mc-action-header"><h3>${emoji} ${label}</h3>${errorDetail}</div>
        <div class="mc-validation-actions">${backLink}</div>`;
      return;
    }

    // Cas spécial : session en WAITING_VALIDATION avec une étape FAILED (rejet utilisateur)
    const rejectedStep = session.steps?.find(s => s.status === 'FAILED' && s.error_message);
    if (session.status === 'WAITING_VALIDATION' && rejectedStep) {
      actionZone.style.display = 'block';
      actionZone.innerHTML = `
        <div class="mc-action-header">
          <h3>❌ Étape rejetée</h3>
          <p class="text-muted"><strong>${rejectedStep.step_display_name || rejectedStep.step_name}</strong></p>
        </div>
        <div class="mc-error-detail">
          <strong>Votre feedback :</strong><br>
          <code>${rejectedStep.error_message}</code>
        </div>
        <div class="mc-validation-actions">
          <button class="btn-primary" onclick="window._missionRetryStep(${rejectedStep.id})">🔄 Relancer cette étape</button>
        </div>`;
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
    const renderDiffFn = window.renderDiff || ((t) => `<pre>${t}</pre>`);
    const diffContent = typeof step.output_data === 'string'
      ? renderDiffFn(step.output_data)
      : `<pre>${JSON.stringify(step.output_data, null, 2)}</pre>`;
    return `
      <div class="mc-action-header">
        <h3>⏸️ ${step.step_display_name || step.step_type} — Validation requise</h3>
        <p class="text-muted">L'IA propose les modifications suivantes :</p>
      </div>
      <div class="mc-diff-container">${diffContent}</div>
      <div class="mc-validation-form">
        <label>Feedback (optionnel)</label>
        <textarea id="mc-feedback-input" placeholder="Commentaires pour l'IA…" rows="2"></textarea>
        <div class="mc-validation-actions">
          <button id="btn-approve" class="btn-primary">✅ Approuver et continuer</button>
          <button id="btn-reject" class="btn-danger">❌ Rejeter</button>
        </div>
      </div>`;
  }

  function renderGenericValidation(step) {
    const renderMarkdown = window.renderMarkdown || ((t) => `<pre>${t}</pre>`);
    let outputHTML = '';
    if (step.output_data) {
      const content = typeof step.output_data === 'string' ? step.output_data : JSON.stringify(step.output_data, null, 2);
      outputHTML = `<div class="mc-output-preview">${renderMarkdown(content)}</div>`;
    }
    return `
      <div class="mc-action-header"><h3>⏸️ ${step.step_display_name || step.step_type} — Validation requise</h3></div>
      ${outputHTML}
      <div class="mc-validation-form">
        <label>Feedback (optionnel)</label>
        <textarea id="mc-feedback-input" placeholder="Commentaires…" rows="2"></textarea>
        <div class="mc-validation-actions">
          <button id="btn-approve" class="btn-primary">✅ Approuver et continuer</button>
          <button id="btn-reject" class="btn-danger">❌ Rejeter</button>
        </div>
      </div>`;
  }

  function attachValidationHandlers(step) {
    const btnApprove = document.getElementById('btn-approve');
    const btnReject = document.getElementById('btn-reject');
    if (btnApprove) {
      btnApprove.onclick = async () => {
        const fb = document.getElementById('mc-feedback-input')?.value || '';
        await handleValidation(step.id, true, fb);
      };
    }
    if (btnReject) {
      btnReject.onclick = async () => {
        const fb = document.getElementById('mc-feedback-input')?.value || '';
        if (!fb.trim()) { window.showToast('Un feedback est requis pour rejeter', 'warning'); return; }
        await handleValidation(step.id, false, fb);
      };
    }
  }

  async function handleValidation(stepId, approved, feedback) {
    const btnApprove = document.getElementById('btn-approve');
    const btnReject = document.getElementById('btn-reject');
    if (btnApprove) btnApprove.disabled = true;
    if (btnReject) btnReject.disabled = true;
    try {
      await window.API.validateStep(pipelineSessionId, stepId, { approved, feedback: feedback || '' });
      await loadPipelineSession();
    } catch (error) {
      window.showToast(error.message || 'Erreur validation', 'error');
      if (btnApprove) btnApprove.disabled = false;
      if (btnReject) btnReject.disabled = false;
    }
  }

  async function handleAbortPipeline() {
    if (!confirm('Abandonner ce pipeline ? Cette action est irréversible.')) return;
    try {
      await window.API.abortPipeline(pipelineSessionId);
      window.showToast('Pipeline abandonné');
      await loadPipelineSession();
    } catch (error) {
      window.showToast('Erreur abandon : ' + error.message, 'error');
    }
  }

  // ── Fonctions globales exposées ───────────────────────────────────
  window._missionRetryStep = async function (stepId) {
    try {
      await window.API.retryStep(pipelineSessionId, stepId);
      window.showToast('Step relancé');
      await loadPipelineSession();
    } catch (error) {
      window.showToast('Erreur relance : ' + error.message, 'error');
    }
  };

  // ── Event Listeners ───────────────────────────────────────────────
  function setupEventListeners() {
    // Zone 1 : créer éléments d'attachement pour réflexion
    const reflexionInputArea = document.getElementById('reflexion-input-area');
    if (reflexionInputArea) {
      const btnSend = document.getElementById('btn-send-message');
      
      const attachBtn = document.createElement('button');
      attachBtn.id = 'attach-btn-reflexion';
      attachBtn.className = 'attach-btn';
      attachBtn.title = 'Joindre une image';
      attachBtn.textContent = '📎';
      attachBtn.type = 'button';

      const attachInput = document.createElement('input');
      attachInput.type = 'file';
      attachInput.id = 'attach-input-reflexion';
      attachInput.accept = 'image/png,image/jpeg,image/webp';
      attachInput.style.display = 'none';

      const attachPreview = document.createElement('div');
      attachPreview.id = 'attach-preview-reflexion';
      attachPreview.className = 'attach-preview';
      attachPreview.style.display = 'none';
      attachPreview.innerHTML = `
        <span id="attach-filename-reflexion" class="attach-filename"></span>
        <button id="attach-clear-reflexion" class="attach-clear" type="button">✕</button>
      `;

      reflexionInputArea.insertBefore(attachBtn, btnSend);
      reflexionInputArea.appendChild(attachInput);
      reflexionInputArea.appendChild(attachPreview);

      // Event listeners attachement
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
          attachedImageReflexion = {
            base64: base64,
            filename: file.name
          };
          document.getElementById('attach-filename-reflexion').textContent = file.name;
          document.getElementById('attach-preview-reflexion').style.display = 'flex';
        };
        reader.readAsDataURL(file);
      });

      document.addEventListener('click', (e) => {
        if (e.target && e.target.id === 'attach-clear-reflexion') {
          attachedImageReflexion = null;
          document.getElementById('attach-preview-reflexion').style.display = 'none';
          document.getElementById('attach-input-reflexion').value = '';
        }
      });
    }
    
    // Zone 1 : envoi message
    document.getElementById('btn-send-message')?.addEventListener('click', sendMessage);
    document.getElementById('reflexion-input')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.ctrlKey) sendMessage();
    });

    // Zone 1 : figer
    document.getElementById('btn-figer')?.addEventListener('click', openFigerModal);

    // Zone 1 : abandon
    document.getElementById('btn-abandonner')?.addEventListener('click', abandonSession);

    // Zone 1 : toggle cadrage
    document.getElementById('btn-toggle-cadrage')?.addEventListener('click', () => {
      const details = document.getElementById('cadrage-details');
      const btn = document.getElementById('btn-toggle-cadrage');
      const isHidden = details.style.display === 'none';
      details.style.display = isHidden ? 'block' : 'none';
      btn.textContent = isHidden ? '▴' : '▾';
    });

    // Modal figement
    document.getElementById('modal-figer-close')?.addEventListener('click', () => {
      document.getElementById('modal-figer').style.display = 'none';
    });
    document.getElementById('modal-figer-cancel')?.addEventListener('click', () => {
      document.getElementById('modal-figer').style.display = 'none';
    });
    document.getElementById('modal-figer-confirm')?.addEventListener('click', confirmFiger);

    // Zone 2 : copier livrable
    document.getElementById('btn-copy-livrable')?.addEventListener('click', copyLivrable);

    // Zone 2 : exécuter mission
    document.getElementById('btn-execute-mission')?.addEventListener('click', executeMission);

    // Zone 2 : appliquer décision
    document.getElementById('btn-apply-decision')?.addEventListener('click', applyDecision);

    // Modal diff
    document.getElementById('modal-diff-close')?.addEventListener('click', () => {
      document.getElementById('modal-diff').style.display = 'none';
    });
    document.getElementById('modal-diff-reject')?.addEventListener('click', () => {
      document.getElementById('modal-diff').style.display = 'none';
      pendingEdit = null;
    });
    document.getElementById('modal-diff-apply')?.addEventListener('click', async () => {
      if (pendingEdit && reflexionSessionId) {
        try {
          await window.API.applyEdit(reflexionSessionId, pendingEdit.file_path, pendingEdit.new_content);
          window.showToast('Édition appliquée', 'success');
          document.getElementById('modal-diff').style.display = 'none';
          pendingEdit = null;

          // Complétion visuelle pour decision_figee
          if (currentLivrableType === 'decision_figee') {
            setActiveStep(4);
            document.getElementById('step-4-placeholder').style.display = 'none';
            document.getElementById('step-4-content').style.display = 'block';

            const step4Content = document.getElementById('step-4-content');
            if (step4Content) {
              step4Content.innerHTML = `
                <div class="recap-fichiers">
                  <p>✅ <strong>Décision appliquée</strong> — PROJET_CONTEXTE.md mis à jour.</p>
                  <p style="color:var(--text-muted);margin-top:0.5rem">
                    La décision figée a été intégrée dans la section 6 de votre document de référence.
                  </p>
                </div>
              `;
            }

            const btnBack = document.getElementById('btn-back-project');
            if (btnBack) btnBack.href = projectId ? `dossier.html?id=${projectId}` : 'index.html';
            const footerEl = document.getElementById('step-4-footer');
            if (footerEl) footerEl.style.display = 'block';
          }
        } catch (error) {
          window.showToast('Erreur application : ' + error.message, 'error');
        }
      }
    });

    // Zone 3 : abandonner pipeline
    document.getElementById('btn-abort-pipeline')?.addEventListener('click', handleAbortPipeline);

    // Nettoyage polling au déchargement
    window.addEventListener('beforeunload', stopPolling);
  }

})();
