/**
 * POINTE DE RÊVE — script.js
 * Gestion du formulaire de réservation, menu dynamique, ardoise du jour
 * Stack : HTML5 + CSS3 + JavaScript vanilla (ES6+)
 */

// ========== CONFIGURATION ==========

const CONFIG = {
  storageKeys: {
    reservations: 'actions_recues',
    editableContent: 'contenu_editable',
    deletedDemoIds: 'deletedDemoIds',
  },
};

// ========== DONNÉES DE DÉMONSTRATION ==========

/**
 * Calcule une date offset par rapport à aujourd'hui
 * @param {number} days - Nombre de jours (0 = aujourd'hui)
 * @returns {string} - Date au format ISO YYYY-MM-DD
 */
function offsetDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

// Données démo — Réservations
const DEMO_RESERVATIONS = [
  {
    id: 'demo-1',
    prenom: 'Marie D.',
    telephone: '06 12 34 56 78',
    date: offsetDate(1),
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
    date: offsetDate(1),
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
    date: offsetDate(2),
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
    date: offsetDate(3),
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
    date: offsetDate(4),
    service: 'diner',
    couverts: '8',
    message: 'Repas d\'entreprise',
    statut: 'Annulée',
    source: 'demo',
  },
];

// Données démo — Carte des menus
const DEMO_MENU_CARD = {
  categories: [
    {
      id: 'cat-1',
      nom: 'Entrées',
      ordre: 1,
      plats: [
        {
          id: 'plat-ent-1',
          nom: 'Terrine de foie gras maison',
          prix: '14,00 €',
          description: 'Chutney de figues, brioche toastée',
          disponible: true,
        },
        {
          id: 'plat-ent-2',
          nom: 'Carpaccio de saint-jacques',
          prix: '16,00 €',
          description: 'Citron confit, roquette fraise',
          disponible: true,
        },
        {
          id: 'plat-ent-3',
          nom: 'Velouté de butternut',
          prix: '8,00 €',
          description: 'Crème fraîche, pignons de pin',
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
          id: 'plat-main-1',
          nom: 'Magret de canard',
          prix: '21,00 €',
          description: 'Jus de cerise, légumes de saison',
          disponible: true,
        },
        {
          id: 'plat-main-2',
          nom: 'Filet de bœuf sauce poivre',
          prix: '24,00 €',
          description: 'Pommes château, petits légumes',
          disponible: true,
        },
        {
          id: 'plat-main-3',
          nom: 'Sole meunière',
          prix: '22,00 €',
          description: 'Beurre citron, pommes pailles',
          disponible: true,
        },
        {
          id: 'plat-main-4',
          nom: 'Blanquette de veau',
          prix: '18,00 €',
          description: 'Champignons, oignons, crème fraîche',
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
          id: 'plat-des-1',
          nom: 'Tarte tatin maison',
          prix: '7,00 €',
          description: 'Glace vanille',
          disponible: true,
        },
        {
          id: 'plat-des-2',
          nom: 'Fondant au chocolat',
          prix: '7,50 €',
          description: 'Glace vanille, sauce caramel',
          disponible: true,
        },
        {
          id: 'plat-des-3',
          nom: 'Mousse au chocolat blanc',
          prix: '6,50 €',
          description: 'Fruits rouges, tuile chocolat',
          disponible: true,
        },
      ],
    },
  ],
};

// Données démo — Ardoise du jour
const DEMO_ARDOISE = {
  disponible: true,
  entree: { nom: 'Velouté de butternut, crème fraîche', prix: '8,00 €' },
  plat: {
    nom: 'Magret de canard, jus de cerise',
    prix: '21,00 €',
    note: 'Cuisson selon votre goût',
  },
  dessert: { nom: 'Tarte tatin maison, glace vanille', prix: '7,00 €' },
  formule: {
    active: true,
    prix: '31,00 €',
    label: 'Entrée + Plat + Dessert',
  },
};

// ========== UTILITAIRES ==========

/**
 * Parse safe de JSON
 */
function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try {
    return JSON.parse(rawValue);
  } catch (e) {
    return fallbackValue;
  }
}

/**
 * Initialise les données de démonstration si absent
 */
function ensureInitialData() {
  const existing = localStorage.getItem(CONFIG.storageKeys.reservations);
  if (!existing) {
    localStorage.setItem(
      CONFIG.storageKeys.reservations,
      JSON.stringify(DEMO_RESERVATIONS)
    );
  }

  const existingMenu = localStorage.getItem(CONFIG.storageKeys.editableContent);
  if (!existingMenu) {
    localStorage.setItem(
      CONFIG.storageKeys.editableContent,
      JSON.stringify({
        ardoise: DEMO_ARDOISE,
      })
    );
  }
}

// ========== GESTION DU MENU ==========

/**
 * Récupère la carte des menus depuis localStorage ou démo
 */
