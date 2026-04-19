// ========================================
// ADMIN.JS — TEMPLATE GÉNÉRIQUE
// L'Atelier Connecté — Démos restauration
// ========================================
//
// ⚠️  RÈGLES ABSOLUES — NE JAMAIS MODIFIER :
// 1. ADMIN_PASSWORD = 'admin2024' — jamais changer ce mot de passe
// 2. Clés localStorage : "actions_recues", "contenu_editable", "menuCard" — jamais d'autres
// 3. Champs réservation : prenom, telephone, service, couverts, message, statut, source
// 4. Valeurs service : "dejeuner" ou "diner" uniquement (minuscules, sans accent)
// 5. Statuts : "En attente", "Confirmée", "Annulée" — exactement ces chaînes
// 6. Répartition démo : 2 En attente · 2 Confirmée · 1 Annulée — toujours
// 7. Aucun alert() — toutes les confirmations sont inline + setTimeout 4000ms

// ========== UTILITAIRES ==========

function offsetDate(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try { return JSON.parse(rawValue); } catch(e) { return fallbackValue; }
}

function formatDateFr(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('fr-FR', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  });
}

function formatDateShort(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('fr-FR', {
    weekday: 'short', day: 'numeric'
  });
}

// ========== MOT DE PASSE ==========
// ⚠️ JAMAIS CHANGER — ni variable ni configurable
const ADMIN_PASSWORD = 'admin2024';

// ========== DONNÉES DÉMO ==========
// ⚠️ Substituer UNIQUEMENT les {{VARIABLES}} — ne pas changer la structure
// Répartition obligatoire : demo-1 En attente · demo-2 Confirmée · demo-3 En attente · demo-4 Confirmée · demo-5 Annulée

function loadDemoData() {
  const existing = localStorage.getItem('actions_recues');
  if (!existing) {
    const DEMO_RESERVATIONS = [
      {
        id: 'demo-1',
        prenom: '{{DEMO_PRENOM_1}}',
        telephone: '{{DEMO_TEL_1}}',
        date: offsetDate(1),
        service: 'diner',
        couverts: '2',
        message: '{{DEMO_MESSAGE_1}}',
        statut: 'En attente',
        source: 'demo'
      },
      {
        id: 'demo-2',
        prenom: '{{DEMO_PRENOM_2}}',
        telephone: '{{DEMO_TEL_2}}',
        date: offsetDate(1),
        service: 'dejeuner',
        couverts: '4',
        message: '',
        statut: 'Confirmée',
        source: 'demo'
      },
      {
        id: 'demo-3',
        prenom: '{{DEMO_PRENOM_3}}',
        telephone: '{{DEMO_TEL_3}}',
        date: offsetDate(2),
        service: 'diner',
        couverts: '6',
        message: '{{DEMO_MESSAGE_3}}',
        statut: 'En attente',
        source: 'demo'
      },
      {
        id: 'demo-4',
        prenom: '{{DEMO_PRENOM_4}}',
        telephone: '{{DEMO_TEL_4}}',
        date: offsetDate(3),
        service: 'dejeuner',
        couverts: '2',
        message: '',
        statut: 'Confirmée',
        source: 'demo'
      },
      {
        id: 'demo-5',
        prenom: '{{DEMO_PRENOM_5}}',
        telephone: '{{DEMO_TEL_5}}',
        date: offsetDate(4),
        service: 'diner',
        couverts: '8',
        message: '{{DEMO_MESSAGE_5}}',
        statut: 'Annulée',
        source: 'demo'
      }
    ];
    localStorage.setItem('actions_recues', JSON.stringify(DEMO_RESERVATIONS));
  }
}

// ========== LOGIN ==========

const loginScreen = document.getElementById('loginScreen');
const adminDashboard = document.getElementById('adminDashboard');
const loginBtn = document.getElementById('loginBtn');
const passwordInput = document.getElementById('passwordInput');
const passwordToggle = document.getElementById('passwordToggle');
const loginError = document.getElementById('loginError');
const logoutBtn = document.getElementById('logoutBtn');

