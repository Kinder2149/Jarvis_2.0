/* ============================================================================
   POINTE DE RÊVE — script.js
   ============================================================================
   Gestion front-end : formulaire, onglets, ardoise, localStorage
   ============================================================================ */

// ============================================================================
// UTILITAIRES
// ============================================================================

function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try {
    return JSON.parse(rawValue);
  } catch (e) {
    console.error('Parse error:', e);
    return fallbackValue;
  }
}

function offsetDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

function showFeedback(elementId, message, type = 'success', duration = 4000) {
  const el = document.getElementById(elementId);
  if (!el) return;
  
  el.className = `feedback-message visible feedback-${type}`;
  el.textContent = message;
  
  setTimeout(() => {
    el.classList.remove('visible');
  }, duration);
}

// ============================================================================
// DONNÉES DÉMO
// ============================================================================

const DEMO_RESERVATIONS = [
  {
    id: "demo-1",
    prenom: "Marie D.",
    telephone: "06 12 34 56 78",
    date: offsetDate(1),
    service: "diner",
    couverts: "2",
    message: "Anniversaire de mariage, si possible une table en retrait",
    statut: "En attente",
    source: "demo"
  },
  {
    id: "demo-2",
    prenom: "Thomas B.",
    telephone: "07 65 43 21 09",
    date: offsetDate(1),
    service: "dejeuner",
    couverts: "4",
    message: "",
    statut: "Confirmée",
    source: "demo"
  },
  {
    id: "demo-3",
    prenom: "Sophie M.",
    telephone: "06 98 76 54 32",
    date: offsetDate(2),
    service: "diner",
    couverts: "6",
    message: "Une personne allergique aux crustacés",
    statut: "En attente",
    source: "demo"
  },
  {
    id: "demo-4",
    prenom: "Laurent F.",
    telephone: "07 11 22 33 44",
    date: offsetDate(3),
    service: "dejeuner",
    couverts: "2",
    message: "Menu dégustation si disponible",
    statut: "Confirmée",
    source: "demo"
  },
  {
    id: "demo-5",
    prenom: "Isabelle R.",
    telephone: "06 55 44 33 22",
    date: offsetDate(4),
    service: "diner",
    couverts: "8",
    message: "Repas d'entreprise",
    statut: "Annulée",
    source: "demo"
  }
];

const DEMO_ARDOISE = {
  disponible: true,
  entree: { nom: "Velouté de butternut, crème fraîche", prix: "8,00 €" },
  plat: { nom: "Filet de bœuf, sauce au poivre", prix: "22,00 €", note: "Cuisson selon votre goût" },
  dessert: { nom: "Fondant au chocolat, glace vanille", prix: "7,00 €" },
  formule: { active: true, prix: "31,00 €", label: "Entrée + Plat + Dessert" }
};

// ============================================================================
// INITIALISATION DONNÉES
// ============================================================================

function ensureInitialData() {
  const existing = localStorage.getItem("actions_recues");
  if (!existing) {
    localStorage.setItem("actions_recues", JSON.stringify(DEMO_RESERVATIONS));
  }

  const existingArdoise = localStorage.getItem("contenu_editable");
  if (!existingArdoise) {
    localStorage.setItem("contenu_editable", JSON.stringify({
      suggestion_du_jour: {
        plat: "Filet de bœuf, sauce au poivre",
        prix: "22,00 €",
        note: "Cuisson selon votre goût"
      }
    }));
  }
}

// ============================================================================
// GESTION ONGLETS MENU
// ============================================================================

function initMenuTabs() {
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabContents = document.querySelectorAll('.tab-content');

  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      const tabName = button.getAttribute('data-tab');

      // Désactiver tous les onglets
      tabButtons.forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
      });
      tabContents.forEach(content => {
        content.classList.remove('active');
      });

      // Activer l'onglet cliqué
      button.classList.add('active');
      button.setAttribute('aria-selected', 'true');
      document.getElementById(tabName).classList.add('active');
    });
  });
}

// ============================================================================
// GESTION STEPPER COUVERTS
// ============================================================================

function initStepper() {
  const minusBtn = document.querySelector('.stepper-minus');
  const plusBtn = document.querySelector('.stepper-plus');
  const input = document.getElementById('res-couverts');

  if (!minusBtn || !plusBtn || !input) return;

  minusBtn.addEventListener('click', (e) => {
    e.preventDefault();
    let value = parseInt(input.value, 10) || 2;
    if (value > 1) {
      input.value = value - 1;
    }
  });

  plusBtn.addEventListener('click', (e) => {
    e.preventDefault();
    let value = parseInt(input.value, 10) || 2;
    if (value < 12) {
      input.value = value + 1;
    }
  });
}

// ============================================================================
// GESTION DATE MINIMALE
// ============================================================================

function initMinDate() {
  const dateInput = document.getElementById('res-date');
  if (dateInput) {
    dateInput.setAttribute('min', offsetDate(0));
  }
}

// ============================================================================
// COMPTEUR CARACTÈRES MESSAGE
// ============================================================================

