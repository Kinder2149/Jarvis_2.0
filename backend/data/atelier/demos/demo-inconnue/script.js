// ========== UTILITIES ==========

function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try {
    return JSON.parse(rawValue);
  } catch (e) {
    return fallbackValue;
  }
}

function offsetDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

// ========== INITIAL DATA ==========

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

const DEFAULT_MENU = {
  categories: [
    {
      id: "cat-1",
      nom: "Entrées",
      ordre: 1,
      plats: [
        {
          id: "plat-1",
          nom: "Salade samossa chèvre, pommes, noix, miel",
          prix: "8,00 €",
          description: "",
          disponible: true
        },
        {
          id: "plat-2",
          nom: "Pâté de campagne au camembert",
          prix: "8,50 €",
          description: "",
          disponible: true
        },
        {
          id: "plat-3",
          nom: "Terrine de légumes, coulis de tomates",
          prix: "8,00 €",
          description: "",
          disponible: true
        }
      ]
    },
    {
      id: "cat-2",
      nom: "Plats",
      ordre: 2,
      plats: [
        {
          id: "plat-4",
          nom: "Onglet de veau croûte aux herbes",
          prix: "18,00 €",
          description: "gnocchi à la romaine, légumes",
          disponible: true
        },
        {
          id: "plat-5",
          nom: "Risotto au pesto vert, burratina, roquette",
          prix: "16,00 €",
          description: "",
          disponible: true
        },
        {
          id: "plat-6",
          nom: "Filet de poisson beurre thym citron, écrasé patates douces",
          prix: "18,00 €",
          description: "",
          disponible: true
        },
        {
          id: "plat-7",
          nom: "Gratin de Ravioles du Royans, tomme de Savoie, tomates confites",
          prix: "16,00 €",
          description: "",
          disponible: true
        }
      ]
    },
    {
      id: "cat-3",
      nom: "Desserts",
      ordre: 3,
      plats: [
        {
          id: "plat-8",
          nom: "Moelleux aux amandes, caramel beurre demi-sel, chantilly",
          prix: "7,00 €",
          description: "",
          disponible: true
        },
        {
          id: "plat-9",
          nom: "Coulant au chocolat",
          prix: "7,50 €",
          description: "coeur spéculos, glace vanille",
          disponible: true
        },
        {
          id: "plat-10",
          nom: "Crème brûlée",
          prix: "7,00 €",
          description: "parfum selon l'humeur du chef",
          disponible: true
        },
        {
          id: "plat-11",
          nom: "Salade de fruits frais",
          prix: "6,50 €",
          description: "",
          disponible: true
        },
        {
          id: "plat-12",
          nom: "Café gourmand",
          prix: "8,00 €",
          description: "Thé : supplément 0,50€",
          disponible: true
        },
        {
          id: "plat-13",
          nom: "Vacherin glacé",
          prix: "7,00 €",
          description: "",
          disponible: true
        },
        {
          id: "plat-14",
          nom: "Fromage blanc, crème ou coulis de fruits maison",
          prix: "5,50 €",
          description: "",
          disponible: true
        }
      ]
    },
    {
      id: "cat-4",
      nom: "Fromage et Glaces",
      ordre: 4,
      plats: [
        {
          id: "plat-15",
          nom: "1/2 St. Marcelin",
          prix: "6,50 €",
          description: "",
          disponible: true
        },
        {
          id: "plat-16",
          nom: "Café Liégeois",
          prix: "7,90 €",
          description: "",
          disponible: true
        },
        {
          id: "plat-17",
          nom: "Glace chocolat, caramel",
          prix: "7,90 €",
          description: "caramel beurre demi-sel, chantilly",
          disponible: true
        },
        {
          id: "plat-18",
          nom: "Glace fruit de la passion, citron",
          prix: "7,90 €",
          description: "meringue, coulis de fruits, chantilly",
          disponible: true
        }
      ]
    },
    {
      id: "cat-5",
      nom: "Les maxi",
      ordre: 5,
      plats: [
        {
          id: "plat-19",
          nom: "Hamburger du moment",
          prix: "18,00 €",
          description: "pain aux graines maison, steak haché de boeuf (150g, FR), pommes de terres grenailles, salade",
          disponible: true
        },
        {
          id: "plat-20",
          nom: "Tartare de boeuf (180g, FR)",
          prix: "19,00 €",
          description: "pommes de terres grenailles, salade",
          disponible: true
        },
        {
          id: "plat-21",
          nom: "Salade samossa chèvre, pommes, noix, miel",
          prix: "15,50 €",
          description: "",
          disponible: true
        },
        {
          id: "plat-22",
          nom: "Salade Lyonnaise",
          prix: "14,00 €",
          description: "lardons, croutons, oeuf poché",
          disponible: true
        }
      ]
    },
    {
      id: "cat-6",
      nom: "Menu Enfant",
      ordre: 6,
      plats: [
        {
          id: "plat-23",
          nom: "Menu Enfant (10 ans)",
          prix: "13,50 €",
          description: "Filet de poisson ou Steak haché (France) - Pommes de terre ou Gratin de ravioles - Sirop et Glace",
          disponible: true
        }
      ]
    }
  ]
};

