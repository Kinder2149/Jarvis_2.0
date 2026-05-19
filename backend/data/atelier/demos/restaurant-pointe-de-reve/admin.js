/**
 * admin.js — Restaurant Pointe de Rêve
 * Gestion administrateur : authentification, réservations, ardoise
 * Contrat localStorage : DEMO_RESERVATIONS, DEMO_ARDOISE, DEMO_ARDOISE_DISPONIBLE, DEMO_INITIALIZED
 */

// ====================================================================
// CONSTANTES
// ====================================================================

const MOT_DE_PASSE_ADMIN = 'admin';

const HEURES_DEJEUNER = ['12h00', '12h30', '13h00', '13h30'];
const HEURES_DINER = ['19h00', '19h30', '20h00', '20h30', '21h00'];

// ====================================================================
// DONNÉES PAR DÉFAUT
// ====================================================================

function offsetDate(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

const DEMO_RESERVATIONS_DEFAULT = [
  {
    id: "demo-1",
    nom: "Marie Dupont",
    email: "marie.dupont@exemple.com",
    tel: "06 45 78 92 34",
    date: offsetDate(1),
    heure: "20h00",
    personnes: 4,
    message: "Première visite, nous avons hâte de découvrir votre cuisine !",
    statut: "En attente",
    source: "demo",
    createdAt: "2025-01-23T10:30:00.000Z"
  },
  {
    id: "demo-2",
    nom: "Pierre Martin",
    email: "p.martin@exemple.com",
    tel: "07 82 45 61 93",
    date: offsetDate(1),
    heure: "12h30",
    personnes: 2,
    message: "",
    statut: "Confirmée",
    source: "demo",
    createdAt: "2025-01-22T14:20:00.000Z"
  },
  {
    id: "demo-3",
    nom: "Sophie Rousseau",
    email: "sophie.rousseau@exemple.com",
    tel: "06 91 23 45 67",
    date: offsetDate(2),
    heure: "19h30",
    personnes: 6,
    message: "Repas en famille, y a-t-il une table au calme ?",
    statut: "En attente",
    source: "demo",
    createdAt: "2025-01-23T09:15:00.000Z"
  },
  {
    id: "demo-4",
    nom: "Jean-Luc Perrin",
    email: "jl.perrin@exemple.com",
    tel: "06 34 56 78 90",
    date: offsetDate(3),
    heure: "13h00",
    personnes: 3,
    message: "Déjeuner entre collègues",
    statut: "En attente",
    source: "demo",
    createdAt: "2025-01-23T08:45:00.000Z"
  },
  {
    id: "demo-5",
    nom: "Isabelle Girard",
    email: "i.girard@exemple.com",
    tel: "07 65 43 21 89",
    date: offsetDate(4),
    heure: "20h30",
    personnes: 8,
    message: "Anniversaire surprise - pourriez-vous prévoir un gâteau ?",
    statut: "Annulée",
    source: "demo",
    createdAt: "2025-01-21T16:30:00.000Z"
  }
];

const DEMO_ARDOISE_DEFAULT = {
  disponible: true,
  plat: "Blanquette de veau à l'ancienne",
  plat_prix: "16,50 €",
  plat_note: "Mijotée pendant 3 heures, servie avec son riz basmati",
  entree: "Terrine maison et ses pickles",
  entree_prix: "9,50 €",
  dessert: "Tarte tatin tiède",
  dessert_prix: "7,50 €"
};

// ====================================================================
// UTILITAIRES
// ====================================================================

/**
 * Parse sécurisé localStorage
 */
function safeParse(key, fallback) {
  try {
    const value = JSON.parse(localStorage.getItem(key));
    return value || fallback;
  } catch (e) {
    return fallback;
  }
}

/**
 * Initialise les données par défaut si première visite
 */
function ensureInitialData() {
  if (!localStorage.getItem('DEMO_INITIALIZED')) {
    localStorage.setItem(
      'DEMO_RESERVATIONS',
      JSON.stringify(DEMO_RESERVATIONS_DEFAULT)
    );
    localStorage.setItem(
      'DEMO_ARDOISE',
      JSON.stringify(DEMO_ARDOISE_DEFAULT)
    );
    localStorage.setItem('DEMO_ARDOISE_DISPONIBLE', 'true');
    localStorage.setItem('DEMO_INITIALIZED', 'true');
  }
}

/**
 * Formate une date "YYYY-MM-DD" en "DD/MM/YYYY"
 */
function formatDateFr(dateStr) {
  if (!dateStr) return '';
  const [year, month, day] = dateStr.split('-');
  return `${day}/${month}/${year}`;
}

/**
 * Affiche une notification inline
 */
function showNotification(elementId, duration = 3000) {
  const element = document.getElementById(elementId);
  if (!element) return;
  element.classList.remove('hidden');
  element.style.display = 'block';
  if (duration > 0) {
    setTimeout(() => {
      element.classList.add('hidden');
      element.style.display = 'none';
    }, duration);
  }
}

// ====================================================================
// AUTHENTIFICATION
// ====================================================================

/**
 * Gère la connexion administrateur
 */
function handleLogin() {
  const passwordInput = document.getElementById('passwordInput');
  const loginError = document.getElementById('loginError');
  const password = passwordInput ? passwordInput.value : '';

  if (password === MOT_DE_PASSE_ADMIN) {
    sessionStorage.setItem('admin_session', '1');
    showLoginScreen(false);
    initDashboard();
  } else {
    if (loginError) {
      loginError.textContent = '❌ Mot de passe incorrect.';
      loginError.classList.remove('hidden');
      loginError.style.display = 'block';
    }
    if (passwordInput) {
      passwordInput.value = '';
      passwordInput.focus();
    }
  }
}

/**
 * Affiche ou masque l'écran de login
 */
function showLoginScreen(visible) {
  const loginScreen = document.getElementById('loginScreen');
  const dashboard = document.getElementById('dashboard');

  if (visible) {
    if (loginScreen) {
      loginScreen.classList.remove('hidden');
      loginScreen.style.display = 'block';
    }
    if (dashboard) {
      dashboard.classList.add('hidden');
      dashboard.style.display = 'none';
    }
  } else {
    if (loginScreen) {
      loginScreen.classList.add('hidden');
      loginScreen.style.display = 'none';
    }
    if (dashboard) {
      dashboard.classList.remove('hidden');
      dashboard.style.display = 'block';
    }
  }
}

/**
 * Gère la déconnexion
 */
function handleLogout() {
  sessionStorage.removeItem('admin_session');
  const passwordInput = document.getElementById('passwordInput');
  if (passwordInput) {
    passwordInput.value = '';
  }
  const loginError = document.getElementById('loginError');
  if (loginError) {
    loginError.textContent = '';
    loginError.classList.add('hidden');
  }
  showLoginScreen(true);
}

// ====================================================================
// KPIs & STATISTIQUES
// ====================================================================

/**
 * Calcule et affiche les KPIs du jour
 */
function calculateKPIs() {
  const reservations = safeParse('DEMO_RESERVATIONS', []);
  const today = new Date().toISOString().split('T')[0];

  let lunchCovers = 0;
  let dinnerCovers = 0;
  let pending = 0;

  reservations.forEach((r) => {
    if (r.date === today && r.statut === 'Confirmée') {
      if (HEURES_DEJEUNER.includes(r.heure)) {
        lunchCovers += parseInt(r.personnes || 0);
      } else if (HEURES_DINER.includes(r.heure)) {
        dinnerCovers += parseInt(r.personnes || 0);
      }
    }
    if (r.statut === 'En attente') {
      pending += 1;
    }
  });

  const kpiLunch = document.getElementById('kpiLunch');
  const kpiDiner = document.getElementById('kpiDiner');
  const kpiPending = document.getElementById('kpiPending');

  if (kpiLunch) kpiLunch.textContent = lunchCovers.toString();
  if (kpiDiner) kpiDiner.textContent = dinnerCovers.toString();
  if (kpiPending) kpiPending.textContent = pending.toString();
}

// ====================================================================
// AFFICHAGE DES RÉSERVATIONS
// ====================================================================

/**
 * Crée une carte de réservation HTML
 */
function createReservationCard(reservation) {
  const card = document.createElement('div');
  card.className = 'reservation-card';
  card.style.cssText = `
    background: var(--bg-alt);
    border: 1px solid var(--border-soft);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  `;

  // En-tête avec nom et statut
  const header = document.createElement('div');
  header.style.cssText = `
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  `;

  const nameEl = document.createElement('div');
  nameEl.style.cssText = `
    font-weight: 600;
    font-size: 1rem;
    color: var(--text-main);
  `;
  nameEl.textContent = reservation.nom;

  const statusBadge = document.createElement('span');
  statusBadge.style.cssText = `
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    font-weight: 500;
    ${
      reservation.statut === 'En attente'
        ? 'background: #FFF3CD; color: #856404;'
        : reservation.statut === 'Confirmée'
          ? 'background: #D4EDDA; color: #155724;'
          : 'background: #F8D7DA; color: #721C24;'
    }
  `;
  statusBadge.textContent = reservation.statut;

  header.appendChild(nameEl);
  header.appendChild(statusBadge);
  card.appendChild(header);

  // Détails
  const details = document.createElement('div');
  details.style.cssText = `
    display: grid;
    gap: 0.5rem;
    font-size: 0.95rem;
    color: var(--text-secondary);
  `;

  const dateHeure = document.createElement('p');
  dateHeure.style.margin = '0';
  dateHeure.innerHTML = `
    <strong>Date & heure :</strong> ${formatDateFr(reservation.date)} à ${reservation.heure}
  `;
  details.appendChild(dateHeure);

  const personnes = document.createElement('p');
  personnes.style.margin = '0';
  personnes.textContent = `${reservation.personnes} couverts`;
  details.appendChild(personnes);

  const tel = document.createElement('p');
  tel.style.margin = '0';
  tel.innerHTML = `
    <strong>Téléphone :</strong> <a href="tel:${reservation.tel}" style="color: var(--accent); text-decoration: none;">${reservation.tel}</a>
  `;
  details.appendChild(tel);

  if (reservation.email) {
    const email = document.createElement('p');
    email.style.margin = '0';
    email.innerHTML = `
      <strong>Email :</strong> <a href="mailto:${reservation.email}" style="color: var(--accent); text-decoration: none;">${reservation.email}</a>
    `;
    details.appendChild(email);
  }

  if (reservation.message) {
    const message = document.createElement('p');
    message.style.cssText = `margin: 0; padding-top: 0.5rem; font-style: italic; border-top: 1px solid var(--border-soft); padding-top: 0.75rem;`;
    message.innerHTML = `<strong>Message :</strong> ${reservation.message}`;
    details.appendChild(message);
  }

  card.appendChild(details);

  // Boutons d'action (si En attente)
  if (reservation.statut === 'En attente') {
    const actions = document.createElement('div');
    actions.style.cssText = `
      display: flex;
      gap: 1rem;
      margin-top: 1rem;
      flex-wrap: wrap;
    `;

    const confirmBtn = document.createElement('button');
    confirmBtn.type = 'button';
    confirmBtn.className = 'btn-primary';
    confirmBtn.style.cssText = `
      flex: 1;
      min-width: 150px;
      padding: 0.75rem;
      border: none;
      border-radius: var(--radius-sm);
      background: var(--accent);
      color: white;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s;
    `;
    confirmBtn.textContent = '✓ Confirmer';
    confirmBtn.addEventListener('click', () => {
      updateReservationStatus(reservation.id, 'Confirmée');
    });
    confirmBtn.addEventListener('mouseover', () => {
      confirmBtn.style.opacity = '0.9';
    });
    confirmBtn.addEventListener('mouseout', () => {
      confirmBtn.style.opacity = '1';
    });

    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'btn-secondary';
    cancelBtn.style.cssText = `
      flex: 1;
      min-width: 150px;
      padding: 0.75rem;
      border: 1px solid #DC3545;
      border-radius: var(--radius-sm);
      background: transparent;
      color: #DC3545;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s;
    `;
    cancelBtn.textContent = '✗ Annuler';
    cancelBtn.addEventListener('click', () => {
      updateReservationStatus(reservation.id, 'Annulée');
    });
    cancelBtn.addEventListener('mouseover', () => {
      cancelBtn.style.opacity = '0.9';
    });
    cancelBtn.addEventListener('mouseout', () => {
      cancelBtn.style.opacity = '1';
    });

    actions.appendChild(confirmBtn);
    actions.appendChild(cancelBtn);
    card.appendChild(actions);
  }

  return card;
}

/**
 * Met à jour le statut d'une réservation et rafraîchit l'affichage
 */
function updateReservationStatus(reservationId, newStatus) {
  const reservations = safeParse('DEMO_RESERVATIONS', []);
  const reservation = reservations.find((r) => r.id === reservationId);

  if (reservation) {
    reservation.statut = newStatus;
    localStorage.setItem('DEMO_RESERVATIONS', JSON.stringify(reservations));
    calculateKPIs();
    renderReservations('all');

    // Notification inline
    const notificationDiv = document.createElement('div');
    notificationDiv.className = 'notification notification-success';
    notificationDiv.style.cssText = `
      position: fixed;
      top: 2rem;
      right: 2rem;
      background: #D4EDDA;
      color: #155724;
      padding: 1rem;
      border-radius: var(--radius-sm);
      border: 1px solid #C3E6CB;
      z-index: 9999;
      animation: slideIn 0.3s ease-out;
    `;
    notificationDiv.textContent = `✓ Réservation ${newStatus.toLowerCase()}`;
    document.body.appendChild(notificationDiv);
    setTimeout(() => {
      notificationDiv.remove();
    }, 3000);
  }
}

/**
 * Affiche la liste des réservations selon filtre
 */
function renderReservations(filter = 'all') {
  const reservationsList = document.getElementById('reservationsList');
  const noReservations = document.getElementById('noReservations');
  const priorityList = document.getElementById('priorityList');
  const noPriority = document.getElementById('noPriority');

  if (!reservationsList) return;

  const reservations = safeParse('DEMO_RESERVATIONS', []);

  // Filtrer
  let filtered = reservations;
  if (filter === 'pending') {
    filtered = reservations.filter((r) => r.statut === 'En attente');
  } else if (filter === 'confirmed') {
    filtered = reservations.filter((r) => r.statut === 'Confirmée');
  } else if (filter === 'cancelled') {
    filtered = reservations.filter((r) => r.statut === 'Annulée');
  }

  // Trier par date/heure
  filtered.sort((a, b) => {
    const dateA = new Date(`${a.date}T${a.heure.replace('h', ':')}`);
    const dateB = new Date(`${b.date}T${b.heure.replace('h', ':')}`);
    return dateA - dateB;
  });

  // Afficher
  reservationsList.innerHTML = '';
  if (filtered.length === 0) {
    noReservations.classList.remove('hidden');
    noReservations.style.display = 'block';
  } else {
    noReservations.classList.add('hidden');
    noReservations.style.display = 'none';
    filtered.forEach((res) => {
      const card = createReservationCard(res);
      reservationsList.appendChild(card);
    });
  }

  // Section "À traiter en priorité" (En attente triées par date)
  if (priorityList) {
    const pending = reservations
      .filter((r) => r.statut === 'En attente')
      .sort((a, b) => {
        const dateA = new Date(`${a.date}T${a.heure.replace('h', ':')}`);
        const dateB = new Date(`${b.date}T${b.heure.replace('h', ':')}`);
        return dateA - dateB;
      })
      .slice(0, 3);

    priorityList.innerHTML = '';
    if (pending.length === 0) {
      if (noPriority) {
        noPriority.classList.remove('hidden');
        noPriority.style.display = 'block';
      }
    } else {
      if (noPriority) {
        noPriority.classList.add('hidden');
        noPriority.style.display = 'none';
      }
      pending.forEach((res) => {
        const card = createReservationCard(res);
        priorityList.appendChild(card);
      });
    }
  }
}

// ====================================================================
// ARDOISE DU JOUR
// ====================================================================

/**
 * Charge l'ardoise dans le formulaire admin
 */
function loadArdoiseForm() {
  const ardoise = safeParse('DEMO_ARDOISE', DEMO_ARDOISE_DEFAULT);
  const disponible = localStorage.getItem('DEMO_ARDOISE_DISPONIBLE') === 'true';

  const adminPlat = document.getElementById('admin-plat');
  const adminPlatPrix = document.getElementById('admin-plat-prix');
  const adminPlatNote = document.getElementById('admin-plat-note');
  const adminEntree = document.getElementById('admin-entree');
  const adminEntreePrix = document.getElementById('admin-entree-prix');
  const adminDessert = document.getElementById('admin-dessert');
  const adminDessertPrix = document.getElementById('admin-dessert-prix');
  const ardoiseToggle = document.getElementById('ardoise-toggle');

  if (adminPlat) adminPlat.value = ardoise.plat || '';
  if (adminPlatPrix) adminPlatPrix.value = ardoise.plat_prix || '';
  if (adminPlatNote) adminPlatNote.value = ardoise.plat_note || '';
  if (adminEntree) adminEntree.value = ardoise.entree || '';
  if (adminEntreePrix) adminEntreePrix.value = ardoise.entree_prix || '';
  if (adminDessert) adminDessert.value = ardoise.dessert || '';
  if (adminDessertPrix) adminDessertPrix.value = ardoise.dessert_prix || '';

  if (ardoiseToggle) {
    // Le toggle est un div avec classe toggle-switch-box — utiliser data-active
    if (disponible) {
      ardoiseToggle.setAttribute('data-active', 'true');
      ardoiseToggle.classList.add('active');
    } else {
      ardoiseToggle.removeAttribute('data-active');
      ardoiseToggle.classList.remove('active');
    }
  }

  updateArdoisePreview();
}

/**
 * Sauvegarde l'ardoise depuis le formulaire admin
 */
function saveArdoise() {
  const adminPlat = document.getElementById('admin-plat');
  const adminPlatPrix = document.getElementById('admin-plat-prix');
  const adminPlatNote = document.getElementById('admin-plat-note');
  const adminEntree = document.getElementById('admin-entree');
  const adminEntreePrix = document.getElementById('admin-entree-prix');
  const adminDessert = document.getElementById('admin-dessert');
  const adminDessertPrix = document.getElementById('admin-dessert-prix');
  const ardoiseToggle = document.getElementById('ardoise-toggle');

  // Validation : plat est obligatoire
  if (!adminPlat || !adminPlat.value.trim()) {
    alert('❌ Le plat du jour est obligatoire.');
    return;
  }

  const disponible = ardoiseToggle ? ardoiseToggle.classList.contains('active') : true;

  const ardoise = {
    disponible: disponible,
    plat: adminPlat.value,
    plat_prix: adminPlatPrix ? adminPlatPrix.value : '',
    plat_note: adminPlatNote ? adminPlatNote.value : '',
    entree: adminEntree ? adminEntree.value : '',
    entree_prix: adminEntreePrix ? adminEntreePrix.value : '',
    dessert: adminDessert ? adminDessert.value : '',
    dessert_prix: adminDessertPrix ? adminDessertPrix.value : ''
  };

  localStorage.setItem('DEMO_ARDOISE', JSON.stringify(ardoise));
  localStorage.setItem('DEMO_ARDOISE_DISPONIBLE', disponible ? 'true' : 'false');

  updateArdoisePreview();
  showNotification('ardoiseConfirmation', 3000);
}

/**
 * Actualise l'aperçu temps réel de l'ardoise
 */
function updateArdoisePreview() {
  const ardoise = safeParse('DEMO_ARDOISE', DEMO_ARDOISE_DEFAULT);
  const disponible = localStorage.getItem('DEMO_ARDOISE_DISPONIBLE') === 'true';

  const preview = document.getElementById('ardoisePreview');
  if (!preview) return;

  if (!disponible) {
    preview.innerHTML = '<p style="color: var(--text-secondary); font-style: italic;">Ardoise non disponible</p>';
    return;
  }

  let html = '<div style="display: grid; gap: 1.5rem;">';

  if (ardoise.entree) {
    html += `
      <div>
        <p style="margin: 0; font-weight: 600; color: var(--text-main);">${ardoise.entree}</p>
        <p style="margin: 0.25rem 0 0 0; color: var(--accent); font-weight: 600;">${ardoise.entree_prix || ''}</p>
      </div>
    `;
  }

  if (ardoise.plat) {
    html += `
      <div>
        <p style="margin: 0; font-weight: 600; color: var(--text-main);">${ardoise.plat}</p>
        ${ardoise.plat_note ? `<p style="margin: 0.25rem 0 0 0; color: var(--text-secondary); font-size: 0.9rem;">${ardoise.plat_note}</p>` : ''}
        <p style="margin: 0.25rem 0 0 0; color: var(--accent); font-weight: 600;">${ardoise.plat_prix || ''}</p>
      </div>
    `;
  }

  if (ardoise.dessert) {
    html += `
      <div>
        <p style="margin: 0; font-weight: 600; color: var(--text-main);">${ardoise.dessert}</p>
        <p style="margin: 0.25rem 0 0 0; color: var(--accent); font-weight: 600;">${ardoise.dessert_prix || ''}</p>
      </div>
    `;
  }

  html += '</div>';
  preview.innerHTML = html;
}

// ====================================================================
// ONGLETS (Réservations / Ardoise)
// ====================================================================

/**
 * Initialise les onglets du dashboard admin
 */
function initTabsAdmin() {
  const tabBtns = document.querySelectorAll('.tab-btn[data-tab]');
  const tabContents = document.querySelectorAll('.menu-tab-content');

  tabBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tabName = btn.getAttribute('data-tab');

      tabBtns.forEach((b) => b.classList.remove('active'));
      tabContents.forEach((c) => c.classList.remove('active'));

      btn.classList.add('active');
      const activeTab = document.getElementById(`${tabName}-tab`);
      if (activeTab) {
        activeTab.classList.add('active');
        activeTab.style.display = 'block';
      }
    });
  });
}