function getMenuCard() {
  const stored = localStorage.getItem('menuCard');
  return safeParse(stored, DEMO_MENU_CARD);
}

/**
 * Affiche le menu avec onglets
 */
function renderMenu() {
  const menuCard = getMenuCard();
  const categories = menuCard.categories || [];

  const menuTabsContainer = document.getElementById('menuTabs');
  const menuContentContainer = document.getElementById('menuContent');

  if (!menuTabsContainer || !menuContentContainer) return;

  // Nettoyage
  menuTabsContainer.innerHTML = '';
  menuContentContainer.innerHTML = '';

  if (categories.length === 0) {
    menuContentContainer.innerHTML =
      '<p style="text-align: center; color: var(--text-secondary);">Menu à venir</p>';
    return;
  }

  // Création des onglets
  categories.forEach((cat, index) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'menu-tab' + (index === 0 ? ' active' : '');
    btn.textContent = cat.nom;
    btn.dataset.categoryId = cat.id;
    btn.addEventListener('click', () => {
      // Désactiver tous les onglets
      document.querySelectorAll('.menu-tab').forEach((t) => {
        t.classList.remove('active');
      });
      // Activer l'onglet cliqué
      btn.classList.add('active');
      // Afficher le contenu
      renderMenuCategory(cat);
    });
    menuTabsContainer.appendChild(btn);
  });

  // Afficher la 1ère catégorie par défaut
  if (categories.length > 0) {
    renderMenuCategory(categories[0]);
  }
}

/**
 * Affiche les plats d'une catégorie
 */
function renderMenuCategory(category) {
  const menuContentContainer = document.getElementById('menuContent');
  if (!menuContentContainer) return;

  menuContentContainer.innerHTML = '';

  const itemsContainer = document.createElement('div');
  itemsContainer.className = 'menu-items';

  if (!category.plats || category.plats.length === 0) {
    itemsContainer.innerHTML =
      '<p style="text-align: center; color: var(--text-secondary);">Aucun plat disponible</p>';
    menuContentContainer.appendChild(itemsContainer);
    return;
  }

  category.plats.forEach((plat) => {
    const itemDiv = document.createElement('div');
    itemDiv.className = 'menu-item' + (!plat.disponible ? ' unavailable' : '');

    const contentDiv = document.createElement('div');
    contentDiv.className = 'menu-item-content';

    const title = document.createElement('h4');
    title.textContent = plat.nom;
    contentDiv.appendChild(title);

    if (plat.description) {
      const desc = document.createElement('p');
      desc.className = 'menu-item-description';
      desc.textContent = plat.description;
      contentDiv.appendChild(desc);
    }

    itemDiv.appendChild(contentDiv);

    const priceDiv = document.createElement('div');
    priceDiv.className = 'menu-item-price';
    priceDiv.textContent = plat.prix;
    itemDiv.appendChild(priceDiv);

    itemsContainer.appendChild(itemDiv);
  });

  menuContentContainer.appendChild(itemsContainer);
}

// ========== GESTION DE L'ARDOISE ==========

/**
 * Récupère l'ardoise du jour depuis localStorage
 */
function getArdoise() {
  const content = localStorage.getItem(CONFIG.storageKeys.editableContent);
  const parsed = safeParse(content, {});
  return parsed.ardoise || DEMO_ARDOISE;
}

/**
 * Affiche l'ardoise du jour
 */
function renderArdoise() {
  const ardoise = getArdoise();
  const ardoiseSection = document.getElementById('ardoise');
  const ardoiseContent = document.getElementById('ardoiseContent');

  if (!ardoiseSection || !ardoiseContent) return;

  // Masquer/afficher la section entière
  if (!ardoise.disponible) {
    ardoiseSection.classList.add('hidden');
    return;
  }

  ardoiseSection.classList.remove('hidden');

  let html = '';

  // Entrée
  if (ardoise.entree && ardoise.entree.nom) {
    html += `
      <div class="ardoise-item">
        <div class="ardoise-item-name">🥂 Entrée : ${ardoise.entree.nom}</div>
        <div class="ardoise-item-price">${ardoise.entree.prix}</div>
      </div>
    `;
  }

  // Plat principal
  if (ardoise.plat && ardoise.plat.nom) {
    html += `
      <div class="ardoise-item">
        <div>
          <div class="ardoise-item-name">🍽️ Plat : ${ardoise.plat.nom}</div>
          ${
            ardoise.plat.note
              ? `<div class="ardoise-item-note">${ardoise.plat.note}</div>`
              : ''
          }
        </div>
        <div class="ardoise-item-price">${ardoise.plat.prix}</div>
      </div>
    `;
  }

  // Dessert
  if (ardoise.dessert && ardoise.dessert.nom) {
    html += `
      <div class="ardoise-item">
        <div class="ardoise-item-name">🍮 Dessert : ${ardoise.dessert.nom}</div>
        <div class="ardoise-item-price">${ardoise.dessert.prix}</div>
      </div>
    `;
  }

  // Formule
  if (ardoise.formule && ardoise.formule.active) {
    html += `
      <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 2px solid rgba(83, 135, 94, 0.2);">
        <div class="ardoise-item" style="margin-bottom: 0; padding-bottom: 0; border-bottom: none;">
          <div class="ardoise-item-name" style="font-weight: 700;">
            ✨ ${ardoise.formule.label}
          </div>
          <div class="ardoise-item-price" style="font-size: 1.3rem;">
            ${ardoise.formule.prix}
          </div>
        </div>
      </div>
    `;
  }

  ardoiseContent.innerHTML = html || '<p>Ardoise à venir</p>';
}

