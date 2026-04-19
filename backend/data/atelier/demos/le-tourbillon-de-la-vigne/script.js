// ==================== UTILITY FUNCTIONS ====================

function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try {
    return JSON.parse(rawValue);
  } catch (e) {
    return fallbackValue;
  }
}

function offsetDate(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

function getDateRelative(dateStr) {
  const date = new Date(dateStr + 'T00:00:00');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffTime = today - date;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'aujourd\'hui';
  if (diffDays === 1) return 'hier';
  if (diffDays > 1 && diffDays < 7) return `il y a ${diffDays} jours`;
  if (diffDays >= 7 && diffDays < 30) return `il y a ${Math.floor(diffDays / 7)} semaines`;
  if (diffDays >= 30) return `il y a ${Math.floor(diffDays / 30)} mois`;
  if (diffDays < 0 && diffDays > -7) return `dans ${Math.abs(diffDays)} jours`;
  return dateStr;
}

// ==================== DEFAULT DATA ====================

const DEFAULT_MENU = {
  categories: [
    {
      id: 'cat-1',
      nom: 'Entrées',
      ordre: 1,
      plats: [
        {
          id: 'plat-1',
          nom: 'Salade lyonnaise',
          prix: '12,00 €',
          description: 'Frisée, lardons, œuf poché',
          disponible: true
        },
        {
          id: 'plat-2',
          nom: 'Pâté en croûte maison',
          prix: '11,00 €',
          description: 'Servi avec pain grillé',
          disponible: true
        },
        {
          id: 'plat-3',
          nom: 'Terrine de foie gras',
          prix: '14,00 €',
          description: 'Chutney de figues, brioche toastée',
          disponible: true
        }
      ]
    },
    {
      id: 'cat-2',
      nom: 'Plats',
      ordre: 2,
      plats: [
        {
          id: 'plat-4',
          nom: 'Quenelle de brochet',
          prix: '18,00 €',
          description: 'Sauce Nantua maison',
          disponible: true
        },
        {
          id: 'plat-5',
          nom: 'Saucisson chaud en brioche',
          prix: '16,00 €',
          description: 'Avec sauce madère',
          disponible: true
        },
        {
          id: 'plat-6',
          nom: 'Andouillette de qualité',
          prix: '15,00 €',
          description: 'Moutarde à l\'ancienne',
          disponible: true
        },
        {
          id: 'plat-7',
          nom: 'Côte de veau rôtie',
          prix: '24,00 €',
          description: 'Jus naturel, légumes de saison',
          disponible: true
        }
      ]
    },
    {
      id: 'cat-3',
      nom: 'Desserts',
      ordre: 3,
      plats: [
        {
          id: 'plat-8',
          nom: 'Tarte Tatin',
          prix: '7,00 €',
          description: 'Maison, crème fraîche',
          disponible: true
        },
        {
          id: 'plat-9',
          nom: 'Fondant au chocolat',
          prix: '7,50 €',
          description: 'Glace vanille',
          disponible: true
        },
        {
          id: 'plat-10',
          nom: 'Gratin de fruits rouges',
          prix: '8,00 €',
          description: 'Sabayon chaud',
          disponible: true
        }
      ]
    }
  ]
};

const DEFAULT_ARDOISE = {
  disponible: true,
  entree: { nom: 'Velouté de butternut', prix: '8,00 €' },
  plat: { nom: 'Quenelle de brochet', prix: '18,00 €', note: 'Sauce Nantua maison' },
  dessert: { nom: 'Tarte Tatin', prix: '7,00 €' },
  formule: { active: true, prix: '32,00 €', label: 'Entrée + Plat + Dessert' }
};

const DEFAULT_AVIS = [
  {
    id: 'avis-demo-1',
    prenom: 'Claire M.',
    note: 5,
    texte: 'Une adresse que l\'on garde précieusement. Accueil chaleureux, carte courte mais parfaitement maîtrisée. On reviendra sans hésiter.',
    date: offsetDate(-5),
    statut: 'visible',
    source: 'demo'
  },
  {
    id: 'avis-demo-2',
    prenom: 'Pierre D.',
    note: 5,
    texte: 'Excellente découverte ! Les vins sont bien choisis et les accords mets-vins parfaitement pensés. Le service est aux petits soins.',
    date: offsetDate(-12),
    statut: 'visible',
    source: 'demo'
  },
  {
    id: 'avis-demo-3',
    prenom: 'Sophie T.',
    note: 4,
    texte: 'Très bonne soirée en amoureux. Cadre intime, cuisine soignée. Peut-être un peu bruyant le samedi soir, mais rien de rédhibitoire.',
    date: offsetDate(-18),
    statut: 'visible',
    source: 'demo'
  },
  {
    id: 'avis-demo-4',
    prenom: 'Isabelle R.',
    note: 5,
    texte: 'J\'ai organisé un repas d\'anniversaire pour 8 personnes. L\'équipe a été aux petits soins du début à la fin. Merci !',
    date: offsetDate(-25),
    statut: 'visible',
    source: 'demo'
  },
  {
    id: 'avis-demo-5',
    prenom: 'Thomas B.',
    note: 4,
    texte: 'Bon rapport qualité-prix pour le quartier. La cuisine lyonnaise est une vraie spécialité ici. À recommander !',
    date: offsetDate(-30),
    statut: 'visible',
    source: 'demo'
  }
];

// ==================== INITIALIZATION ====================

function ensureInitialData() {
  // Ensure menuCard exists
  const existingMenu = localStorage.getItem('menuCard');
  if (!existingMenu) {
    localStorage.setItem('menuCard', JSON.stringify(DEFAULT_MENU));
  }

  // Ensure ardoise exists
  const existingArdoise = localStorage.getItem('contenu_editable');
  if (!existingArdoise) {
    localStorage.setItem('contenu_editable', JSON.stringify({ ardoise: DEFAULT_ARDOISE }));
  }

  // Ensure avis exists
  const existingAvis = localStorage.getItem('avis_clients');
  if (!existingAvis) {
    localStorage.setItem('avis_clients', JSON.stringify(DEFAULT_AVIS));
  }
}

// ==================== MENU RENDERING ====================

function renderMenu() {
  const menuData = safeParse(localStorage.getItem('menuCard'), DEFAULT_MENU);
  const tabsContainer = document.getElementById('menuTabs');
  const contentContainer = document.getElementById('menuContent');

  if (!tabsContainer || !contentContainer) return;

  tabsContainer.innerHTML = '';
  contentContainer.innerHTML = '';

  menuData.categories.forEach((cat, index) => {
    // Create tab button
    const tabBtn = document.createElement('button');
    tabBtn.className = `menu-category-btn ${index === 0 ? 'active' : ''}`;
    tabBtn.textContent = cat.nom;
    tabBtn.style.cssText = `
      padding: 1rem 1.5rem;
      background-color: transparent;
      border: none;
      border-bottom: 3px solid transparent;
      cursor: pointer;
      font-size: 0.95rem;
      font-weight: 500;
      color: var(--text-secondary);
      transition: all 0.3s ease;
    `;
    tabBtn.onclick = () => selectMenuCategory(cat.id, document.querySelectorAll('.menu-category-btn'));

    if (index === 0) {
      tabBtn.style.color = 'var(--accent)';
      tabBtn.style.borderBottomColor = 'var(--accent)';
    }

    tabsContainer.appendChild(tabBtn);

    // Create content section
    const section = document.createElement('div');
    section.className = `menu-category-content ${index === 0 ? 'active' : ''}`;
    section.id = `menu-${cat.id}`;
    section.style.display = index === 0 ? 'block' : 'none';

    section.innerHTML = `
      <div class="menu-section">
        <div class="menu-category">
          <div class="menu-items">
            ${cat.plats.map(plat => `
              <div class="menu-item" style="opacity: ${plat.disponible ? '1' : '0.5'}; ${plat.disponible ? '' : 'text-decoration: line-through;'}">
                <div class="menu-item-header">
                  <span class="menu-item-name">${plat.nom}</span>
                  <span class="menu-item-price">${plat.prix}</span>
                </div>
                ${plat.description ? `<p class="menu-item-description">${plat.description}</p>` : ''}
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;

    contentContainer.appendChild(section);
  });
}

function selectMenuCategory(categoryId, buttons) {
  buttons.forEach(btn => {
    btn.style.color = 'var(--text-secondary)';
    btn.style.borderBottomColor = 'transparent';
  });

  const clickedBtn = event.target;
  clickedBtn.style.color = 'var(--accent)';
  clickedBtn.style.borderBottomColor = 'var(--accent)';

  document.querySelectorAll('.menu-category-content').forEach(content => {
    content.style.display = 'none';
  });

  const targetContent = document.getElementById(`menu-${categoryId}`);
  if (targetContent) {
    targetContent.style.display = 'block';
  }
}

// ==================== ARDOISE RENDERING ====================

function renderArdoise() {
  const editableData = safeParse(localStorage.getItem('contenu_editable'), { ardoise: DEFAULT_ARDOISE });
  const ardoiseData = editableData.ardoise || DEFAULT_ARDOISE;
  const ardoiseSection = document.getElementById('ardoise-section');
  const ardoiseContent = document.getElementById('ardoiseContent');

  if (!ardoiseData.disponible) {
    ardoiseSection.style.display = 'none';
    return;
  }

  ardoiseSection.style.display = 'block';
  ardoiseContent.innerHTML = '';

  if (ardoiseData.entree) {
    ardoiseContent.innerHTML += `
      <div class="ardoise-item">
        <div class="ardoise-item-content">
          <h4>${ardoiseData.entree.nom}</h4>
        </div>
        <div class="ardoise-item-price">${ardoiseData.entree.prix}</div>
      </div>
    `;
  }

  if (ardoiseData.plat) {
    ardoiseContent.innerHTML += `
      <div class="ardoise-item" style="border: 2px solid var(--accent); background-color: rgba(139, 38, 53, 0.05);">
        <div class="ardoise-item-content">
          <h4 style="color: var(--accent); font-weight: 700;">${ardoiseData.plat.nom}</h4>
          ${ardoiseData.plat.note ? `<p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.3rem;">${ardoiseData.plat.note}</p>` : ''}
        </div>
        <div class="ardoise-item-price">${ardoiseData.plat.prix}</div>
      </div>
    `;
  }

  if (ardoiseData.dessert) {
    ardoiseContent.innerHTML += `
      <div class="ardoise-item">
        <div class="ardoise-item-content">
          <h4>${ardoiseData.dessert.nom}</h4>
        </div>
        <div class="ardoise-item-price">${ardoiseData.dessert.prix}</div>
      </div>
    `;
  }

  if (ardoiseData.formule && ardoiseData.formule.active) {
    ardoiseContent.innerHTML += `
      <div class="ardoise-item" style="background-color: rgba(139, 38, 53, 0.1); border: 2px dashed var(--accent);">
        <div class="ardoise-item-content">
          <h4 style="color: var(--accent);">🎁 Formule ${ardoiseData.formule.label}</h4>
        </div>
        <div class="ardoise-item-price" style="font-size: 1.2rem;">${ardoiseData.formule.prix}</div>
      </div>
    `;
  }
}

// ==================== AVIS RENDERING ====================

function renderAvis() {
  const avisData = safeParse(localStorage.getItem('avis_clients'), DEFAULT_AVIS);
  const visibleAvis = avisData.filter(a => a.statut === 'visible');
  const reviewsCarousel = document.getElementById('reviewsCarousel');
  const avisSection = document.getElementById('avis-section');

  if (!avisSection) return;

  if (visibleAvis.length === 0) {
    avisSection.style.display = 'none';
    return;
  }

  avisSection.style.display = 'block';

  if (reviewsCarousel) {
    reviewsCarousel.innerHTML = '';
    visibleAvis.forEach(avis => {
      const card = document.createElement('div');
      card.style.cssText = `
        background-color: var(--card-bg);
        border: 1px solid var(--border-soft);
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      `;
      card.innerHTML = `
        <div style="color: var(--accent); font-size: 1.2rem; margin-bottom: 0.5rem;">
          ${'★'.repeat(avis.note)}${'☆'.repeat(5 - avis.note)}
        </div>
        <p style="color: var(--text-secondary); font-style: italic; margin-bottom: 1rem; line-height: 1.6;">"${avis.texte}"</p>
        <p style="font-size: 0.9rem; color: var(--text-secondary);">
          <strong>${avis.prenom}</strong> · ${getDateRelative(avis.date)}
        </p>
      `;
      reviewsCarousel.appendChild(card);
    });
  }
}

// ==================== FORM HANDLING ====================

function initReservationForm() {
  const form = document.getElementById('reservationForm');
  const minDate = new Date();
  const dateInput = document.getElementById('date');
  const couvertsMinus = document.getElementById('couverts-minus');
  const couvertsPlus = document.getElementById('couverts-plus');
  const couvertsInput = document.getElementById('couverts');
  const serviceCards = document.querySelectorAll('.service-card');

  // Set minimum date
  if (dateInput) {
    dateInput.min = minDate.toISOString().split('T')[0];
  }

  // Service card selection
  serviceCards.forEach(card => {
    card.addEventListener('click', () => {
      serviceCards.forEach(c => {
        c.style.borderColor = 'var(--border-soft)';
        c.style.backgroundColor = 'transparent';
      });
      card.style.borderColor = 'var(--accent)';
      card.style.backgroundColor = 'rgba(139, 38, 53, 0.05)';
      const radio = card.querySelector('input[type="radio"]');
      radio.checked = true;
    });
  });

  // Stepper couverts
  if (couvertsMinus) {
    couvertsMinus.addEventListener('click', (e) => {
      e.preventDefault();
      const current = parseInt(couvertsInput.value);
      if (current > 1) {
        couvertsInput.value = current - 1;
      }
    });
  }

  if (couvertsPlus) {
    couvertsPlus.addEventListener('click', (e) => {
      e.preventDefault();
      const current = parseInt(couvertsInput.value);
      if (current < 12) {
        couvertsInput.value = current + 1;
      }
    });
  }

  // Form submission
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();

      const reservation = {
        id: Date.now().toString(),
        prenom: document.getElementById('prenom').value,
        telephone: document.getElementById('telephone').value,
        date: document.getElementById('date').value,
        service: document.getElementById('service-dejeuner').checked ? 'dejeuner' : 'diner',
        couverts: document.getElementById('couverts').value,
        message: document.getElementById('message').value,
        statut: 'En attente',
        source: 'web'
      };

      const existingReservations = safeParse(localStorage.getItem('actions_recues'), []);
      existingReservations.push(reservation);
      localStorage.setItem('actions_recues', JSON.stringify(existingReservations));

      form.reset();
      serviceCards.forEach(c => {
        c.style.borderColor = 'var(--border-soft)';
        c.style.backgroundColor = 'transparent';
      });
      couvertsInput.value = '2';

      showConfirmation('✓ Réservation enregistrée ! Nous vous recontacterons rapidement.');
    });
  }
}

function initReviewForm() {
  const ratingStars = document.querySelectorAll('#ratingStars span');
  const selectedRatingInput = document.getElementById('selectedRating');
  const reviewConsent = document.getElementById('reviewConsent');
  const publishBtn = document.getElementById('publishReviewBtn');
  const reviewForm = document.getElementById('reviewSubmitForm');
  const reviewConfirmation = document.getElementById('reviewConfirmation');

  ratingStars.forEach(star => {
    star.addEventListener('click', () => {
      const rating = star.getAttribute('data-rating');
      selectedRatingInput.value = rating;
      ratingStars.forEach(s => {
        const sRating = s.getAttribute('data-rating');
        s.style.color = sRating <= rating ? 'var(--accent)' : '#ccc';
      });
    });

    star.addEventListener('mouseover', () => {
      const hoverRating = star.getAttribute('data-rating');
      ratingStars.forEach(s => {
        const sRating = s.getAttribute('data-rating');
        s.style.opacity = sRating <= hoverRating ? '1' : '0.3';
      });
    });
  });

  document.getElementById('ratingStars').addEventListener('mouseleave', () => {
    const currentRating = selectedRatingInput.value;
    ratingStars.forEach(s => {
      s.style.opacity = '1';
    });
  });

  reviewConsent.addEventListener('change', () => {
    publishBtn.disabled = !reviewConsent.checked || selectedRatingInput.value === '0';
  });

  if (reviewForm) {
    reviewForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const review = {
        id: `review-${Date.now()}`,
        prenom: 'Visiteur',
        note: parseInt(selectedRatingInput.value),
        texte: document.getElementById('reviewText').value,
        date: new Date().toISOString().split('T')[0],
        statut: 'en_attente',
        source: 'web'
      };

      const existingReviews = safeParse(localStorage.getItem('avis_clients'), DEFAULT_AVIS);
      existingReviews.push(review);
      localStorage.setItem('avis_clients', JSON.stringify(existingReviews));

      reviewForm.style.display = 'none';
      reviewConfirmation.style.display = 'block';

      setTimeout(() => {
        reviewForm.style.display = 'flex';
        reviewConfirmation.style.display = 'none';
        reviewForm.reset();
        selectedRatingInput.value = '0';
        publishBtn.disabled = true;
        ratingStars.forEach(s => s.style.color = '#ccc');
        reviewConsent.checked = false;
      }, 4000);
    });
  }
}

function showConfirmation(message) {
  const confirmationMessage = document.getElementById('confirmationMessage');
  if (confirmationMessage) {
    confirmationMessage.textContent = message;
    confirmationMessage.classList.add('show');
    setTimeout(() => {
      confirmationMessage.classList.remove('show');
    }, 4000);
  }
}

// ==================== DOM READY ====================

document.addEventListener('DOMContentLoaded', () => {
  ensureInitialData();
  renderMenu();
  renderArdoise();
  renderAvis();
  initReservationForm();
  initReviewForm();

  // Add container width constraint to CSS dynamically
  const style = document.createElement('style');
  style.textContent = `
    .container {
      max-width: 1400px;
      margin: 0 auto;
    }
  `;
  document.head.appendChild(style);
});

// Listen for changes from admin panel
window.addEventListener('storage', () => {
  renderMenu();
  renderArdoise();
  renderAvis();
});
```