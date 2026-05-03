// ===== CONSTANTES =====

const MOT_DE_PASSE_ADMIN = 'admin';

const HEURES_DEJEUNER = ['12h00', '12h30', '13h00', '13h30'];
const HEURES_DINER = ['19h00', '19h30', '20h00', '20h30', '21h00'];

// ===== UTILITY FUNCTIONS =====

function safeParse(key, fallback) {
  if (!key) return fallback;
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch (e) {
    return fallback;
  }
}

function offsetDate(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

function formatDate(isoString) {
  const date = new Date(isoString + 'T00:00:00');
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  return date.toLocaleDateString('fr-FR', options);
}

function formatDateShort(isoString) {
  const date = new Date(isoString + 'T00:00:00');
  const options = { day: 'numeric', month: 'numeric', year: '2-digit' };
  return date.toLocaleDateString('fr-FR', options);
}

function showNotification(elementId, duration = 4000) {
  const notification = document.getElementById(elementId);
  if (!notification) return;
  notification.classList.remove('hidden');
  setTimeout(() => {
    notification.classList.add('hidden');
  }, duration);
}

// ===== DONNÉES PAR DÉFAUT =====

const DEMO_RESERVATIONS_DEFAULT = [
  {
    id: 'demo-1',
    nom: 'Claire Dubois',
    email: 'claire.dubois@exemple.com',
    tel: '06 23 45 67 89',
    date: 'offsetDate(1)',
    heure: '12h30',
    personnes: 2,
    message: 'Table en terrasse si possible',
    statut: 'En attente',
    source: 'demo',
    createdAt: new Date(Date.now() - 2 * 3600000).toISOString()
  },
  {
    id: 'demo-2',
    nom: 'Philippe Martin',
    email: 'p.martin@exemple.com',
    tel: '07 82 34 56 78',
    date: 'offsetDate(1)',
    heure: '20h00',
    personnes: 4,
    message: 'Anniversaire de mariage, merci !',
    statut: 'Confirmée',
    source: 'demo',
    createdAt: new Date(Date.now() - 5 * 3600000).toISOString()
  },
  {
    id: 'demo-3',
    nom: 'Nathalie Rousseau',
    email: 'nathalie.r@exemple.com',
    tel: '06 91 23 45 67',
    date: 'offsetDate(2)',
    heure: '19h30',
    personnes: 3,
    message: 'Une personne allergique aux fruits à coque',
    statut: 'En attente',
    source: 'demo',
    createdAt: new Date(Date.now() - 8 * 3600000).toISOString()
  },
  {
    id: 'demo-4',
    nom: 'Jean-Luc Bernard',
    email: 'jl.bernard@exemple.com',
    tel: '06 45 78 91 23',
    date: 'offsetDate(3)',
    heure: '13h00',
    personnes: 5,
    message: 'Repas de famille, chaise haute nécessaire',
    statut: 'En attente',
    source: 'demo',
    createdAt: new Date(Date.now() - 12 * 3600000).toISOString()
  },
  {
    id: 'demo-5',
    nom: 'Sandrine Moreau',
    email: 'sandrine.moreau@exemple.com',
    tel: '07 34 56 78 90',
    date: 'offsetDate(4)',
    heure: '20h30',
    personnes: 6,
    message: 'Réservation annulée suite changement de plans',
    statut: 'Annulée',
    source: 'demo',
    createdAt: new Date(Date.now() - 20 * 3600000).toISOString()
  }
];

const DEMO_ARDOISE_DEFAULT = {
  disponible: true,
  plat: 'Bœuf bourguignon mijoté',
  plat_prix: '16,50 €',
  plat_note: 'Viande fondante accompagnée de pommes de terre grenaille',
  entree: 'Terrine maison et cornichons',
  entree_prix: '9,00 €',
  dessert: 'Tarte tatin aux pommes',
  dessert_prix: '7,50 €'
};

// ===== INITIALISATION DONNÉES =====

function ensureInitialData() {
  if (!localStorage.getItem('DEMO_INITIALIZED')) {
    const reservationsWithDates = DEMO_RESERVATIONS_DEFAULT.map(r => ({
      ...r,
      date: r.date.startsWith('offsetDate') 
        ? offsetDate(parseInt(r.date.match(/\d+/)[0])) 
        : r.date
    }));

    localStorage.setItem('DEMO_RESERVATIONS', JSON.stringify(reservationsWithDates));
    localStorage.setItem('DEMO_ARDOISE', JSON.stringify(DEMO_ARDOISE_DEFAULT));
    localStorage.setItem('DEMO_ARDOISE_DISPONIBLE', 'true');
    localStorage.setItem('DEMO_INITIALIZED', 'true');
  }
}

// ===== LOGIN =====

function verifierMotDePasse(saisie) {
  return saisie === MOT_DE_PASSE_ADMIN;
}

function handleLogin() {
  const passwordInput = document.getElementById('passwordInput');
  const loginError = document.getElementById('loginError');

  if (!passwordInput) return;

  const password = passwordInput.value;

  if (!password) {
    if (loginError) {
      loginError.textContent = 'Veuillez entrer votre mot de passe';
      loginError.classList.remove('hidden');
    }
    return;
  }

  if (!verifierMotDePasse(password)) {
    if (loginError) {
      loginError.textContent = 'Mot de passe incorrect';
      loginError.classList.remove('hidden');
    }
    return;
  }

  // Login réussi
  if (loginError) {
    loginError.classList.add('hidden');
  }

  sessionStorage.setItem('admin_session', '1');
  showDashboard();
  initDashboard();
}

function togglePasswordVisibility() {
  const passwordInput = document.getElementById('passwordInput');
  const toggleButton = document.getElementById('togglePassword');

  if (!passwordInput || !toggleButton) return;

  const isPassword = passwordInput.type === 'password';
  passwordInput.type = isPassword ? 'text' : 'password';
  toggleButton.textContent = isPassword ? '🙈' : '👁️';
}

// ===== AFFICHAGE/MASQUAGE ÉCRANS =====

function showDashboard() {
  const loginScreen = document.getElementById('loginScreen');
  const dashboard = document.getElementById('dashboard');

  if (loginScreen) loginScreen.classList.add('hidden');
  if (dashboard) dashboard.classList.remove('hidden');
}

function showLoginScreen() {
  const loginScreen = document.getElementById('loginScreen');
  const dashboard = document.getElementById('dashboard');

  if (loginScreen) loginScreen.classList.remove('hidden');
  if (dashboard) dashboard.classList.add('hidden');

  const passwordInput = document.getElementById('passwordInput');
  if (passwordInput) passwordInput.value = '';

  const loginError = document.getElementById('loginError');
  if (loginError) loginError.classList.add('hidden');
}

function handleLogout() {
  sessionStorage.removeItem('admin_session');
  showLoginScreen();
}

// ===== KPI CALCULATION =====

function calculateKPIs() {
  const reservations = safeParse('DEMO_RESERVATIONS', []);
  const today = new Date().toISOString().split('T')[0];

  const lunchCovers = reservations
    .filter(r => r.date === today && HEURES_DEJEUNER.includes(r.heure) && r.statut !== 'Annulée')
    .reduce((sum, r) => sum + (parseInt(r.personnes) || 0), 0);

  const dinnerCovers = reservations
    .filter(r => r.date === today && HEURES_DINER.includes(r.heure) && r.statut !== 'Annulée')
    .reduce((sum, r) => sum + (parseInt(r.personnes) || 0), 0);

  const pendingCount = reservations.filter(r => r.statut === 'En attente').length;

  const kpiLunch = document.getElementById('kpiLunch');
  const kpiDiner = document.getElementById('kpiDiner');
  const kpiPending = document.getElementById('kpiPending');

  if (kpiLunch) kpiLunch.textContent = lunchCovers;
  if (kpiDiner) kpiDiner.textContent = dinnerCovers;
  if (kpiPending) kpiPending.textContent = pendingCount;
}

// ===== AFFICHAGE DATE DU JOUR =====

function displayTodayDate() {
  const todayDate = document.getElementById('todayDate');
  if (todayDate) {
    const today = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const dateStr = today.toLocaleDateString('fr-FR', options);
    todayDate.textContent = `Aujourd'hui, ${dateStr.charAt(0).toUpperCase() + dateStr.slice(1)}`;
  }
}

// ===== RENDUS RÉSERVATIONS =====

function renderPriorityReservations() {
  const reservationsList = document.getElementById('reservationsList');
  if (!reservationsList) return;

  const reservations = safeParse('DEMO_RESERVATIONS', []);
  const today = new Date().toISOString().split('T')[0];
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];

  // Filtrer : en attente des 2 derniers jours
  const priorityReservations = reservations.filter(
    r => r.statut === 'En attente' && 
    (r.date === today || r.date === yesterday)
  );

  if (priorityReservations.length === 0) {
    reservationsList.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: var(--spacing-lg);">Aucune réservation en attente</p>';
    return;
  }

  reservationsList.innerHTML = priorityReservations.map(r => renderReservationCard(r)).join('');
  attachReservationCardHandlers();
}