passwordToggle.addEventListener('click', (e) => {
  e.preventDefault();
  const type = passwordInput.type === 'password' ? 'text' : 'password';
  passwordInput.type = type;
  passwordToggle.textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
});

loginBtn.addEventListener('click', (e) => {
  e.preventDefault();
  if (passwordInput.value.trim() === ADMIN_PASSWORD) {
    loginError.classList.remove('show');
    loginScreen.classList.add('hidden');
    adminDashboard.classList.add('show');
    passwordInput.value = '';
    initDashboard();
  } else {
    loginError.textContent = 'Mot de passe incorrect. Veuillez réessayer.';
    loginError.classList.add('show');
    setTimeout(() => loginError.classList.remove('show'), 4000);
  }
});

passwordInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') loginBtn.click();
});

logoutBtn.addEventListener('click', () => {
  adminDashboard.classList.remove('show');
  loginScreen.classList.remove('hidden');
  passwordInput.value = '';
});

// ========== GESTION RÉSERVATIONS ==========

function loadReservations() {
  return safeParse(localStorage.getItem('actions_recues'), []);
}

function saveReservations(reservations) {
  localStorage.setItem('actions_recues', JSON.stringify(reservations));
}

function updateKPIs() {
  const reservations = loadReservations();
  const today = offsetDate(0);
  const weekEnd = offsetDate(6);

  const kpiToday = reservations.filter(r => r.date === today).length;
  const kpiPending = reservations.filter(r => r.statut === 'En attente').length;
  const kpiWeek = reservations.filter(r =>
    r.statut === 'Confirmée' && r.date >= today && r.date <= weekEnd
  ).length;

  document.getElementById('kpiToday').textContent = kpiToday;
  document.getElementById('kpiPending').textContent = kpiPending;
  document.getElementById('kpiConfirmedWeek').textContent = kpiWeek;
}

function confirmReservation(id) {
  const reservations = loadReservations();
  const res = reservations.find(r => r.id === id);
  if (res && res.statut === 'En attente') {
    res.statut = 'Confirmée';
    saveReservations(reservations);
    refreshAllReservationViews();
    showToast('✓ Réservation confirmée !');
  }
}

function cancelReservation(id) {
  const reservations = loadReservations();
  const res = reservations.find(r => r.id === id);
  if (res && res.statut !== 'Annulée') {
    res.statut = 'Annulée';
    saveReservations(reservations);
    refreshAllReservationViews();
    showToast('✓ Réservation annulée.');
  }
}

function refreshAllReservationViews() {
  updateKPIs();
  renderPendingReservations();
  renderReservationsCalendar();
  renderReservationsList();
}

// ========== TOAST (pas d'alert) ==========

function showToast(text) {
  const msg = document.createElement('div');
  msg.className = 'confirmation-message show';
  msg.textContent = text;
  msg.style.position = 'fixed';
  msg.style.top = '2rem';
  msg.style.right = '2rem';
  msg.style.zIndex = '9999';
  document.body.appendChild(msg);
  setTimeout(() => msg.remove(), 4000);
}

// ========== SECTION EN ATTENTE ==========

function renderPendingReservations() {
  const container = document.getElementById('pendingReservationsContainer');
  const pending = loadReservations()
    .filter(r => r.statut === 'En attente')
    .sort((a, b) => a.date.localeCompare(b.date));

  if (pending.length === 0) {
    container.innerHTML = '<p style="color:var(--text-secondary); text-align:center; padding:1rem;">Aucune réservation en attente.</p>';
    return;
  }

  container.innerHTML = pending.map(r => `
    <div class="reservation-card status-attente">
      <div class="reservation-header">
        <div class="reservation-info">
          <h3>${r.prenom}</h3>
          <p>📅 ${formatDateFr(r.date)} — ${r.service === 'dejeuner' ? 'Déjeuner' : 'Dîner'}</p>
          <p>📞 ${r.telephone}</p>
          <p>${r.couverts} couvert${r.couverts !== '1' ? 's' : ''}</p>
        </div>
        <span class="badge badge-attente">En attente</span>
      </div>
      ${r.message ? `<p style="margin:1rem 0 0 0; font-size:0.95rem; color:var(--text-secondary);">💬 ${r.message}</p>` : ''}
      <div class="reservation-actions">
        <button type="button" class="btn-submit" style="padding:0.6rem 1.2rem; width:auto;" onclick="confirmReservation('${r.id}')">✓ Confirmer</button>
        <button type="button" class="btn-danger" style="padding:0.6rem 1.2rem; width:auto;" onclick="cancelReservation('${r.id}')">✗ Annuler</button>
      </div>
    </div>
  `).join('');
}

