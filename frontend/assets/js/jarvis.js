(function () {
  'use strict';

  let currentSessionId = null;
  let lastMessageId = 0;
  let pollInterval = null;
  let isSending = false;

  // ─── Boot ───────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', async () => {
    await window.initSidebar();
    await loadSessions();
    attachStaticHandlers();
  });

  // ─── Session loading ─────────────────────────────────────────────────────────

  async function loadSessions() {
    try {
      let sessions = await window.API.listJarvisSessions();

      if (sessions.length === 0) {
        const s = await window.API.createJarvisSession('Session Jarvis');
        sessions = [s];
      }

      const select = document.getElementById('jarvis-session-select');
      select.innerHTML = sessions
        .map(s => `<option value="${s.id}">${s.title} #${s.id}</option>`)
        .join('');

      const urlId = window.getURLParam ? parseInt(window.getURLParam('session')) : NaN;
      const target = sessions.find(s => s.id === urlId) || sessions[0];
      select.value = target.id;

      await openSession(target.id);

      select.addEventListener('change', () => openSession(parseInt(select.value)));
    } catch (err) {
      showFatalError('Impossible de charger les sessions Jarvis : ' + err.message);
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
      showFatalError('Impossible de charger la session : ' + err.message);
    }
  }

  // ─── Static event handlers (session buttons, input) ──────────────────────────

  function attachStaticHandlers() {
    document.getElementById('btn-new-jarvis-session').addEventListener('click', async () => {
      try {
        const session = await window.API.createJarvisSession('Session Jarvis');
        const select = document.getElementById('jarvis-session-select');
        const opt = document.createElement('option');
        opt.value = session.id;
        opt.textContent = `${session.title} #${session.id}`;
        select.insertBefore(opt, select.firstChild);
        select.value = session.id;
        await openSession(session.id);
      } catch (err) {
        toast('Erreur : ' + err.message, 'error');
      }
    });

    document.getElementById('btn-delete-jarvis-session').addEventListener('click', async () => {
      if (!currentSessionId) return;
      if (!confirm('Supprimer cette session Jarvis et tous ses messages ?')) return;
      try {
        await window.API.deleteJarvisSession(currentSessionId);
        window.location.reload();
      } catch (err) {
        toast('Erreur : ' + err.message, 'error');
      }
    });

    const textarea = document.getElementById('jarvis-input');
    const sendBtn = document.getElementById('jarvis-send-btn');

    textarea.addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    textarea.addEventListener('input', () => autoResize(textarea));
    sendBtn.addEventListener('click', sendMessage);
    textarea.focus();
  }

  // ─── Render messages ─────────────────────────────────────────────────────────

  function renderMessages(messages) {
    const container = document.getElementById('jarvis-messages');
    container.innerHTML = '';

    if (messages.length === 0) {
      container.innerHTML = `
        <div class="jarvis-empty">
          <div style="font-size:2rem;margin-bottom:12px">⚡</div>
          <div>Bonjour ! Je suis JARVIS, votre orchestrateur IA.</div>
          <div style="font-size:0.82rem;color:var(--text-muted);margin-top:6px">
            Posez-moi une question, ou dites-moi de lancer un agent.
          </div>
        </div>`;
      return;
    }

    messages.forEach(msg => appendMessageEl(buildMessageEl(msg)));
    scrollToBottom();
  }

  function appendMessageEl(el) {
    const container = document.getElementById('jarvis-messages');
    container.appendChild(el);
  }

  function buildMessageEl(msg) {
    if (msg.message_type === 'agent_status' || msg.message_type === 'validation_request') {
      return buildAgentCard(msg);
    }
    return buildBubble(msg);
  }

  // ── Text bubble ──────────────────────────────────────────────────────────────

  function buildBubble(msg) {
    const isUser = msg.role === 'user';
    const wrap = document.createElement('div');
    wrap.className = `jarvis-msg jarvis-msg--${isUser ? 'user' : 'jarvis'}`;
    wrap.dataset.msgId = msg.id;

    const content = isUser
      ? escHtml(msg.content).replace(/\n/g, '<br>')
      : (window.renderMarkdown ? window.renderMarkdown(msg.content) : escHtml(msg.content).replace(/\n/g, '<br>'));

    wrap.innerHTML = `
      <div class="jarvis-avatar jarvis-avatar--${isUser ? 'user' : 'jarvis'}">
        ${isUser ? '👤' : '⚡'}
      </div>
      <div class="jarvis-bubble">${content}</div>`;
    return wrap;
  }

  // ── Agent status / validation card ──────────────────────────────────────────

  function buildAgentCard(msg) {
    const isValidation = msg.message_type === 'validation_request';
    const meta = msg.metadata || {};
    const sessionStatus = meta.session_status || '';

    const icons = { code:'⚙️', atelier:'🏭', reflexion:'🧠', sentinelle:'🛡️', chat:'💬' };
    const agentIcon = icons[msg.agent_type] || '🤖';

    let cardMod = '';
    if (isValidation) cardMod = 'agent-status-card--waiting';
    else if (sessionStatus === 'COMPLETED') cardMod = 'agent-status-card--done';
    else if (['FAILED','ABORTED'].includes(sessionStatus)) cardMod = 'agent-status-card--failed';

    const wrap = document.createElement('div');
    wrap.className = 'jarvis-msg jarvis-msg--agent';
    wrap.dataset.msgId = msg.id;

    const lines = msg.content.split('\n');
    const headline = lines[0];
    const rest = lines.slice(1).join('\n').trim();
    const hasPreview = rest.startsWith('---');
    const previewText = hasPreview ? rest.slice(3).trim() : rest;

    let html = `
      <div class="jarvis-avatar jarvis-avatar--agent">${agentIcon}</div>
      <div class="agent-status-card ${cardMod}">
        <div class="agent-status-headline">${escHtml(headline)}</div>`;

    if (previewText) {
      html += `<pre class="agent-status-pre">${escHtml(previewText)}</pre>`;
    }

    if (isValidation && msg.pipeline_session_id && msg.pipeline_step_id) {
      const psId = msg.pipeline_session_id;
      const stepId = msg.pipeline_step_id;
      const msgId = msg.id;
      html += `
        <div class="validation-zone" data-msg-id="${msgId}">
          <div class="validation-actions">
            <button class="btn-validate" data-action="approve" data-msg="${msgId}" data-ps="${psId}" data-step="${stepId}">✅ Valider</button>
            <button class="btn-reject"   data-action="reject"  data-msg="${msgId}" data-ps="${psId}" data-step="${stepId}">❌ Rejeter</button>
          </div>
          <textarea class="validation-feedback" id="feedback-${msgId}" placeholder="Raison du rejet…" style="display:none"></textarea>
          <button class="btn-reject btn-confirm-reject" data-action="confirm-reject" data-msg="${msgId}" data-ps="${psId}" data-step="${stepId}" style="display:none">
            Confirmer le rejet
          </button>
        </div>`;
    }

    html += `</div>`;
    wrap.innerHTML = html;

    // Attach validation events via delegation (no inline onclick)
    wrap.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', handleValidationClick);
    });

    return wrap;
  }

  async function handleValidationClick(e) {
    const btn = e.currentTarget;
    const action = btn.dataset.action;
    const msgId = btn.dataset.msg;
    const psId = parseInt(btn.dataset.ps);
    const stepId = parseInt(btn.dataset.step);

    if (action === 'approve') {
      await submitValidation(msgId, psId, stepId, true, '');
    } else if (action === 'reject') {
      const fb = document.getElementById(`feedback-${msgId}`);
      const confirmBtn = btn.closest('.validation-zone').querySelector('.btn-confirm-reject');
      if (fb) fb.style.display = 'block';
      if (confirmBtn) confirmBtn.style.display = 'inline-block';
    } else if (action === 'confirm-reject') {
      const fb = document.getElementById(`feedback-${msgId}`);
      const feedback = fb ? fb.value.trim() : '';
      await submitValidation(msgId, psId, stepId, false, feedback);
    }
  }

  async function submitValidation(msgId, psId, stepId, approved, feedback) {
    const zone = document.querySelector(`.validation-zone[data-msg-id="${msgId}"]`);
    if (zone) zone.innerHTML = '<span style="color:var(--text-muted);font-size:0.85rem">Traitement…</span>';

    try {
      await window.API.validateJarvisStep(currentSessionId, psId, stepId, { approved, feedback });
      toast(approved ? 'Étape validée' : 'Étape rejetée', approved ? 'success' : 'info');
      await pollNow();
    } catch (err) {
      toast('Erreur : ' + err.message, 'error');
    }
  }

  // ── Thinking card ────────────────────────────────────────────────────────────

  function createThinkingCard() {
    const wrap = document.createElement('div');
    wrap.id = 'jarvis-thinking-card';
    wrap.className = 'jarvis-msg jarvis-msg--jarvis';
    wrap.innerHTML = `
      <div class="jarvis-avatar jarvis-avatar--jarvis">⚡</div>
      <div class="thinking-card">
        <div id="thinking-steps"></div>
      </div>`;
    appendMessageEl(wrap);
    scrollToBottom();
    return wrap;
  }

  function addThinkingStep(content, status = 'active') {
    const steps = document.getElementById('thinking-steps');
    if (!steps) return;

    // Marquer l'étape précédente comme done
    steps.querySelectorAll('.thinking-step.active').forEach(s => {
      s.classList.remove('active');
      s.classList.add('done');
    });

    const el = document.createElement('div');
    el.className = `thinking-step ${status}`;
    el.textContent = content;
    steps.appendChild(el);
    scrollToBottom();
  }

  function removeThinkingCard() {
    const card = document.getElementById('jarvis-thinking-card');
    if (card) card.remove();
  }

  // ─── SSE send message ────────────────────────────────────────────────────────

  async function sendMessage() {
    if (isSending || !currentSessionId) return;
    const textarea = document.getElementById('jarvis-input');
    const content = textarea.value.trim();
    if (!content) return;

    isSending = true;
    textarea.value = '';
    autoResize(textarea);
    document.getElementById('jarvis-send-btn').disabled = true;

    // Bulle utilisateur optimiste
    const userEl = buildBubble({ id: 'tmp', role: 'user', content, message_type: 'text' });
    appendMessageEl(userEl);
    scrollToBottom();

    // Thinking card
    const thinkingCard = createThinkingCard();

    try {
      const response = await fetch(`${window.location.origin}/api/jarvis/sessions/${currentSessionId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, project_id: null }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop(); // Garder l'événement incomplet

        for (const chunk of chunks) {
          if (!chunk.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(chunk.slice(6));
            handleSSEEvent(event);
          } catch (_) { /* ignore malformed */ }
        }
      }
    } catch (err) {
      addThinkingStep('Erreur : ' + err.message, 'error-step');
      toast('Erreur : ' + err.message, 'error');
    } finally {
      removeThinkingCard();
      isSending = false;
      document.getElementById('jarvis-send-btn').disabled = false;
      textarea.focus();
    }
  }

  function handleSSEEvent(event) {
    switch (event.type) {
      case 'thinking':
        addThinkingStep(event.content);
        break;

      case 'message': {
        const msg = event.data;
        if (!msg || !msg.id) break;
        // Supprimer la bulle optimiste si c'est le premier message retourné
        const tmp = document.querySelector('[data-msg-id="tmp"]');
        if (tmp) tmp.remove();
        // Ne pas dupliquer
        if (!document.querySelector(`[data-msg-id="${msg.id}"]`)) {
          appendMessageEl(buildMessageEl(msg));
          if (msg.id > lastMessageId) lastMessageId = msg.id;
          scrollToBottom();
        }
        break;
      }

      case 'agent_status': {
        // Statut agent émis inline pendant le stream
        const msg = event.data;
        if (msg && msg.id && !document.querySelector(`[data-msg-id="${msg.id}"]`)) {
          appendMessageEl(buildMessageEl(msg));
          if (msg.id > lastMessageId) lastMessageId = msg.id;
          scrollToBottom();
        }
        break;
      }

      case 'done':
        // Le stream est terminé — le finally s'en charge
        break;

      case 'error':
        addThinkingStep('Erreur : ' + (event.content || '?'), 'error-step');
        break;
    }
  }

  // ─── Polling (pour les agents en fond) ───────────────────────────────────────

  function startPolling() {
    stopPolling();
    pollInterval = setInterval(pollNow, 3000);
  }

  function stopPolling() {
    if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
  }

  async function pollNow() {
    if (!currentSessionId) return;
    try {
      const result = await window.API.getJarvisAgentUpdates(currentSessionId, lastMessageId);
      const msgs = result.messages || [];
      let appended = false;
      msgs.forEach(msg => {
        if (msg.id > lastMessageId) lastMessageId = msg.id;
        if (!document.querySelector(`[data-msg-id="${msg.id}"]`)) {
          appendMessageEl(buildMessageEl(msg));
          appended = true;
        }
      });
      if (appended) scrollToBottom();
    } catch (_) { /* polling errors silencieux */ }
  }

  // ─── Utilities ───────────────────────────────────────────────────────────────

  function scrollToBottom() {
    const c = document.getElementById('jarvis-messages');
    if (c) requestAnimationFrame(() => { c.scrollTop = c.scrollHeight; });
  }

  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }

  function showFatalError(msg) {
    const c = document.getElementById('jarvis-messages');
    if (c) c.innerHTML = `<div style="color:var(--danger);text-align:center;padding:2rem">${escHtml(msg)}</div>`;
  }

  function toast(msg, type = 'info') {
    if (window.showToast) window.showToast(msg, type);
  }

  function escHtml(str) {
    return window.escapeHtml
      ? window.escapeHtml(str)
      : String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
})();