const DEFAULT_ARDOISE = {
  disponible: true,
  entree: {
    nom: "Velouté de butternut, crème fraîche",
    prix: "8,00 €"
  },
  plat: {
    nom: "Magret de canard, jus de cerise",
    prix: "21,00 €",
    note: "Cuisson selon votre goût"
  },
  dessert: {
    nom: "Fondant au chocolat, glace vanille",
    prix: "7,00 €"
  },
  formule: {
    active: true,
    prix: "31,00 €",
    label: "Entrée + Plat + Dessert"
  }
};

// ========== INITIALIZATION ==========

function ensureInitialData() {
  const existing = localStorage.getItem("actions_recues");
  if (!existing) {
    localStorage.setItem("actions_recues", JSON.stringify(DEMO_RESERVATIONS));
  }

  const existingMenu = localStorage.getItem("menuCard");
  if (!existingMenu) {
    localStorage.setItem("menuCard", JSON.stringify(DEFAULT_MENU));
  }

  const existingArdoise = localStorage.getItem("contenu_editable");
  if (!existingArdoise) {
    localStorage.setItem("contenu_editable", JSON.stringify({
      ardoise: DEFAULT_ARDOISE,
      suggestion_du_jour: {
        plat: "Magret de canard, jus de cerise",
        prix: "21,00 €",
        note: "Cuisson selon votre goût"
      }
    }));
  }
}

// ========== MENU RENDERING ==========

function renderMenu() {
  const menuData = safeParse(localStorage.getItem("menuCard"), DEFAULT_MENU);
  const menuItemsContainer = document.getElementById("menuItems");
  
  if (!menuItemsContainer) return;

  // Clear previous items
  menuItemsContainer.innerHTML = "";

  // Get first category by default
  const firstCategory = menuData.categories[0];
  if (!firstCategory) return;

  renderMenuItems(firstCategory.plats);
}

function renderMenuItems(plats) {
  const menuItemsContainer = document.getElementById("menuItems");
  menuItemsContainer.innerHTML = "";

  plats.forEach(plat => {
    const menuItem = document.createElement("div");
    menuItem.className = "menu-item";
    if (!plat.disponible) {
      menuItem.style.opacity = "0.6";
      menuItem.style.textDecoration = "line-through";
    }

    let html = `<h4 style="${!plat.disponible ? 'text-decoration: line-through;' : ''}">${plat.nom}</h4>`;
    html += `<div class="price">${plat.prix}</div>`;
    if (plat.description) {
      html += `<div class="description">${plat.description}</div>`;
    }

    menuItem.innerHTML = html;
    menuItemsContainer.appendChild(menuItem);
  });
}

// ========== MENU CATEGORY TABS ==========

function initMenuTabs() {
  const menuData = safeParse(localStorage.getItem("menuCard"), DEFAULT_MENU);
  const tabs = document.querySelectorAll(".menu-category-btn");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      // Remove active class from all tabs
      tabs.forEach(t => t.classList.remove("active"));
      
      // Add active class to clicked tab
      tab.classList.add("active");

      // Get category index and render items
      const categoryIndex = parseInt(tab.getAttribute("data-category"));
      const category = menuData.categories[categoryIndex];
      if (category) {
        renderMenuItems(category.plats);
      }
    });
  });
}

// ========== ARDOISE RENDERING ==========