// ========== CALENDRIER SEMAINE ==========

let selectedDate = offsetDate(0);
let selectedService = 'tous';

function renderReservationsCalendar() {
  const reservations = loadReservations();
  const weekCalendar = document.getElementById('weekCalendar');
  weekCalendar.innerHTML = '';

  for (let i = 0; i < 7; i++) {
    const date = offsetDate(i);
    const count = reservations.filter(r => r.date === date).length;
    const isActive = date === selectedDate;

    const dateObj = new Date(date + 'T00:00:00');
    const dayName = dateObj.toLocaleDateString('fr-FR', { weekday: 'short' }).toUpperCase();

    const dayCell = document.createElement('button');
    dayCell.className = 'day-cell' + (isActive ? ' active' : '');
    dayCell.innerHTML = `
      <strong>${dayName}</strong>
      <span>${dateObj.getDate()}</span>
      <p style="margin:0.5rem 0 0 0; font-size:0.8rem; color:${isActive ? 'rgba(255,255,255,0.8)' : 'var(--text-secondary)'};">${count} rés.</p>
    `;
    dayCell.addEventListener('click', () => {
      document.querySelectorAll('.day-cell').forEach(c => c.classList.remove('active'));
      dayCell.classList.add('active');
      selectedDate = date;
      renderReservationsList();
    });
    weekCalendar.appendChild(dayCell);
  }
}

// ========== FILTRES SERVICE ==========

document.getElementById('filterAll').addEventListener('click', () => {
  setServiceFilter('tous', 'filterAll');
});
document.getElementById('filterDejeuner').addEventListener('click', () => {
  setServiceFilter('dejeuner', 'filterDejeuner');
});
document.getElementById('filterDiner').addEventListener('click', () => {
  setServiceFilter('diner', 'filterDiner');
});

function setServiceFilter(service, activeId) {
  document.querySelectorAll('#filterAll, #filterDejeuner, #filterDiner').forEach(b => b.classList.remove('active'));
  document.getElementById(activeId).classList.add('active');
  selectedService = service;
  renderReservationsList();
}

// ========== LISTE RÉSERVATIONS ==========

