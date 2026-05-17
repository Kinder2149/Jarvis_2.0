(function () {
  let currentSessionId = null;
  let lastMessageId = 0;
  let pollInterval = null;
  let sending = false;

  // ─── Init ───────────────────────────────────────────────────────────────────

  async function init() {
    await window.initSidebar();
    await loadSessions();
    attachInputHandlers();
  }

  async function loadSessions() {
    try {
      const sessions = await window.API.listJarvisSessions();
      const select = document.getElementById('jarvis-session-select');

      if (sessions.length === 0) {
        const session = await window.API.createJarvisSession('Session Jarvis');
        sessions.push(session);
      }

      select.innerHTML = sessions
        .map(s => `<option value="${s.id}">${s.title} #${s.id}</option>`)
        .join('');

      // Lire l'ID depuis l'URL ou prendre le plus récent
      const urlId = window.getURLParam ? parseInt(window.getURLParam('session')) : NaN;
      const target = sessions.find(s => s.id === urlId) || sessions[0];

      select.value = target.id;
      await openSession(target.id);

      select.addEventListener('change', () => openSession(parseInt(select.value)));
    } catch (err) {
      console.error('[JARVIS] loadSessions error:', err);
      showError('Impossible de charger les sessions Jarvis.');
    }
  }

  async function openSession(sessionId) {
    stopPolling();
    currentSessionId = sessionId;
    lastMessageId = 0;

    try {
      const data = await window.API.getJarvisSession(sessionId);
      renderMessages(data.messages || []);
      if (data.messages && data.messages.length > 0) {
        lastMessageId = data.messages[data.messages.length - 1].id;
      }
      startPolling();
    } catch (err) {
      console.error('[JARVIS] openSession error:', err);
      showError('Impossible de charger la session.');
    }
  }

  // ─── Rendering ──────────────────────────────────────────────────────────────

  function renderMessages(messages) {
    const container = document.getElementById('jarvis-messages');
    container.innerHTML = '';

    if (messages.length === 0) {
      container.innerHTML = `
        <div style="color:var(--text-muted);text-align:center;margin-top:60px;font-size:0.9rem">
          ⚡ Bonjour ! Je suis JARVIS, votre orchestrateur IA.<br>
          <span style="font-size:0.82rem">Posez-moi une question, demandez-moi de lancer un agent, ou dites-moi ce que vous voulez faire.</span>
        </div>`;
      return;
    }

    messages.forEach(msg => appendMessage(msg));
    scrollToBottom();
  }

  function appendMessage(msg) {
    const container = document.getElementById('jarvis-messages');

    if (msg.message_type === 'agent_status' || msg.message_type === 'validation_request') {
      container.appendChild(buildAgentCard(msg));
    } else {
      container.appendChild(buildBubble(msg));
    }
  }

  function buildBubble(msg) {
    const isUser = msg.role === 'user';
    const wrapper = document.createElement('div');
    wrapper.className = `jarvis-msg jarvis-msg--${isUser ? 'user' : 'jarvis'}`;
    wrapper.dataset.msgId = msg.id;

    const avatarChar = isUser ? '👤' : '⚡';
    const avatarClass = isUser ? 'jarvis-avatar--user' : 'jarvis-avatar--jarvis';
    const content = window.renderMarkdown
      ? window.renderMarkdown(msg.content)
      : escapeAndBreak(msg.content);

    wrapper.innerHTML = `
      <div class="jarvis-avatar ${avatarClass}">${avatarChar}</div>
      <div class="jarvis-bubble">${content}</div>`;

    return wrapper;
  }

  function buildAgentCard(msg) {
    const isValidation = msg.message_type === 'validation_request';
    const agentIcons = {
      code: '⚙️', atelier: '🏭', reflexion: '🧠',
      sentinelle: '🛡️', chat: '💬', unknown: '🤖'
    };
    const agentIcon = agentIcons[msg.agent_type] || '🤖';

    const meta = msg.metadata || {};
    const sessionStatus = meta.session_status || '';
    let cardClass = 'agent-status-card';
    if (isValidation) cardClass += ' agent-status-card--waiting';
    else if (['COMPLETED'].includes(sessionStatus)) cardClass += ' agent-status-card--done';
    else if (['FAILED', 'ABORTED'].includes(sessionStatus)) cardClass += ' agent-status-card--failed';

    const wrapper = document.createElement('div');
    wrapper.className = `jarvis-msg jarvis-msg--agent`;
    wrapper.dataset.msgId = msg.id;

    const lines = msg.content.split('\n');
    const firstLine = lines[0];
    const rest = lines.slice(1).join('\n').trim();

    let cardHTML = `
      <div class="${cardClass}">
        <div style="font-weight:600;font-size:0.85rem">${agentIcon} ${escapeHtml(firstLine)}</div>`;

    if (rest) {
      const previewText = rest.startsWith('---') ? rest.slice(3).trim() : rest;
      cardHTML += `<pre>${escapeHtml(previewText)}</pre>`;
    }

    if (isValidation && msg.pipeline_session_id && msg.pipeline_step_id) {
      cardHTML += `
        <div class="validation-actions" data-ps="${msg.pipeline_session_id}" data-step="${msg.pipeline_step_id}">
          <button class="btn-validate" onclick="jarvisValidate(${msg.id}, ${msg.pipeline_session_id}, ${msg.pipeline_step_id}, true)">✅ Valider</button>
          <button class="btn-reject"   onclick="jarvisShowReject(${msg.id})">❌ Rejeter</button>
          <textarea id="feedback-${msg.id}" class="validation-feedback" placeholder="Raison du rejet…"></textarea>
          <button id="btn-confirm-reject-${msg.id}" class="btn-reject" style="display:none"
            onclick="jarvisValidate(${msg.id}, ${msg.pipeline_session_id}, ${msg.pipeline_step_id}, false)">Confirmer le rejet</button>
        </div>`;
    }

    cardHTML += `</div>`;
    wrapper.innerHTML = `<div class="jarvis-avatar jarvis-avatar--agent">${agentIcon}</div>${cardHTML}`;
    return wrapper;
  }

  function addTypingIndicator() {
    removeTypingIndicator();
    const container = document.getElementById('jarvis-messages');
    const el = document.createElement('div');
    el.id = 'jarvis-typing';
    el.className = 'jarvis-msg jarvis-msg--jarvis';
    el.innerHTML = `
      <div class="jarvis-avatar jarvis-avatar--jarvis">⚡</div>
      <div class="jarvis-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>`;
    container.appendChild(el);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const el = document.getElementById('jarvis-typing');
    if (el) el.remove();
  }

  // ─── Send message ────────────────────────────────────────────────────────────

  async function sendMessage() {
    if (sending || !currentSessionId) return;
    const textarea = document.getElementById('jarvis-input');
    const content = textarea.value.trim();
    if (!content) return;

    sending = true;
    textarea.value = '';
    autoResizeTextarea(textarea);
    document.getElementById('jarvis-send-btn').disabled = true;

    // Append optimistic user bubble
    const container = document.getElementById('jarvis-messages');
    const optimistic = document.createElement('div');
    optimistic.className = 'jarvis-msg jarvis-msg--user';
    optimistic.innerHTML = `
      <div class="jarvis-avatar jarvis-avatar--user">👤</div>
      <div class="jarvis-bubble">${escapeHtml(content)}</div>`;
    container.appendChild(optimistic);
    scrollToBottom();

    addTypingIndicator();

    try {
      const result = await window.API.sendJarvisMessage(currentSessionId, { content });
      removeTypingIndicator();
      optimistic.remove();

      const msgs = result.messages || [];
      msgs.forEach(msg => {
        if (!document.querySelector(`[data-msg-id="${msg.id}"]`)) {
          appendMessage(msg);
          if (msg.id > lastMessageId) lastMessageId = msg.id;
        }
      });
      scrollToBottom();
    } catch (err) {
      removeTypingIndicator();
      optimistic.remove();
      console.error('[JARVIS] sendMessage error:', err);
      window.showToast && window.showToast('Erreur : ' + err.message, 'error');
    } finally {
      sending = false;
      document.getElementById('jarvis-send-btn').disabled = false;
      textarea.focus();
    }
  }

  // ─── Polling ─────────────────────────────────────────────────────────────────

  function startPolling() {
    stopPolling();
    pollInterval = setInterval(pollAgentUpdates, 5000);
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  }

  async function pollAgentUpdates() {
    if (!currentSessionId) return;
    try {
      const result = await window.API.getJarvisAgentUpdates(currentSessionId, lastMessageId);
      const msgs = result.messages || [];
      msgs.forEach(msg => {
        if (msg.id > lastMessageId) lastMessageId = msg.id;
        const existing = document.querySelector(`[data-msg-id="${msg.id}"]`);
        if (!existing) {
          appendMessage(msg);
          scrollToBottom();
        }
      });
    } catch (err) {
      // Polling errors are silent
    }
  }

  // ─── Validation ─────────────────────────────────────────────────────────────

  window.jarvisValidate = async function (msgId, pipelineSessionId, stepId, approved) {
    const feedbackEl = document.getElementById(`feedback-${msgId}`);
    const feedback = feedbackEl ? feedbackEl.value.trim() : '';

    const card = document.querySelector(`[data-msg-id="${msgId}"]`);
    const actions = card ? card.querySelector('.validation-actions') : null;
    if (actions) {
      actions.innerHTML = '<span style="color:var(--text-muted);font-size:0.85rem">Traitement…</span>';
    }

    try {
      await window.API.validateJarvisStep(currentSessionId, pipelineSessionId, stepId, {
        approved,
        feedback,
      });

      // Forcer un poll immédiat
      await pollAgentUpdates();
      window.showToast && window.showToast(approved ? 'Étape validée' : 'Étape rejetée', approved ? 'success' : 'info');
    } catch (err) {
      console.error('[JARVIS] validate error:', err);
      window.showToast && window.showToast('Erreur : ' + err.message, 'error');
    }
  };

  window.jarvisShowReject = function (msgId) {
    const feedback = document.getElementById(`feedback-${msgId}`);
    const confirmBtn = document.getElementById(`btn-confirm-reject-${msgId}`);
    if (feedback) feedback.style.display = 'block';
    if (confirmBtn) confirmBtn.style.display = 'inline-block';
  };

  // ─── Session management ──────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn-new-jarvis-session').addEventListener('click', async () => {
      try {
        const session = await window.API.createJarvisSession('Session Jarvis');
        const select = document.getElementById('jarvis-session-select');
        const option = document.createElement('option');
        option.value = session.id;
        option.textContent = `${session.title} #${session.id}`;
        select.insertBefore(option, select.firstChild);
        select.value = session.id;
        await openSession(session.id);
      } catch (err) {
        window.showToast && window.showToast('Erreur : ' + err.message, 'error');
      }
    });

    document.getElementById('btn-delete-jarvis-session').addEventListener('click', async () => {
      if (!currentSessionId) return;
      if (!confirm('Supprimer cette session Jarvis et tous ses messages ?')) return;
      try {
        await window.API.deleteJarvisSession(currentSessionId);
        window.location.reload();
      } catch (err) {
        window.showToast && window.showToast('Erreur : ' + err.message, 'error');
      }
    });
  });

  // ─── Input handlers ──────────────────────────────────────────────────────────

  function attachInputHandlers() {
    const textarea = document.getElementById('jarvis-input');
    const sendBtn = document.getElementById('jarvis-send-btn');

    textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    textarea.addEventListener('input', () => autoResizeTextarea(textarea));
    sendBtn.addEventListener('click', sendMessage);
    textarea.focus();
  }

  function autoResizeTextarea(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }

  // ─── Utilities ───────────────────────────────────────────────────────────────

  function scrollToBottom() {
    const container = document.getElementById('jarvis-messages');
    if (container) container.scrollTop = container.scrollHeight;
  }

  function showError(msg) {
    const container = document.getElementById('jarvis-messages');
    if (container) {
      container.innerHTML = `<div style="color:var(--danger);text-align:center;padding:2rem">${escapeHtml(msg)}</div>`;
    }
  }

  function escapeHtml(str) {
    return window.escapeHtml ? window.escapeHtml(str) : String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function escapeAndBreak(str) {
    return escapeHtml(str).replace(/\n/g, '<br>');
  }

  // ─── Boot ────────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', init);
})();
