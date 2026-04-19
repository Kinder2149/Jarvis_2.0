/* ========================================
   POINTE DE RÊVE — admin.js
   Stack Standard — Vanilla JavaScript ES6+
   ======================================== */

// ========== CONFIGURATION ==========
const CONFIG = {
  password: 'demo',
  appPrefix: 'DEMO_',
};

// ========== DEMO DATA ==========
function getOffsetDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

const DEMO_RESERVATIONS = [
  {
    id: 'demo-1',
    prenom: 'Marie D.',
    telephone: '06 12 34 56 78',
    date: getOffsetDate(1),
    service: 'diner',
    couverts: '2',
    message: 'Anniversaire de mariage, si possible une table en retrait',
    statut: 'En attente',
    source: 'demo',
  },
  {
    id: 'demo-2',
    prenom: 'Thomas B.',
    telephone: '07 65 43 21 09',
    date: getOffsetDate(1),
    service: 'dejeuner',
    couverts: '4',
    message: '',
    statut: 'Confirmée',
    source: 'demo',
  },
  {
    id: 'demo-3',
    prenom: 'Sophie M.',
    telephone: '06 98 76 54 32',
    date: getOffsetDate(2),
    service: 'diner',
    couverts: '6',
    message: 'Une personne allergique aux crustacés',
    statut: 'En attente',
    source: 'demo',
  },
  {
    id: 'demo-4',
    prenom: 'Laurent F.',
    telephone: '07 11 22 33 44',
    date: getOffsetDate(3),
    service: 'dejeuner',
    couverts: '2',
    message: 'Menu dégustation si disponible',
    statut: 'Confirmée',
    source: 'demo',
  },
  {
    id: 'demo-5',
    prenom: 'Isabelle R.',
    telephone: '06 55 44 33 22',
    date: getOffsetDate(4),
    service: 'diner',
    couverts: '8',
    message: 'Repas d\'entreprise',
    statut: 'Annulée',
    source: 'demo',
  },
];

const DEMO_ARDOISE = {
  disponible: true,
  entree: {
    nom: 'Velouté de butternut, crème fraîche',
    prix: '8,00 €',
  },
  plat: {
    nom: 'Magret de canard, jus de cerise',
    prix: '21,00 €',
    note: 'Cuisson selon votre goût',
  },
  dessert: {
    nom: 'Fondant au chocolat, glace vanille',
    prix: '7,00 €',
  },
  formule: {
    active: true,
    prix: '31,00 €',
    label: 'Entrée + Plat + Dessert',
  },
};

const DEMO_MENU = {
  categories: [
    {
      id: 'cat-1',
      nom: 'Entrées',
      ordre: 1,
      plats: [
        {
          id: 'plat-1',
          nom: 'Terrine de foie gras maison',
          prix: '14,00 €',
          description: 'Chutney de figues, brioche toastée',
          disponible: true,
        },
        {
          id: 'plat-2',
          nom: 'Carpaccio de saint-jacques',
          prix: '12,00 €',
          description: 'Citron frais, parmesan râpé',
          disponible: true,
        },
        {
          id: 'plat-3',
          nom: 'Salade de chèvre chaud',
          prix: '9,00 €',
          description: 'Mélange de feuilles fraîches, noix',
          disponible: true,
        },
      ],
    },
    {
      id: 'cat-2',
      nom: 'Plats',
      ordre: 2,
      plats: [
        {
          id: 'plat-4',
          nom: 'Filet de bœuf sauce béarnaise',
          prix: '24,00 €',
          description: 'Servi avec légumes de saison',
          disponible: true,
        },
        {
          id: 'plat-5',
          nom: 'Brochette de homard et scampi',
          prix: '26,00 €',
          description: 'Moutarde légère',
          disponible: true,
        },
        {
          id: 'plat-6',
          nom: 'Volaille fermière rôtie',
          prix: '18,00 €',
          description: 'Aux herbes de Provence',
          disponible: true,
        },
        {
          id: 'plat-7',
          nom: 'Pâtes fraîches aux truffes',
          prix: '16,00 €',
          description: 'Parmesan frais',
          disponible: true,
        },
      ],
    },
    {
      id: 'cat-3',
      nom: 'Desserts',
      ordre: 3,
      plats: [
        {
          id: 'plat-8',
          nom: 'Fondant au chocolat',
          prix: '8,00 €',
          description: 'Glace à la vanille',
          disponible: true,
        },
        {
          id: 'plat-9',
          nom: 'Tarte tatin maison',
          prix: '7,00 €',
          description: 'Crème fraîche',
          disponible: true,
        },
        {
          id: 'plat-10',
          nom: 'Assortiment de fromages',
          prix: '9,00 €',
          description: 'Sélection du marché',
          disponible: true,
        },
      ],
    },
  ],
};