function renderReservationsList() {
  const container = document.getElementById('reservationsContainer');
  let filtered = loadReservations().filter(r => r.date === selectedDate);

  if (selectedService !== 'tous') {
    filtered = filtered.filter(r => r.service === selectedService);
  }

  if (filtered.length === 0) {
    container.innerHTML = '<p style="color:var(--text-secondary); text-align:center; padding:1rem;">Aucune réservation pour cette sélection.</p>';
    return;
  }

  container.innerHTML = filtered.map(r => {
    const badgeClass = r.statut === 'Confirmée' ? 'badge-confirme' : r.statut === 'Annulée' ? 'badge-annule' : 'badge-attente';
    const statusClass = r.statut === 'Confirmée' ? 'status-confirme' : r.statut === 'Annulée' ? 'status-annule' : 'status-attente';
    return `
      <div class="reservation-card ${statusClass}">
        <div class="reservation-header">
          <div class="reservation-info">
            <h3>${r.prenom}</h3>
            <p>${r.service === 'dejeuner' ? 'Déjeuner' : 'Dîner'} — ${r.couverts} couvert${r.couverts !== '1' ? 's' : ''}</p>
            <p>📞 ${r.telephone}</p>
          </div>
          <span class="badge ${badgeClass}">${r.statut}</span>
        </div>
        ${r.message ? `<p style="margin:1rem 0 0 0; font-size:0.95rem; color:var(--text-secondary);">💬 ${r.message}</p>` : ''}
        <div class="reservation-actions">
          ${r.statut !== 'Confirmée' ? `<button type="button" class="btn-submit" style="padding:0.6rem 1.2rem; width:auto;" onclick="confirmReservation('${r.id}')">✓ Confirmer</button>` : ''}
          ${r.statut !== 'Annulée' ? `<button type="button" class="btn-danger" style="padding:0.6rem 1.2rem; width:auto;" onclick="cancelReservation('${r.id}')">✗ Annuler</button>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

// ========== ONGLETS NAVIGATION ==========

document.querySelectorAll('.admin-tab[data-tab]').forEach(tab => {
  tab.addEventListener('click', () => {
    const tabName = tab.dataset.tab;
    document.querySelectorAll('.admin-tab[data-tab]').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tabName).classList.add('active');
  });
});

// ========== ARDOISE — STRUCTURE COMPLÈTE ==========
// Structure obligatoire : disponible + entree(nom,prix) + plat(nom,prix,note) + dessert(nom,prix) + formule(active,label,prix)

document.getElementById('formuleActive').addEventListener('change', function() {
  document.getElementById('formuleFields').style.display = this.checked ? 'grid' : 'none';
});

function getArdoiseFromForm() {
  const val = id => document.getElementById(id) ? document.getElementById(id).value.trim() : '';
  const checked = id => document.getElementById(id) ? document.getElementById(id).checked : false;

  return {
    disponible: checked('ardoiseDisponible'),
    entree: val('ardoiseEntree') ? { nom: val('ardoiseEntree'), prix: val('ardoiseEntreePrix') } : null,
    plat: { nom: val('ardoisePlat'), prix: val('ardoisePlatPrix'), note: val('ardoisePlatNote') },
    dessert: val('ardoiseDessert') ? { nom: val('ardoiseDessert'), prix: val('ardoiseDessertPrix') } : null,
    formule: checked('formuleActive')
      ? { active: true, label: val('formuleLabel'), prix: val('formulePrix') }
      : { active: false }
  };
}

function setArdoiseToForm(a) {
  if (!a) return;
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v || ''; };
  const check = (id, v) => { const el = document.getElementById(id); if (el) el.checked = !!v; };

  check('ardoiseDisponible', a.disponible !== false);
  if (a.entree) { set('ardoiseEntree', a.entree.nom); set('ardoiseEntreePrix', a.entree.prix); }
  if (a.plat) { set('ardoisePlat', a.plat.nom); set('ardoisePlatPrix', a.plat.prix); set('ardoisePlatNote', a.plat.note); }
  if (a.dessert) { set('ardoiseDessert', a.dessert.nom); set('ardoiseDessertPrix', a.dessert.prix); }
  if (a.formule && a.formule.active) {
    check('formuleActive', true);
    document.getElementById('formuleFields').style.display = 'grid';
    set('formuleLabel', a.formule.label);
    set('formulePrix', a.formule.prix);
  }
  updateArdoisePreview();
}

document.getElementById('ardoiseSaveBtn').addEventListener('click', () => {
  const plat = document.getElementById('ardoisePlat').value.trim();
  const prix = document.getElementById('ardoisePlatPrix').value.trim();
  if (!plat || !prix) { showToast('⚠️ Plat du jour et prix sont obligatoires.'); return; }

  const contenu = safeParse(localStorage.getItem('contenu_editable'), {});
  contenu.ardoise = getArdoiseFromForm();
  localStorage.setItem('contenu_editable', JSON.stringify(contenu));

  updateArdoisePreview();

  const msg = document.getElementById('ardoiseConfirmation');
  msg.classList.add('show');
  setTimeout(() => msg.classList.remove('show'), 4000);
});

['ardoiseEntree','ardoiseEntreePrix','ardoisePlat','ardoisePlatPrix','ardoisePlatNote',
 'ardoiseDessert','ardoiseDessertPrix','formuleLabel','formulePrix'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener('input', updateArdoisePreview);
});