function renderAllReservations() {
  const allReservationsList = document.getElementById('allReservationsList');
  if (!allReservationsList) return;

  const reservations = safeParse('DEMO_RESERVATIONS', []);

  // Trier : les plus récentes en premier
  const sortedReservations = [...reservations].sort((a, b) => {
    const dateA = new Date(b.date);
    const dateB = new Date(a.date);
    return dateB - dateA;
  });

  if (sortedReservations.length === 0) {
    allReservationsList.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: var(--spacing-lg);">Aucune réservation</p>';
    return;
  }

  allReservationsList.innerHTML = sortedReservations.map(r => renderReservationCard(r)).join('');
  attachReservationCardHandlers();
}

function renderReservationCard(reservation) {
  const statusClass = reservation.statut === 'En attente' 
    ? 'badge-pending'
    : reservation.statut === 'Confirmée'
    ? 'badge-confirmed'
    : 'badge-cancelled';

  const messageHtml = reservation.message 
    ? `<p style="margin-top: var(--spacing-md); font-size: 0.9rem; color: var(--text-secondary); font-style: italic;">💬 ${reservation.message}</p>`
    : '';

  const buttons = reservation.statut === 'En attente'
    ? `
      <div style="display: flex; gap: var(--spacing-md); margin-top: var(--spacing-lg);">
        <button type="button" class="btn-confirm" data-id="${reservation.id}" style="flex: 1; padding: var(--spacing-md) var(--spacing-lg); background-color: var(--success); color: white; border: none; border-radius: var(--radius-md); cursor: pointer; font-weight: 600; font-size: 0.9rem;">✓ Confirmer</button>
        <button type="button" class="btn-cancel" data-id="${reservation.id}" style="flex: 1; padding: var(--spacing-md) var(--spacing-lg); background-color: var(--danger); color: white; border: none; border-radius: var(--radius-md); cursor: pointer; font-weight: 600; font-size: 0.9rem;">✗ Annuler</button>
      </div>
    `
    : '';

  return `
    <div class="reservation-card" style="padding: var(--spacing-lg); background-color: var(--card-bg); border-radius: var(--radius-md); border-left: 4px solid var(--accent); margin-bottom: var(--spacing-md);">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--spacing-md);">
        <div>
          <h4 style="margin: 0 0 var(--spacing-sm) 0; color: var(--text-main);">${reservation.nom}</h4>
          <p style="margin: 0; color: var(--text-secondary); font-size: 0.9rem;">${formatDateShort(reservation.date)} à ${reservation.heure}</p>
        </div>
        <span class="badge ${statusClass}" style="padding: var(--spacing-xs) var(--spacing-md); border-radius: var(--radius-md); font-size: 0.85rem; font-weight: 600; white-space: nowrap;">
          ${reservation.statut}
        </span>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-md); margin-bottom: var(--spacing-md); font-size: 0.9rem;">
        <div>
          <span style="color: var(--text-secondary);">Couverts</span>
          <p style="margin: var(--spacing-xs) 0 0 0; color: var(--text-main); font-weight: 600;">${reservation.personnes} ${reservation.personnes === 1 ? 'couvert' : 'couverts'}</p>
        </div>
        <div>
          <span style="color: var(--text-secondary);">Téléphone</span>
          <p style="margin: var(--spacing-xs) 0 0 0; color: var(--accent);"><a href="tel:${reservation.tel.replace(/\s/g, '')}" style="color: var(--accent); text-decoration: none; font-weight: 600;">${reservation.tel}</a></p>
        </div>
      </div>

      ${messageHtml}

      ${buttons}
    </div>
  `;
}