function initCharCounter() {
  const textarea = document.getElementById('res-message');
  const counter = document.getElementById('char-count');

  if (textarea && counter) {
    textarea.addEventListener('input', () => {
      counter.textContent = `${textarea.value.length}/300`;
    });
  }
}

// ============================================================================
// GESTION SÉLECTION SERVICE
// ============================================================================

function initServiceSelection() {
  const serviceCards = document.querySelectorAll('.service-card');

  serviceCards.forEach(card => {
    card.addEventListener('click', () => {
      serviceCards.forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      card.querySelector('input[type="radio"]').checked = true;
    });
  });
}

// ============================================================================
// GESTION FORMULAIRE RÉSERVATION
// ============================================================================

function initReservationForm() {
  const form = document.getElementById('reservation-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    // Récupérer les données
    const prenom = document.getElementById('res-prenom').value.trim();
    const telephone = document.getElementById('res-telephone').value.trim();
    const date = document.getElementById('res-date').value;
    const service = document.querySelector('input[name="service"]:checked').value;
    const couverts = document.getElementById('res-couverts').value;
    const message = document.getElementById('res-message').value.trim();

    // Validation basique
    if (!prenom || !telephone || !date || !service || !couverts) {
      showFeedback('reservation-feedback', 'Veuillez remplir tous les champs obligatoires.', 'error');
      return;
    }

    // Créer l'objet réservation
    const reservation = {
      id: Date.now().toString(),
      prenom,
      telephone,
      date,
      service,
      couverts,
      message,
      statut: "En attente",
      source: "client"
    };

    // Récupérer les réservations existantes
    const existing = safeParse(localStorage.getItem("actions_recues"), []);
    existing.push(reservation);

    // Sauvegarder
    localStorage.setItem("actions_recues", JSON.stringify(existing));

    // Message de confirmation
    showFeedback('reservation-feedback', '✓ Votre réservation a été enregistrée ! Notre équipe vous contactera pour confirmation.', 'success', 5000);

    // Réinitialiser le formulaire
    form.reset();
    document.getElementById('res-couverts').value = '2';
    document.getElementById('char-count').textContent = '0/300';

    // Scroll top
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 500);
  });
}

// ============================================================================
// GESTION ARDOISE DU JOUR
// ============================================================================

function initArdoise() {
  const contenuEditable = safeParse(localStorage.getItem("contenu_editable"), {
    suggestion_du_jour: {
      plat: "Filet de bœuf, sauce au poivre",
      prix: "22,00 €",
      note: "Cuisson selon votre goût"
    }
  });

  // Récupérer les données de l'ardoise complète depuis admin ou utiliser les démos
  const ardoiseData = safeParse(localStorage.getItem("ardoise_data"), DEMO_ARDOISE);

  const ardoiseContent = document.getElementById('ardoise-content');
  if (!ardoiseContent) return;

  // Si l'ardoise n'est pas disponible, masquer la section
  if (!ardoiseData.disponible) {
    ardoiseContent.parentElement.style.display = 'none';
    return;
  }

  // Afficher le plat du jour
  if (ardoiseData.plat) {
    document.getElementById('ardoise-plat-nom').textContent = ardoiseData.plat.nom || '';
    document.getElementById('ardoise-plat-prix').textContent = ardoiseData.plat.prix || '';
    if (ardoiseData.plat.note) {
      document.getElementById('ardoise-plat-note').textContent = ardoiseData.plat.note;
    }
  }

  // Afficher l'entrée si présente
  if (ardoiseData.entree && ardoiseData.entree.nom) {
    const wrap = document.getElementById('ardoise-entree-wrap');
    wrap.style.display = 'block';
    document.getElementById('ardoise-entree-nom').textContent = ardoiseData.entree.nom;
    document.getElementById('ardoise-entree-prix').textContent = ardoiseData.entree.prix;
  }

  // Afficher le dessert si présent
  if (ardoiseData.dessert && ardoiseData.dessert.nom) {
    const wrap = document.getElementById('ardoise-dessert-wrap');
    wrap.style.display = 'block';
    document.getElementById('ardoise-dessert-nom').textContent = ardoiseData.dessert.nom;
    document.getElementById('ardoise-dessert-prix').textContent = ardoiseData.dessert.prix;
  }

  // Afficher la formule si active
  if (ardoiseData.formule && ardoiseData.formule.active) {
    const wrap = document.getElementById('ardoise-formule-wrap');
    wrap.style.display = 'block';
    document.getElementById('ardoise-formule-label').textContent = ardoiseData.formule.label || 'Entrée + Plat + Dessert';
    document.getElementById('ardoise-formule-prix').textContent = ardoiseData.formule.prix;
  }
}

// ============================================================================
// GESTION SMOOTH SCROLL
// ============================================================================

function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href === '#' || href === '#top') return;

      const target = document.querySelector(href);
      if (!target) return;

      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

// ============================================================================
// INITIALISATION GLOBALE
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  ensureInitialData();
  initMenuTabs();
  initStepper();
  initMinDate();
  initCharCounter();
  initServiceSelection();
  initReservationForm();
  initArdoise();
  initSmoothScroll();
});

// ============================================================================
// FIN script.js
// ============================================================================