// ========== UTILITIES ==========
function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try {
    return JSON.parse(rawValue);
  } catch (e) {
    return fallbackValue;
  }
}

function getStorageKey(key) {
  return CONFIG.appPrefix + key;
}

function getFromStorage(key, fallback = null) {
  const value = localStorage.getItem(getStorageKey(key));
  if (value === null) return fallback;
  return safeParse(value, fallback);
}

function setToStorage(key, value) {
  localStorage.setItem(getStorageKey(key), JSON.stringify(value));
}

function formatDateFR(dateString) {
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  return new Date(dateString).toLocaleDateString('fr-FR', options);
}

function formatServiceLabel(service) {
  return service === 'dejeuner' ? 'Déjeuner' : 'Dîner';
}

function showNotification(message, type = 'info') {
  const notification = document.getElementById('notification');
  notification.textContent = message;
  notification.className = `notification show ${type}`;
  setTimeout(() => {
    notification.classList.remove('show');
  }, 4000);
}

// ========== INITIALIZATION ==========
function ensureInitialData() {
  const existing = getFromStorage('RESERVATIONS');
  if (!existing) {
    setToStorage('RESERVATIONS', DEMO_RESERVATIONS);
  }

  const existingArdoise = getFromStorage('ARDOISE');
  if (!existingArdoise) {
    setToStorage('ARDOISE', DEMO_ARDOISE);
  }

  const existingMenu = getFromStorage('MENU');
  if (!existingMenu) {
    setToStorage('MENU', DEMO_MENU);
  }
}

// ========== LOGIN LOGIC ==========
function initLoginForm() {
  const loginForm = document.getElementById('loginForm');
  const loginScreen = document.getElementById('loginScreen');
  const passwordInput = document.getElementById('login-password');
  const togglePasswordBtn = document.getElementById('togglePassword');
  const loginError = document.getElementById('loginError');

  togglePasswordBtn.addEventListener('click', () => {
    const type = passwordInput.type === 'password' ? 'text' : 'password';
    passwordInput.type = type;
    togglePasswordBtn.textContent = type === 'password' ? '👁️' : '🙈';
  });

  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const password = passwordInput.value.trim();

    if (password === CONFIG.password) {
      loginError.classList.remove('show');
      loginScreen.classList.add('hidden');
      document.getElementById('dashboard').classList.add('visible');
      sessionStorage.setItem('admin_logged_in', 'true');
      passwordInput.value = '';
      initDashboard();
    } else {
      loginError.textContent = 'Mot de passe incorrect';
      loginError.classList.add('show');
      passwordInput.focus();
    }
  });
}

// ========== LOGOUT ==========
function initLogout() {
  const logoutBtn = document.getElementById('logoutBtn');
  logoutBtn.addEventListener('click', () => {
    sessionStorage.removeItem('admin_logged_in');
    document.getElementById('dashboard').classList.remove('visible');
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('loginForm').reset();
    document.getElementById('login-password').type = 'password';
    document.getElementById('togglePassword').textContent = '👁️';
  });
}

// ========== KPI CALCULATIONS ==========
function calculateKPIs() {
  const reservations = getFromStorage('RESERVATIONS', []);
  const today = new Date().toISOString().split('T')[0];
  const weekStart = new Date();
  const weekEnd = new Date();
  weekEnd.setDate(weekEnd.getDate() + 7);
  const weekEndStr = weekEnd.toISOString().split('T')[0];

  const todayReservations = reservations.filter((r) => r.date === today);
  const pendingReservations = reservations.filter((r) => r.statut === 'En attente');
  const confirmedThisWeek = reservations.filter(
    (r) => r.statut === 'Confirmée' && r.date >= today && r.date <= weekEndStr
  );

  document.getElementById('kpiToday').textContent = todayReservations.length;
  document.getElementById('kpiPending').textContent = pendingReservations.length;
  document.getElementById('kpiConfirmed').textContent = confirmedThisWeek.length;
}