// ========== GESTION DU FORMULAIRE DE RÉSERVATION ==========

/**
 * Initialise la sélection du service
 */
function initServiceSelector() {
  const serviceCards = document.querySelectorAll('.service-card');
  const serviceInput = document.getElementById('service');

  serviceCards.forEach((card) => {
    card.addEventListener('click', () => {
      // Désélectionner tous
      serviceCards.forEach((c) => c.classList.remove('selected'));
      // Sélectionner celui-ci
      card.classList.add('selected');
      // Mettre à jour l'input caché
      serviceInput.value = card.dataset.service;
    });
  });
}

/**
 * Initialise le stepper des couverts
 */
function initStepper() {
  const stepperMinus = document.querySelector('.stepper-minus');
  const stepperPlus = document.querySelector('.stepper-plus');
  const covertsInput = document.getElementById('couverts');

  if (stepperMinus) {
    stepperMinus.addEventListener('click', (e) => {
      e.preventDefault();
      const val = parseInt(covertsInput.value, 10);
      if (val > 1) {
        covertsInput.value = val - 1;
      }
    });
  }

  if (stepperPlus) {
    stepperPlus.addEventListener('click', (e) => {
      e.preventDefault();
      const val = parseInt(covertsInput.value, 10);
      if (val < 12) {
        covertsInput.value = val + 1;
      }
    });
  }
}

/**
 * Définit la date minimale du formulaire à aujourd'hui
 */
function initDateInput() {
  const dateInput = document.getElementById('date');
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;
  }
}

/**
 * Gère la soumission du formulaire
 */
function initFormSubmit() {
  const form = document.getElementById('reservationForm');

  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    // Validation du service
    const serviceInput = document.getElementById('service');
    if (!serviceInput.value) {
      alert('Veuillez sélectionner un service');
      return;
    }

    // Récupération des données
    const prenom = document.getElementById('prenom').value.trim();
    const telephone = document.getElementById('telephone').value.trim();
    const date = document.getElementById('date').value;
    const couverts = document.getElementById('couverts').value;
    const message = document.getElementById('message').value.trim();
    const service = serviceInput.value;

    // Création de la réservation
    const reservation = {
      id: Date.now().toString(),
      prenom,
      telephone,
      date,
      service,
      couverts,
      message,
      statut: 'En attente',
      source: 'formulaire',
    };

    // Sauvegarde dans localStorage
    const existing = safeParse(
      localStorage.getItem(CONFIG.storageKeys.reservations),
      []
    );
    existing.push(reservation);
    localStorage.setItem(
      CONFIG.storageKeys.reservations,
      JSON.stringify(existing)
    );

    // Affichage du message de confirmation
    const confirmMsg = document.getElementById('confirmationMessage');
    if (confirmMsg) {
      confirmMsg.classList.add('show');
      setTimeout(() => {
        confirmMsg.classList.remove('show');
      }, 4000);
    }

    // Réinitialisation du formulaire
    form.reset();
    document.getElementById('service').value = '';
    document.querySelectorAll('.service-card').forEach((c) => {
      c.classList.remove('selected');
    });
    document.getElementById('couverts').value = '2';

    // Scroll vers le haut du formulaire
    form.scrollIntoView({ behavior: 'smooth' });
  });
}

// ========== INITIALISATION ==========

document.addEventListener('DOMContentLoaded', () => {
  // Initialiser les données de démo
  ensureInitialData();

  // Rendre le menu
  renderMenu();

  // Rendre l'ardoise
  renderArdoise();

  // Initialiser les contrôles du formulaire
  initServiceSelector();
  initStepper();
  initDateInput();
  initFormSubmit();

  // Écoute des changements localStorage pour l'ardoise (admin → index)
  window.addEventListener('storage', (e) => {
    if (e.key === CONFIG.storageKeys.editableContent) {
      renderArdoise();
    }
    if (e.key === 'menuCard') {
      renderMenu();
    }
  });
});

// ========== SMOOTH SCROLL POUR LES ANCRES ==========

document.addEventListener('click', (e) => {
  if (e.target.tagName === 'A' && e.target.getAttribute('href').startsWith('#')) {
    const href = e.target.getAttribute('href');
    const target = document.querySelector(href);
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth' });
    }
  }
});