document.getElementById('ardoiseDisponible').addEventListener('change', updateArdoisePreview);

function updateArdoisePreview() {
  const preview = document.getElementById('ardoisePreviewContent');
  if (!preview) return;
  const a = getArdoiseFromForm();

  if (!a.disponible) {
    preview.innerHTML = '<p style="color:var(--text-secondary); font-style:italic;">Ardoise masquée sur le site aujourd\'hui.</p>';
    return;
  }

  let html = '';
  if (a.entree) html += `<p style="margin:0 0 0.5rem 0;"><strong>Entrée :</strong> ${a.entree.nom} <span style="color:var(--accent); font-weight:700;">${a.entree.prix}</span></p>`;
  if (a.plat && a.plat.nom) html += `<p style="margin:0 0 0.25rem 0;"><strong>Plat :</strong> ${a.plat.nom} <span style="color:var(--accent); font-weight:700;">${a.plat.prix}</span></p>`;
  if (a.plat && a.plat.note) html += `<p style="margin:0 0 0.5rem 1rem; font-size:0.9rem; color:var(--text-secondary); font-style:italic;">${a.plat.note}</p>`;
  if (a.dessert) html += `<p style="margin:0 0 0.5rem 0;"><strong>Dessert :</strong> ${a.dessert.nom} <span style="color:var(--accent); font-weight:700;">${a.dessert.prix}</span></p>`;
  if (a.formule && a.formule.active && a.formule.label) {
    html += `<hr style="border:none; border-top:1px solid var(--border-soft); margin:0.75rem 0;">`;
    html += `<p style="margin:0; color:var(--accent); font-weight:700;">Formule : ${a.formule.label} — ${a.formule.prix}</p>`;
  }
  preview.innerHTML = html || '<p style="color:var(--text-secondary);">Remplissez le plat du jour pour voir l\'aperçu.</p>';
}

// ========== MODAL (remplace prompt/confirm) ==========

function showModal({ title, message = '', fields = [], confirmText = 'Confirmer', danger = false }) {
  return new Promise(resolve => {
    const overlay = document.getElementById('modal-overlay');
    const titleEl = document.getElementById('modal-title');
    const messageEl = document.getElementById('modal-message');
    const fieldsEl = document.getElementById('modal-fields');
    const confirmBtn = document.getElementById('modal-confirm');
    const cancelBtn = document.getElementById('modal-cancel');

    titleEl.textContent = title;

    if (message) {
      messageEl.textContent = message;
      messageEl.style.display = 'block';
    } else {
      messageEl.style.display = 'none';
    }

    fieldsEl.innerHTML = '';
    fields.forEach(f => {
      const div = document.createElement('div');
      div.className = 'modal-field';
      div.innerHTML = `<label>${f.label}</label><input type="text" id="modal-input-${f.key}" placeholder="${f.placeholder || ''}" value="${f.value || ''}" />`;
      fieldsEl.appendChild(div);
    });

    confirmBtn.textContent = confirmText;
    confirmBtn.style.backgroundColor = danger ? 'var(--danger)' : '';

    overlay.style.display = 'flex';

    const firstInput = fieldsEl.querySelector('input');
    if (firstInput) setTimeout(() => firstInput.focus(), 50);

    function cleanup(result) {
      overlay.style.display = 'none';
      confirmBtn.removeEventListener('click', onConfirm);
      cancelBtn.removeEventListener('click', onCancel);
      overlay.removeEventListener('click', onBackdrop);
      document.removeEventListener('keydown', onKey);
      resolve(result);
    }

    function onConfirm() {
      if (fields.length > 0) {
        const values = {};
        let valid = true;
        fields.forEach(f => {
          const val = document.getElementById('modal-input-' + f.key).value.trim();
          if (f.required && !val) { valid = false; }
          values[f.key] = val;
        });
        if (!valid) return;
        cleanup(values);
      } else {
        cleanup(true);
      }
    }

    function onCancel() { cleanup(null); }
    function onBackdrop(e) { if (e.target === overlay) cleanup(null); }
    function onKey(e) {
      if (e.key === 'Escape') cleanup(null);
      if (e.key === 'Enter' && fields.length > 0) onConfirm();
    }

    confirmBtn.addEventListener('click', onConfirm);
    cancelBtn.addEventListener('click', onCancel);
    overlay.addEventListener('click', onBackdrop);
    document.addEventListener('keydown', onKey);
  });
}