// ========== TODAY SECTION ==========
function renderTodayReservations() {
  const reservations = getFromStorage('RESERVATIONS', []);
  const today = new Date().toISOString().split('T')[0];
  const todayReservations = reservations
    .filter((r) => r.date === today)
    .sort((a, b) => {
      const statusOrder = { 'En attente': 0, Confirmée: 1, Annulée: 2 };
      return statusOrder[a.statut] - statusOrder[b.statut];
    });

  const container = document.getElementById('todayReservations');
  const dateDisplay = document.getElementById('todayDate');

  if (todayReservations.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>Aucune réservation pour aujourd\'hui</p></div>';
    dateDisplay.textContent = formatDateFR(today);
    return;
  }

  dateDisplay.textContent = formatDateFR(today);
  container.innerHTML = todayReservations.map((r) => renderReservationCard(r)).join('');

  // Attach event listeners
  todayReservations.forEach((r) => {
    const confirmBtn = container.querySelector(`[data-action="confirm"][data-id="${r.id}"]`);
    const cancelBtn = container.querySelector(`[data-action="cancel"][data-id="${r.id}"]`);

    if (confirmBtn) {
      confirmBtn.addEventListener('click', () => handleConfirmReservation(r.id));
    }
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => handleCancelReservation(r.id));
    }
  });
}

function renderReservationCard(reservation) {
  const isConfirmed = reservation.statut === 'Confirmée';
  const isCancelled = reservation.statut === 'Annulée';
  const confirmBtnDisabled = isConfirmed ? 'disabled' : '';
  const cancelBtnDisabled = isCancelled ? 'disabled' : '';

  return `
    <div class="reservation-card ${reservation.statut.toLowerCase().replace(' ', '-')}">
      <div class="reservation-header">
        <div class="reservation-info">
          <div class="reservation-name">${reservation.prenom}</div>
          <div class="reservation-service">${formatServiceLabel(reservation.service)} · ${reservation.date}</div>
          <div class="reservation-phone">📞 ${reservation.telephone}</div>
          <div class="reservation-couverts">${reservation.couverts} converts</div>
          ${
            reservation.statut === 'En attente'
              ? `<span class="badge badge-warning">${reservation.statut}</span>`
              : reservation.statut === 'Confirmée'
                ? `<span class="badge badge-success">${reservation.statut}</span>`
                : `<span class="badge badge-danger">${reservation.statut}</span>`
          }
        </div>
      </div>
      ${reservation.message ? `<div class="reservation-message">${reservation.message}</div>` : ''}
      <div class="reservation-actions">
        <button 
          class="btn-action btn-confirm" 
          data-action="confirm" 
          data-id="${reservation.id}"
          ${confirmBtnDisabled}
        >✓ Confirmer</button>
        <button 
          class="btn-action btn-cancel" 
          data-action="cancel" 
          data-id="${reservation.id}"
          ${cancelBtnDisabled}
        >✗ Annuler</button>
      </div>
    </div>
  `;
}

function handleConfirmReservation(id) {
  const reservations = getFromStorage('RESERVATIONS', []);
  const index = reservations.findIndex((r) => r.id === id);
  if (index !== -1) {
    reservations[index].statut = 'Confirmée';
    setToStorage('RESERVATIONS', reservations);
    calculateKPIs();
    renderTodayReservations();
    renderFullReservationsList();
    showNotification('Réservation confirmée ✓', 'success');
  }
}

function handleCancelReservation(id) {
  const reservations = getFromStorage('RESERVATIONS', []);
  const index = reservations.findIndex((r) => r.id === id);
  if (index !== -1) {
    reservations[index].statut = 'Annulée';
    setToStorage('RESERVATIONS', reservations);
    calculateKPIs();
    renderTodayReservations();
    renderFullReservationsList();
    showNotification('Réservation annulée', 'info');
  }
}