function attachReservationCardHandlers() {
  const confirmButtons = document.querySelectorAll('.btn-confirm');
  const cancelButtons = document.querySelectorAll('.btn-cancel');

  confirmButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const reservationId = btn.getAttribute('data-id');
      updateReservationStatus(reservationId, 'Confirmée');
    });
  });

  cancelButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const reservationId = btn.getAttribute('data-id');
      updateReservationStatus(reservationId, 'Annulée');
    });
  });
}

function updateReservationStatus(reservationId, newStatus) {
  const reservations = safeParse('DEMO_RESERVATIONS', []);
  
  const reservation = reservations.find(r => r.id === reservationId);
  if (!reservation) return;

  reservation.statut = newStatus;

  localStorage.setItem('DEMO_RESERVATIONS', JSON.stringify(reservations));

  calculateKPIs();
  renderPriorityReservations();
  renderAllReservations();

  // Afficher notification de succès
  const statusLabel = newStatus === 'Confirmée' ? 'confirmée' : 'annulée';
  showTransientNotification(`Réservation ${statusLabel} avec succès`);
}

function showTransientNotification(message) {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    bottom: var(--spacing-xl);
    right: var(--spacing-xl);
    background-color: var(--success);
    color: white;
    padding: var(--spacing-lg) var(--spacing-xl);
    border-radius: var(--radius-md);
    font-weight: 600;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  `;
  notification.textContent = `✓ ${message}`;
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// ===== FILTRES RÉSERVATIONS =====

function initReservationFilters() {
  const filterButtons = document.querySelectorAll('.filter-btn');

  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      // Désactiver tous les boutons
      filterButtons.forEach(b => b.classList.remove('active'));
      // Activer le bouton cliqué
      btn.classList.add('active');

      const filter = btn.getAttribute('data-filter');
      applyReservationFilter(filter);
    });
  });
}

function applyReservationFilter(filter) {
  const reservations = safeParse('DEMO_RESERVATIONS', []);
  const allReservationsList = document.getElementById('allReservationsList');

  let filtered = [...reservations];

  if (filter === 'pending') {
    filtered = filtered.filter(r => r.statut === 'En attente');
  } else if (filter === 'confirmed') {
    filtered = filtered.filter(r => r.statut === 'Confirmée');
  } else if (filter === 'cancelled') {
    filtered = filtered.filter(r => r.statut === 'Annulée');
  }

  // Trier par date
  filtered.sort((a, b) => new Date(b.date) - new Date(a.date));

  if (allReservationsList) {
    if (filtered.length === 0) {
      allReservationsList.innerHTML = `<p style="color: var(--text-secondary); text-align: center; padding: var(--spacing-lg);">Aucune réservation ${filter !== 'all' ? 'dans cette catégorie' : ''}</p>`;
    } else {
      allReservationsList.innerHTML = filtered.map(r => renderReservationCard(r)).join('');
      attachReservationCardHandlers();
    }
  }
}

// ===== ONGLETS ADMIN =====

function initAdminTabs() {
  const tabButtons = document.querySelectorAll('.admin-tabs .tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      const targetTab = button.getAttribute('data-tab');

      // Désactiver tous les onglets
      tabButtons.forEach(btn => btn.classList.remove('active'));
      tabContents.forEach(content => content.classList.remove('active'));

      // Activer l'onglet cliqué
      button.classList.add('active');
      const targetContent = document.getElementById(targetTab);
      if (targetContent) {
        targetContent.classList.add('active');
      }
    });
  });
}

// ===== ARDOISE =====

function loadArdoiseForm() {
  const ardoise = safeParse('DEMO_ARDOISE', {});
  const disponible = localStorage.getItem('DEMO_ARDOISE_DISPONIBLE') === 'true';

  document.getElementById('ardoise-toggle').checked = disponible;
  document.getElementById('admin-plat').value = ardoise.plat || '';
  document.getElementById('admin-plat-prix').value = ardoise.plat_prix || '';
  document.getElementById('admin-plat-note').value = ardoise.plat_note || '';
  document.getElementById('admin-entree').value = ardoise.entree || '';
  document.getElementById('admin-entree-prix').value = ardoise.entree_prix || '';
  document.getElementById('admin-dessert').value = ardoise.dessert || '';
  document.getElementById('admin-dessert-prix').value = ardoise.dessert_prix || '';

  updateArdoiseToggleVisual();
}

function updateArdoiseToggleVisual() {
  const toggle = document.getElementById('ardoise-toggle');
  const toggleVisual = document.getElementById('ardoise-toggle-visual');

  if (!toggle || !toggleVisual) return;

  if (toggle.checked) {
    toggleVisual.style.backgroundColor = 'var(--success)';
  } else {
    toggleVisual.style.backgroundColor = 'var(--border-soft)';
  }
}

function handleArdoiseToggle() {
  const toggle = document.getElementById('ardoise-toggle');
  if (toggle) {
    toggle.addEventListener('change', updateArdoiseToggleVisual);
  }
}

function saveArdoise() {
  const ardoise = {
    disponible: document.getElementById('ardoise-toggle').checked,
    plat: document.getElementById('admin-plat').value,
    plat_prix: document.getElementById('admin-plat-prix').value,
    plat_note: document.getElementById('admin-plat-note').value,
    entree: document.getElementById('admin-entree').value,
    entree_prix: document.getElementById('admin-entree-prix').value,
    dessert: document.getElementById('admin-dessert').value,
    dessert_prix: document.getElementById('admin-dessert-prix').value
  };

  localStorage.setItem('DEMO_ARDOISE', JSON.stringify(ardoise));
  localStorage.setItem('DEMO_ARDOISE_DISPONIBLE', ardoise.disponible ? 'true' : 'false');

  showNotification('ardoiseNotification', 4000);
}

function initArdoiseHandlers() {
  const saveButton = document.getElementById('saveArdoiseBtn');
  if (saveButton) {
    saveButton.addEventListener('click', saveArdoise);
  }

  handleArdoiseToggle();
  loadArdoiseForm();
}

// ===== INITIALISATION DASHBOARD =====

function initDashboard() {
  ensureInitialData();

  displayTodayDate();
  calculateKPIs();
  renderPriorityReservations();
  renderAllReservations();

  initAdminTabs();
  initReservationFilters();
  initArdoiseHandlers();
}

// ===== EVENT LISTENERS =====

function attachEventListeners() {
  // Login
  const loginBtn = document.getElementById('loginBtn');
  if (loginBtn) {
    loginBtn.addEventListener('click', handleLogin);
  }

  const passwordInput = document.getElementById('passwordInput');
  if (passwordInput) {
    passwordInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        handleLogin();
      }
    });
  }

  const togglePassword = document.getElementById('togglePassword');
  if (togglePassword) {
    togglePassword.addEventListener('click', togglePasswordVisibility);
  }

  // Logout
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }
}

// ===== DÉMARRAGE =====

document.addEventListener('DOMContentLoaded', () => {
  ensureInitialData();
  attachEventListeners();

  // Vérifier si session existe
  if (sessionStorage.getItem('admin_session') === '1') {
    showDashboard();
    initDashboard();
  } else {
    showLoginScreen();
  }
});

// ===== ÉCOUTE STORAGE (SYNC TEMPS RÉEL) =====

window.addEventListener('storage', (e) => {
  if (e.key === 'DEMO_RESERVATIONS' || e.key === 'DEMO_ARDOISE' || e.key === 'DEMO_ARDOISE_DISPONIBLE') {
    if (sessionStorage.getItem('admin_session') === '1') {
      calculateKPIs();
      renderPriorityReservations();
      renderAllReservations();
    }
  }
});