// ========== GESTION CARTE MENUS ==========

let currentMenu = null;

function loadMenuCard() {
  return safeParse(localStorage.getItem('menuCard'), { categories: [] });
}

function renderMenuCard() {
  currentMenu = loadMenuCard();
  const container = document.getElementById('menuCategoriesContainer');
  container.innerHTML = '';

  if (!currentMenu.categories || currentMenu.categories.length === 0) {
    container.innerHTML = '<p style="color:var(--text-secondary); text-align:center; padding:2rem;">Aucune catégorie. Cliquez sur "+ Catégorie" pour commencer.</p>';
    return;
  }

  currentMenu.categories.forEach(cat => {
    const catDiv = document.createElement('div');
    catDiv.style.cssText = 'margin-bottom:2rem; border-radius:8px; border:1px solid var(--border-soft); overflow:hidden;';

    const header = document.createElement('div');
    header.style.cssText = 'background-color:var(--card-bg); padding:1rem; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-soft);';
    header.innerHTML = `
      <h4 style="margin:0; font-size:1.1rem; color:var(--text-main);">${cat.nom}</h4>
      <div style="display:flex; gap:0.5rem;">
        <button type="button" class="btn-secondary" style="width:auto; padding:0.5rem 1rem; font-size:0.85rem;" onclick="editCategory(${JSON.stringify(cat).replace(/"/g,'&quot;')})">✎ Modifier</button>
        <button type="button" class="btn-danger" style="width:auto; padding:0.5rem 1rem; font-size:0.85rem;" onclick="deleteCategory('${cat.id}')">× Supprimer</button>
      </div>
    `;

    const content = document.createElement('div');
    content.style.padding = '1rem';

    if (cat.plats && cat.plats.length > 0) {
      cat.plats.forEach((plat, idx) => {
        const platDiv = document.createElement('div');
        const isLast = idx === cat.plats.length - 1;
        platDiv.style.cssText = `display:flex; justify-content:space-between; align-items:start; padding-bottom:${isLast?'0':'1rem'}; margin-bottom:${isLast?'0':'1rem'}; border-bottom:${isLast?'none':'1px solid var(--border-soft)'};`;
        platDiv.innerHTML = `
          <div>
            <p style="margin:0 0 0.25rem 0; font-size:0.95rem; font-weight:600; color:var(--text-main);">${plat.nom}</p>
            <p style="margin:0; font-size:0.85rem; color:var(--accent); font-weight:700;">${plat.prix}</p>
            ${plat.description ? `<p style="margin:0.25rem 0 0 0; font-size:0.85rem; color:var(--text-secondary);">${plat.description}</p>` : ''}
          </div>
          <div style="display:flex; gap:0.5rem; flex-shrink:0; margin-left:1rem;">
            <button type="button" class="btn-secondary" style="width:auto; padding:0.4rem 0.8rem; font-size:0.8rem;" onclick="editPlat('${cat.id}', '${plat.id}')">✎</button>
            <button type="button" class="btn-danger" style="width:auto; padding:0.4rem 0.8rem; font-size:0.8rem;" onclick="deletePlat('${cat.id}', '${plat.id}')">×</button>
          </div>
        `;
        content.appendChild(platDiv);
      });
    }

    const addBtn = document.createElement('button');
    addBtn.type = 'button';
    addBtn.className = 'btn-secondary';
    addBtn.style.cssText = 'width:100%; padding:0.75rem; margin-top:0.5rem;';
    addBtn.textContent = '+ Ajouter un plat';
    addBtn.onclick = () => addPlatToCategory(cat.id);
    content.appendChild(addBtn);

    catDiv.appendChild(header);
    catDiv.appendChild(content);
    container.appendChild(catDiv);
  });
}