/**
 * Initialise les filtres de réservations
 */
function initFiltersAdmin() {
  const filterBtns = document.querySelectorAll('.filter-btn');

  filterBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const filter = btn.getAttribute('data-filter');

      filterBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');

      renderReservations(filter);
    });
  });
}

/**
 * Initialise le toggle de disponibilité de l'ardoise
 */
function initArdoiseToggle() {
  const ardoiseToggle = document.getElementById('ardoise-toggle');
  if (!ardoiseToggle) return;

  ardoiseToggle.addEventListener('click', () => {
    ardoiseToggle.classList.toggle('active');
    updateArdoisePreview();
  });
}

// ====================================================================
// INITIALISATION DU DASHBOARD
// ====================================================================

/**
 * Initialise le tableau de bord administrateur
 */
function initDashboard() {
  // Afficher la date du jour
  const currentDateEl = document.getElementById('currentDate');
  if (currentDateEl) {
    const now = new Date();
    const options = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    };
    currentDateEl.textContent = now.toLocaleDateString('fr-FR', options);
  }

  // Calculer et afficher KPIs
  calculateKPIs();

  // Afficher les réservations
  renderReservations('all');

  // Charger l'ardoise
  loadArdoiseForm();

  // Initialiser les onglets
  initTabsAdmin();

  // Initialiser les filtres
  initFiltersAdmin();

  // Initialiser le toggle ardoise
  initArdoiseToggle();

  // Bouton sauvegarder ardoise
  const saveArdoiseBtn = document.getElementById('saveArdoiseBtn');
  if (saveArdoiseBtn) {
    saveArdoiseBtn.addEventListener('click', saveArdoise);
  }
}