// ========== FULL RESERVATIONS LIST ==========
function renderFullReservationsList(filter = 'all') {
  const reservations = getFromStorage('RESERVATIONS', []);
  let filtered = reservations;

  if (filter === 'pending') filtered = reservations.filter((r) => r.statut === 'En attente');
  else if (filter === 'confirmed') filtered = reservations.filter((r) => r.statut === 'Confirmée');
  else if (filter === 'cancelled') filtered = reservations.filter((r) => r.statut === 'Annulée');

  filtered.sort((a, b) => new Date(b.date) - new Date(a.date));

  const container = document.getElementById('fullReservationsList');
  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>Aucune réservation pour cette sélection</p></div>';
    return;
  }

  container.innerHTML = filtered.map((r) => renderReservationCard(r)).join('');

  // Attach event listeners
  filtered.forEach((r) => {
    const confirmBtn = container.querySelector(`[data-action="confirm"][data-id="${r.id}"]`);
    const cancelBtn = container.querySelector(`[data-action="cancel"][data-id="${r.id}"]`);

    if (confirmBtn) {
      confirmBtn.addEventListener('click', () => handleConfirmReservation(r.id));
    }
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => handleCancelReservation(r.id));
    }
  });
}

// ========== TAB SWITCHING ==========
function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabContents = document.querySelectorAll('.tab-content');

  tabButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const tabName = button.getAttribute('data-tab');

      tabButtons.forEach((btn) => btn.classList.remove('active'));
      tabContents.forEach((content) => content.classList.remove('active'));

      button.classList.add('active');
      document.getElementById(`${tabName}Tab`).classList.add('active');
    });
  });
}

// ========== FILTER BUTTONS ==========
function initFilterButtons() {
  const filterButtons = document.querySelectorAll('.filter-btn');

  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      filterButtons.forEach((btn) => btn.classList.remove('active'));
      button.classList.add('active');
      const filter = button.getAttribute('data-filter');
      renderFullReservationsList(filter);
    });
  });
}

// ========== ARDOISE FORM ==========
function initArdoiseForm() {
  const form = document.getElementById('ardoiseForm');
  const ardoiseAvailable = document.getElementById('ardoiseAvailable');
  const ardoise = getFromStorage('ARDOISE', DEMO_ARDOISE);

  // Set initial state
  if (ardoise.disponible) {
    ardoiseAvailable.classList.add('active');
  }
  populateArdoiseForm(ardoise);
  updateArdoisePreview(ardoise);

  // Toggle availability
  ardoiseAvailable.addEventListener('click', () => {
    ardoiseAvailable.classList.toggle('active');
  });

  // Form submission
  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const updatedArdoise = {
      disponible: ardoiseAvailable.classList.contains('active'),
      entree: {
        nom: document.getElementById('ardoiseEntreeName').value.trim(),
        prix: document.getElementById('ardoiseEntreePrice').value.trim(),
      },
      plat: {
        nom: document.getElementById('ardoisePlatName').value.trim(),
        prix: document.getElementById('ardoisePlatPrice').value.trim(),
        note: document.getElementById('ardoisePlatNote').value.trim(),
      },
      dessert: {
        nom: document.getElementById('ardoiseDessertName').value.trim(),
        prix: document.getElementById('ardoiseDessertPrice').value.trim(),
      },
      formule: {
        active: document.getElementById('ardoiseFormulaPrice').value.trim() !== '',
        prix: document.getElementById('ardoiseFormulaPrice').value.trim(),
        label: 'Entrée + Plat + Dessert',
      },
    };

    setToStorage('ARDOISE', updatedArdoise);
    updateArdoisePreview(updatedArdoise);
    showNotification('Ardoise mise à jour ✓', 'success');
  });
}

function populateArdoiseForm(ardoise) {
  document.getElementById('ardoisePlatName').value = ardoise.plat.nom || '';
  document.getElementById('ardoisePlatPrice').value = ardoise.plat.prix || '';
  document.getElementById('ardoisePlatNote').value = ardoise.plat.note || '';
  document.getElementById('ardoiseEntreeName').value = ardoise.entree.nom || '';
  document.getElementById('ardoiseEntreePrice').value = ardoise.entree.prix || '';
  document.getElementById('ardoiseDessertName').value = ardoise.dessert.nom || '';
  document.getElementById('ardoiseDessertPrice').value = ardoise.dessert.prix || '';
  document.getElementById('ardoiseFormulaPrice').value = ardoise.formule.prix || '';
}