function renderArdoise() {
  const contentData = safeParse(localStorage.getItem("contenu_editable"), {
    ardoise: DEFAULT_ARDOISE
  });

  const ardoise = contentData.ardoise || DEFAULT_ARDOISE;
  const ardoiseSection = document.getElementById("ardoise-section");

  if (!ardoiseSection) return;

  // Show/hide ardoise section based on availability
  if (ardoise.disponible) {
    ardoiseSection.style.display = "block";
  } else {
    ardoiseSection.style.display = "none";
    return;
  }

  // Entrée
  if (ardoise.entree && ardoise.entree.nom) {
    document.getElementById("ardoise-entree").style.display = "block";
    document.getElementById("ardoise-entree-nom").textContent = ardoise.entree.nom;
    document.getElementById("ardoise-entree-prix").textContent = ardoise.entree.prix;
  } else {
    document.getElementById("ardoise-entree").style.display = "none";
  }

  // Plat (obligatoire)
  if (ardoise.plat && ardoise.plat.nom) {
    document.getElementById("ardoise-plat-nom").textContent = ardoise.plat.nom;
    document.getElementById("ardoise-plat-prix").textContent = ardoise.plat.prix;
    
    const noteEl = document.getElementById("ardoise-plat-note");
    if (ardoise.plat.note) {
      noteEl.textContent = ardoise.plat.note;
      noteEl.style.display = "block";
    } else {
      noteEl.style.display = "none";
    }
  }

  // Dessert
  if (ardoise.dessert && ardoise.dessert.nom) {
    document.getElementById("ardoise-dessert").style.display = "block";
    document.getElementById("ardoise-dessert-nom").textContent = ardoise.dessert.nom;
    document.getElementById("ardoise-dessert-prix").textContent = ardoise.dessert.prix;
  } else {
    document.getElementById("ardoise-dessert").style.display = "none";
  }

  // Formule
  if (ardoise.formule && ardoise.formule.active) {
    document.getElementById("ardoise-formule").style.display = "block";
    document.getElementById("ardoise-formule-label").textContent = ardoise.formule.label;
    document.getElementById("ardoise-formule-prix").textContent = ardoise.formule.prix;
  } else {
    document.getElementById("ardoise-formule").style.display = "none";
  }
}

// ========== RESERVATION FORM ==========

function initReservationForm() {
  const form = document.getElementById("reservationForm");
  if (!form) return;

  // Set min date to today
  const dateInput = document.getElementById("date");
  const today = new Date().toISOString().split('T')[0];
  dateInput.setAttribute("min", today);

  // Service card selection
  const serviceCards = document.querySelectorAll(".service-card");
  serviceCards.forEach(card => {
    card.addEventListener("click", () => {
      serviceCards.forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      document.getElementById("service").value = card.getAttribute("data-service");
    });
  });

  // Stepper controls
  const couverts = document.getElementById("couverts");
  const minusBtn = document.getElementById("couverts-minus");
  const plusBtn = document.getElementById("couverts-plus");

  minusBtn.addEventListener("click", (e) => {
    e.preventDefault();
    if (parseInt(couverts.value) > 1) {
      couverts.value = parseInt(couverts.value) - 1;
    }
  });

  plusBtn.addEventListener("click", (e) => {
    e.preventDefault();
    if (parseInt(couverts.value) < 12) {
      couverts.value = parseInt(couverts.value) + 1;
    }
  });

  // Form submission
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const prenom = document.getElementById("prenom").value.trim();
    const telephone = document.getElementById("telephone").value.trim();
    const date = document.getElementById("date").value;
    const service = document.getElementById("service").value;
    const couverts = document.getElementById("couverts").value;
    const message = document.getElementById("message").value.trim();

    if (!prenom || !telephone || !date || !service) {
      return;
    }

    // Create reservation object
    const reservation = {
      id: Date.now(),
      prenom: prenom,
      telephone: telephone,
      date: date,
      service: service,
      couverts: couverts,
      message: message,
      statut: "En attente",
      source: "client"
    };

    // Get existing reservations
    let reservations = safeParse(localStorage.getItem("actions_recues"), []);
    
    // Add new reservation
    reservations.push(reservation);

    // Save to localStorage
    localStorage.setItem("actions_recues", JSON.stringify(reservations));

    // Show confirmation message
    showConfirmationMessage();

    // Reset form
    form.reset();
    serviceCards.forEach(c => c.classList.remove("selected"));
    document.getElementById("service").value = "";
    document.getElementById("couverts").value = "2";
  });
}

function showConfirmationMessage() {
  const confirmationDiv = document.getElementById("confirmationMessage");
  if (!confirmationDiv) return;

  confirmationDiv.style.display = "block";
  confirmationDiv.classList.remove("hidden");

  setTimeout(() => {
    confirmationDiv.style.display = "none";
    confirmationDiv.classList.add("hidden");
  }, 4000);
}

// ========== DOCUMENT READY ==========

document.addEventListener("DOMContentLoaded", () => {
  ensureInitialData();
  renderMenu();
  initMenuTabs();
  renderArdoise();
  initReservationForm();

  // Listen for storage changes (when admin updates content)
  window.addEventListener("storage", () => {
    renderMenu();
    renderArdoise();
  });
});
>>>