// ====================================================================
// LISTENERS GLOBAUX
// ====================================================================

window.addEventListener('storage', (e) => {
  if (sessionStorage.getItem('admin_session') === '1') {
    if (e.key === 'DEMO_RESERVATIONS') {
      calculateKPIs();
      renderReservations('all');
    } else if (e.key === 'DEMO_ARDOISE' || e.key === 'DEMO_ARDOISE_DISPONIBLE') {
      loadArdoiseForm();
    }
  }
});

// ====================================================================
// INITIALISATION
// ====================================================================

document.addEventListener('DOMContentLoaded', () => {
  ensureInitialData();

  // Récupérer l'état de session
  const isLoggedIn = sessionStorage.getItem('admin_session') === '1';

  if (isLoggedIn) {
    showLoginScreen(false);
    initDashboard();
  } else {
    showLoginScreen(true);

    // Bouton login
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
      loginBtn.addEventListener('click', handleLogin);
    }

    // Toggle password visibility
    const togglePasswordBtn = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('passwordInput');
    if (togglePasswordBtn && passwordInput) {
      togglePasswordBtn.addEventListener('click', () => {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
      });
    }

    // Entrée à la pression de Entrée
    const passwordInput2 = document.getElementById('passwordInput');
    if (passwordInput2) {
      passwordInput2.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          handleLogin();
        }
      });
    }

    // Clear login error on input
    const passwordInput3 = document.getElementById('passwordInput');
    if (passwordInput3) {
      passwordInput3.addEventListener('input', () => {
        const loginError = document.getElementById('loginError');
        if (loginError) {
          loginError.textContent = '';
          loginError.classList.add('hidden');
        }
      });
    }
  }

  // Bouton logout
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }
});