async function editCategory(cat) {
  const result = await showModal({
    title: 'Modifier la catégorie',
    fields: [{ key: 'nom', label: 'Nom de la catégorie', value: cat.nom, required: true }],
    confirmText: 'Enregistrer'
  });
  if (result) { cat.nom = result.nom; renderMenuCard(); }
}

async function deleteCategory(catId) {
  const result = await showModal({
    title: 'Supprimer la catégorie ?',
    message: 'Cette action supprimera la catégorie et tous ses plats.',
    confirmText: 'Supprimer',
    danger: true
  });
  if (!result) return;
  currentMenu.categories = currentMenu.categories.filter(c => c.id !== catId);
  renderMenuCard();
}

async function addPlatToCategory(catId) {
  const cat = currentMenu.categories.find(c => c.id === catId);
  if (!cat) return;
  const result = await showModal({
    title: 'Ajouter un plat',
    fields: [
      { key: 'nom', label: 'Nom du plat', placeholder: 'Ex : Côte de veau normande', required: true },
      { key: 'prix', label: 'Prix', placeholder: 'Ex : 22,00 €', required: true }
    ],
    confirmText: 'Ajouter'
  });
  if (!result) return;
  cat.plats.push({ id: 'plat-' + Date.now(), nom: result.nom, prix: result.prix, description: '', disponible: true });
  renderMenuCard();
}

async function editPlat(catId, platId) {
  const cat = currentMenu.categories.find(c => c.id === catId);
  if (!cat) return;
  const plat = cat.plats.find(p => p.id === platId);
  if (!plat) return;
  const result = await showModal({
    title: 'Modifier le plat',
    fields: [
      { key: 'nom', label: 'Nom du plat', value: plat.nom, required: true },
      { key: 'prix', label: 'Prix', value: plat.prix, required: true }
    ],
    confirmText: 'Enregistrer'
  });
  if (!result) return;
  plat.nom = result.nom;
  plat.prix = result.prix;
  renderMenuCard();
}

function deletePlat(catId, platId) {
  const cat = currentMenu.categories.find(c => c.id === catId);
  if (cat) { cat.plats = cat.plats.filter(p => p.id !== platId); renderMenuCard(); }
}

document.getElementById('addCategoryBtn').addEventListener('click', async () => {
  const result = await showModal({
    title: 'Nouvelle catégorie',
    fields: [{ key: 'nom', label: 'Nom de la catégorie', placeholder: 'Ex : Entrées, Plats, Desserts…', required: true }],
    confirmText: 'Créer'
  });
  if (!result) return;
  if (!currentMenu) currentMenu = { categories: [] };
  currentMenu.categories.push({ id: 'cat-' + Date.now(), nom: result.nom, ordre: currentMenu.categories.length + 1, plats: [] });
  renderMenuCard();
});

document.getElementById('menuSaveBtn').addEventListener('click', () => {
  localStorage.setItem('menuCard', JSON.stringify(currentMenu));
  const msg = document.getElementById('menuConfirmation');
  msg.classList.add('show');
  setTimeout(() => msg.classList.remove('show'), 4000);
});

// ========== INITIALISATION DASHBOARD ==========

function initDashboard() {
  loadDemoData();
  document.getElementById('todayDate').textContent = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  });

  const contenu = safeParse(localStorage.getItem('contenu_editable'), {});
  if (contenu.ardoise) setArdoiseToForm(contenu.ardoise);
  updateArdoisePreview();

  updateKPIs();
  renderPendingReservations();
  renderReservationsCalendar();
  renderReservationsList();
  renderMenuCard();
}

document.addEventListener('DOMContentLoaded', () => {});