function updateArdoisePreview(ardoise) {
  const preview = document.getElementById('ardoisePreview');

  if (!ardoise.disponible) {
    preview.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Ardoise non disponible</p>';
    return;
  }

  let html = '';

  if (ardoise.entree.nom) {
    html += `
      <div class="ardoise-preview-item">
        <span class="ardoise-preview-name">Entrée</span>
        <span class="ardoise-preview-price">${ardoise.entree.prix}</span>
      </div>
      <div style="font-size: 0.85rem; color: var(--text-secondary); margin-left: 1rem; margin-bottom: 0.5rem;">${ardoise.entree.nom}</div>
    `;
  }

  html += `
    <div class="ardoise-preview-item">
      <span class="ardoise-preview-name">Plat du jour</span>
      <span class="ardoise-preview-price">${ardoise.plat.prix}</span>
    </div>
    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-left: 1rem; margin-bottom: 0.5rem;">${ardoise.plat.nom}</div>
  `;

  if (ardoise.plat.note) {
    html += `<div class="ardoise-preview-note">${ardoise.plat.note}</div>`;
  }

  if (ardoise.dessert.nom) {
    html += `
      <div class="ardoise-preview-item" style="margin-top: 1rem;">
        <span class="ardoise-preview-name">Dessert</span>
        <span class="ardoise-preview-price">${ardoise.dessert.prix}</span>
      </div>
      <div style="font-size: 0.85rem; color: var(--text-secondary); margin-left: 1rem; margin-bottom: 0.5rem;">${ardoise.dessert.nom}</div>
    `;
  }

  if (ardoise.formule.active && ardoise.formule.prix) {
    html += `
      <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(83, 135, 94, 0.2);">
        <div class="ardoise-preview-item" style="font-weight: 700;">
          <span>Formule</span>
          <span class="ardoise-preview-price">${ardoise.formule.prix}</span>
        </div>
        <div style="font-size: 0.85rem; color: var(--text-secondary); margin-left: 1rem;">Entrée + Plat + Dessert</div>
      </div>
    `;
  }

  preview.innerHTML = html;
}

// ========== MENU DISPLAY ==========
function renderMenuContent() {
  const menu = getFromStorage('MENU', DEMO_MENU);
  const container = document.getElementById('menuContent');

  if (!menu.categories || menu.categories.length === 0) {
    container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Aucune catégorie disponible</p>';
    return;
  }

  const html = menu.categories
    .sort((a, b) => a.ordre - b.ordre)
    .map((category) => {
      const platsHtml = category.plats
        .map(
          (plat) => `
        <div style="padding: 1rem; border-bottom: 1px solid rgba(68, 68, 68, 0.08); display: grid; grid-template-columns: 1fr auto; gap: 1rem; align-items: start;">
          <div>
            <div style="font-weight: 600; color: var(--text-main);">${plat.nom}</div>
            ${plat.description ? `<div style="font-size: 0.9rem; color: var(--text-secondary);">${plat.description}</div>` : ''}
            ${
              !plat.disponible
                ? '<div style="text-decoration: line-through; color: var(--text-secondary); font-size: 0.9rem; margin-top: 0.25rem;">Non disponible</div>'
                : ''
            }
          </div>
          <div style="font-weight: 700; color: var(--accent); white-space: nowrap;">${plat.prix}</div>
        </div>
      `
        )
        .join('');

      return `
        <div style="margin-bottom: 2rem;">
          <h4 style="font-family: var(--font-titles); font-size: 1.2rem; color: var(--accent); margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--accent);">${category.nom}</h4>
          <div>${platsHtml}</div>
        </div>
      `;
    })
    .join('');

  container.innerHTML = html;
}

// ========== DASHBOARD INITIALIZATION ==========
function initDashboard() {
  calculateKPIs();
  renderTodayReservations();
  renderFullReservationsList();
  renderMenuContent();
  initArdoiseForm();
  initTabs();
  initFilterButtons();
}

// ========== PAGE LOAD ==========
document.addEventListener('DOMContentLoaded', () => {
  ensureInitialData();

  // Check if already logged in
  if (sessionStorage.getItem('admin_logged_in') === 'true') {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('dashboard').classList.add('visible');
    initDashboard();
  } else {
    document.getElementById('dashboard').classList.remove('visible');
    document.getElementById('loginScreen').classList.remove('hidden');
  }

  initLoginForm();
  initLogout();
});