# ADMIN_TEMPLATE_RESTAURATION — L'ATELIER CONNECTÉ
> **RÉFÉRENCE CLAUDE** — Utilisé comme référence lors de la génération du PROMPT_CASCADE. Ne pas copier dans le dossier client.
> Template générique pour la page admin d'un restaurant.
> Outils obligatoires : Réservations · Menu & Ardoise
> Outils optionnels : Événements · Avis · Emporter (activer selon PROMPT_CASCADE)
> Variables à remplacer : `{{VARIABLE}}` — voir section VARIABLES en bas.
> Sections optionnelles marquées : <!-- OPTIONNEL: [NOM_OUTIL] -->

---

## VARIABLES DE PERSONNALISATION

```
— Obligatoires —
{{NOM_ETABLISSEMENT}}       ex: "Le Tourbillon de la Vigne"
{{NOM_GERANT}}              ex: "Pierre"
{{MOT_DE_PASSE}}            Obsolète — mot de passe codé en dur : "admin2024"
{{URL_LOGO}}                ex: "https://..." ou "assets/logo.jpg"
{{EQUIPE}}                  ex: "Pierre & Virginie"
{{CAPACITE_DEJEUNER}}       ex: 15
{{CAPACITE_DINER}}          ex: 20
{{MENU_CATEGORIES}}         JSON des catégories réelles (extrait Phase 2)
{{ARDOISE_INITIALE}}        JSON ardoise démo par défaut

— EmailJS (si activé) —
{{EMAILJS_PUBLIC_KEY}}      ex: "AO-oBPw9GC0Lc9cQZ"
{{EMAILJS_SERVICE_ID}}      ex: "service_0vr7k2s"
{{EMAILJS_TPL_CLIENT}}      ex: "template_295vy3j"

— Outil Événements (si activé) —
{{EVENEMENTS_INITIAUX}}     JSON des 3 événements démo

— Outil Avis (si activé) —
{{AVIS_DEMO}}               JSON des 5 avis démo
{{URL_GOOGLE_MAPS}}         URL Google Maps du client

— Outil Emporter (si activé) —
{{ARTICLES_EMPORTER}}       JSON des articles disponibles
{{CRENEAUX_MIDI}}           ex: ["12:00","12:15","12:30","12:45","13:00"]
{{CRENEAUX_SOIR}}           ex: ["19:00","19:30","20:00"] (vide si pas de service soir)
```

---

## STRUCTURE HTML — admin.html

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Espace Gérant — {{NOM_ETABLISSEMENT}}</title>
  <link rel="icon" href="{{URL_LOGO}}">
  <link href="https://fonts.googleapis.com/css2?family=[FONTS]&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
  <!-- EmailJS — supprimer si non utilisé -->
  <script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>
  <script>(function(){ emailjs.init("{{EMAILJS_PUBLIC_KEY}}"); })();</script>
</head>
<body class="admin-page">

  <!-- ===================== ÉCRAN LOGIN ===================== -->
  <section id="login-screen" class="login-screen">
    <img class="login-logo" src="{{URL_LOGO}}" alt="Logo {{NOM_ETABLISSEMENT}}">
    <h1>Espace Gérant — {{NOM_ETABLISSEMENT}}</h1>
    <div class="password-wrap">
      <input id="admin-password" type="password" placeholder="Mot de passe" aria-label="Mot de passe">
      <button id="toggle-password" type="button" class="btn-eye" aria-label="Afficher le mot de passe">👁</button>
    </div>
    <button id="login-btn" type="button" class="btn-main">Accéder à mon espace</button>
    <p id="login-error" class="error-message hidden" aria-live="polite">Mot de passe incorrect</p>
  </section>

  <!-- ===================== DASHBOARD ===================== -->
  <section id="dashboard" class="dashboard hidden">

    <header class="admin-header">
      <div class="admin-brand">
        <img src="{{URL_LOGO}}" alt="Logo {{NOM_ETABLISSEMENT}}">
        <div>
          <h2>Espace Gérant — {{NOM_ETABLISSEMENT}}</h2>
          <p id="currentDate" class="admin-date"></p>
        </div>
      </div>
      <div class="admin-header-right">
        <span class="today-badge" id="todayBadge">0 réservation aujourd'hui</span>
        <button id="logout-btn" type="button" class="btn-admin">Se déconnecter</button>
      </div>
    </header>

    <!-- KPI -->
    <div class="stats-bar">
      <article class="stat-card">
        <p class="stat-value" id="stat-today">0</p>
        <h3>Demandes aujourd'hui</h3>
      </article>
      <article class="stat-card">
        <p class="stat-value" id="stat-pending">0</p>
        <h3>En attente de confirmation</h3>
      </article>
      <article class="stat-card">
        <p class="stat-value" id="stat-week">0</p>
        <h3>Confirmées cette semaine</h3>
      </article>
    </div>

    <!-- ONGLETS — obligatoires toujours présents, optionnels selon PROMPT_CASCADE -->
    <nav class="admin-tabs">
      <button class="admin-tab active" data-tab="reservations">Réservations</button>
      <button class="admin-tab" data-tab="menu-ardoise">Menu & Ardoise</button>
      <!-- OPTIONNEL: ÉVÉNEMENTS — inclure si outil activé -->
      <!-- <button class="admin-tab" data-tab="evenements">Événements</button> -->
      <!-- OPTIONNEL: AVIS — inclure si outil activé -->
      <!-- <button class="admin-tab" data-tab="avis">Avis clients</button> -->
      <!-- OPTIONNEL: EMPORTER — inclure si outil activé -->
      <!-- <button class="admin-tab" data-tab="emporter">À emporter</button> -->
    </nav>

    <main class="admin-main">

      <!-- ===== ONGLET RÉSERVATIONS ===== -->
      <div id="tabReservations" class="tab-content active">

        <div class="section-header">
          <h2 class="section-title" id="sectionTitle">Réservations du jour</h2>
          <div class="filter-buttons">
            <button class="filter-btn active" data-filter="all">Toutes</button>
            <button class="filter-btn" data-filter="lunch">Déjeuner</button>
            <button class="filter-btn" data-filter="dinner">Dîner</button>
          </div>
        </div>

        <!-- Calendrier semaine -->
        <div class="calendar-section">
          <div class="calendar-grid" id="calendarGrid"></div>
        </div>

        <!-- Liste réservations -->
        <div id="reservations-list" class="reservations-list"></div>

        <button type="button" class="btn-secondary" id="deleteCancelledBtn">
          🗑️ Supprimer les réservations annulées
        </button>

        <!-- Capacités (sub-section dans l'onglet Réservations) -->
        <section class="admin-card admin-card--capacites">
          <h3>Capacités du service</h3>
          <div class="capacity-default">
            <div class="capacity-input-group">
              <label for="defaultLunch">Déjeuner (couverts max)</label>
              <input type="number" id="defaultLunch" min="0" value="{{CAPACITE_DEJEUNER}}">
            </div>
            <div class="capacity-input-group">
              <label for="defaultDinner">Dîner (couverts max)</label>
              <input type="number" id="defaultDinner" min="0" value="{{CAPACITE_DINER}}">
            </div>
          </div>
          <div class="capacity-add-form">
            <h4>Capacité spécifique par date</h4>
            <input type="date" id="specificDate">
            <input type="number" id="specificLunch" min="0" placeholder="Déjeuner">
            <input type="number" id="specificDinner" min="0" placeholder="Dîner">
            <button class="btn-secondary" id="addSpecificCapacityBtn">+ Ajouter</button>
          </div>
          <div id="specificCapacitiesList" class="specific-capacities-list"></div>
          <button class="btn-primary" id="saveCapacitiesBtn">💾 Sauvegarder les capacités</button>
          <p id="capacities-message" class="confirmation-message hidden">✓ Capacités mises à jour</p>
        </section>

        <a href="index.html" class="back-link">← Retour au site</a>
      </div>

      <!-- ===== ONGLET MENU & ARDOISE ===== -->
      <div id="tabMenuArdoise" class="tab-content">

        <!-- Sous-section 1 : Ardoise du jour (utilisée quotidiennement) -->
        <section class="admin-card">
          <div class="ardoise-header">
            <h3>Ardoise du jour</h3>
            <label class="toggle-label">
              <input type="checkbox" id="ardoise-disponible" checked>
              <span class="toggle-text">Disponible aujourd'hui</span>
            </label>
          </div>

          <div id="ardoise-form">
            <div class="form-row">
              <div class="form-group form-group--large">
                <label for="ardoise-plat">Plat du jour *</label>
                <input id="ardoise-plat" type="text" placeholder="Magret de canard, jus de cerise">
              </div>
              <div class="form-group form-group--small">
                <label for="ardoise-plat-prix">Prix</label>
                <input id="ardoise-plat-prix" type="text" placeholder="21,00 €">
              </div>
            </div>
            <div class="form-group">
              <label for="ardoise-note">Note (cuisson, accompagnement...)</label>
              <input id="ardoise-note" type="text" placeholder="Cuisson selon votre goût">
            </div>
            <div class="form-row">
              <div class="form-group form-group--large">
                <label for="ardoise-entree">Entrée du jour (optionnel)</label>
                <input id="ardoise-entree" type="text" placeholder="Velouté de butternut">
              </div>
              <div class="form-group form-group--small">
                <label for="ardoise-entree-prix">Prix</label>
                <input id="ardoise-entree-prix" type="text" placeholder="8,00 €">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group form-group--large">
                <label for="ardoise-dessert">Dessert du jour (optionnel)</label>
                <input id="ardoise-dessert" type="text" placeholder="Fondant au chocolat">
              </div>
              <div class="form-group form-group--small">
                <label for="ardoise-dessert-prix">Prix</label>
                <input id="ardoise-dessert-prix" type="text" placeholder="7,00 €">
              </div>
            </div>

            <div class="admin-card admin-card--inner">
              <label class="toggle-label">
                <input type="checkbox" id="formule-active">
                <span class="toggle-text">Proposer une formule</span>
              </label>
              <div id="formule-fields" class="hidden">
                <div class="form-row">
                  <div class="form-group form-group--large">
                    <label for="formule-label">Libellé de la formule</label>
                    <input id="formule-label" type="text" placeholder="Entrée + Plat + Dessert">
                  </div>
                  <div class="form-group form-group--small">
                    <label for="formule-prix">Prix formule</label>
                    <input id="formule-prix" type="text" placeholder="31,00 €">
                  </div>
                </div>
              </div>
            </div>

            <button id="save-ardoise" type="button" class="btn-main">Mettre à jour l'ardoise</button>
            <p id="ardoise-message" class="confirmation-message hidden">
              ✓ Ardoise mise à jour — visible sur le site au rechargement
            </p>
          </div>
        </section>

        <!-- Sous-section 2 : Carte des menus (modifications saisonnières) -->
        <section class="admin-card">
          <div class="section-header">
            <h3>Carte des menus</h3>
            <button class="btn-primary" id="saveMenuBtn">💾 Sauvegarder la carte</button>
          </div>
          <div id="menuEditor" class="menu-editor"></div>
          <button class="btn-secondary" id="addCategoryBtn">+ Ajouter une catégorie</button>
          <p id="menu-message" class="confirmation-message hidden">
            ✓ Carte sauvegardée — visible sur le site au rechargement
          </p>
        </section>

        <a href="index.html" class="back-link">← Retour au site</a>
      </div>

      <!-- ===== ONGLET ÉVÉNEMENTS (OPTIONNEL) ===== -->
      <!-- OPTIONNEL: ÉVÉNEMENTS — décommenter si outil activé -->
      <!--
      <div id="tabEvenements" class="tab-content">
        <div class="section-header">
          <h3>Événements & Privatisations</h3>
          <button class="btn-primary" id="addEvenementBtn">+ Nouvel événement</button>
        </div>
        <div id="evenements-list" class="evenements-list"></div>
        <a href="index.html" class="back-link">← Retour au site</a>
      </div>
      -->

      <!-- ===== ONGLET AVIS (OPTIONNEL) ===== -->
      <!-- OPTIONNEL: AVIS — décommenter si outil activé -->
      <!--
      <div id="tabAvis" class="tab-content">
        <div class="section-header">
          <h3>Avis clients</h3>
          <span class="badge-pending" id="avis-pending-count"></span>
        </div>
        <div id="avis-list" class="avis-list"></div>
        <a href="index.html" class="back-link">← Retour au site</a>
      </div>
      -->

      <!-- ===== ONGLET EMPORTER (OPTIONNEL) ===== -->
      <!-- OPTIONNEL: EMPORTER — décommenter si outil activé -->
      <!--
      <div id="tabEmporter" class="tab-content">
        <div class="section-header">
          <h3>Commandes à emporter</h3>
          <span class="today-badge" id="emporter-today-count">0 commande aujourd'hui</span>
        </div>
        <div id="emporter-list" class="emporter-list"></div>

        <section class="admin-card">
          <h4>Articles disponibles</h4>
          <div id="articles-list"></div>
          <button class="btn-secondary" id="addArticleBtn">+ Ajouter un article</button>
        </section>

        <section class="admin-card">
          <h4>Créneaux de retrait</h4>
          <div id="creneaux-midi" class="creneaux-group">
            <span>Service Midi :</span>
            <div id="creneaux-midi-list"></div>
          </div>
          <div id="creneaux-soir" class="creneaux-group">
            <span>Service Soir :</span>
            <div id="creneaux-soir-list"></div>
          </div>
        </section>

        <a href="index.html" class="back-link">← Retour au site</a>
      </div>
      -->

    </main>
  </section>

  <script src="admin.js"></script>
</body>
</html>
```

---

## STRUCTURE JS — admin.js

### Section 1 — Config (à personnaliser par client)

```javascript
// ============================================
// CONFIG CLIENT — seule section à modifier
// ============================================

const ADMIN_PASSWORD = 'admin2024';

const EMAILJS_SERVICE_ID = '{{EMAILJS_SERVICE_ID}}';
const EMAILJS_TEMPLATE_CLIENT = '{{EMAILJS_TPL_CLIENT}}';
const RESTAURANT_NAME = '{{NOM_ETABLISSEMENT}}';
const RESTAURANT_TEAM = '{{EQUIPE}}';

const DELETED_DEMO_KEY = 'deletedDemoIds';
```

### Section 2 — Données démo (à personnaliser par client)

```javascript
// ============================================
// DONNÉES DÉMO — 5 entrées réalistes
// ============================================

const DEMO_RESERVATIONS = [
  {
    id: Date.now() + 1,
    prenom: 'Sophie', nom: 'M.',
    email: 'sophie.m@email.fr',
    telephone: '06 12 34 56 78',
    date: offsetDate(1),   // demain
    time: '20:00',
    couverts: '4',
    message: 'Anniversaire de mariage',
    statut: 'Confirmée',
    source: 'demo'
  },
  {
    id: Date.now() + 2,
    prenom: 'Marc', nom: 'D.',
    email: 'marc.d@email.fr',
    telephone: '06 23 45 67 89',
    date: offsetDate(0),   // aujourd'hui
    time: '12:30',
    couverts: '2',
    message: '',
    statut: 'En attente',
    source: 'demo'
  },
  {
    id: Date.now() + 3,
    prenom: 'Claire', nom: 'R.',
    email: 'claire.r@email.fr',
    telephone: '06 34 56 78 90',
    date: offsetDate(0),   // aujourd'hui
    time: '19:30',
    couverts: '6',
    message: 'Table près de la fenêtre si possible',
    statut: 'En attente',
    source: 'demo'
  },
  {
    id: Date.now() + 4,
    prenom: 'Thomas', nom: 'L.',
    email: 'thomas.l@email.fr',
    telephone: '06 45 67 89 01',
    date: offsetDate(2),   // J+2
    time: '20:30',
    couverts: '3',
    message: '',
    statut: 'Confirmée',
    source: 'demo'
  },
  {
    id: Date.now() + 5,
    prenom: 'Émilie', nom: 'B.',
    email: 'emilie.b@email.fr',
    telephone: '06 56 78 90 12',
    date: offsetDate(-1),  // hier
    time: '20:00',
    couverts: '2',
    message: '',
    statut: 'Annulée',
    source: 'demo'
  }
];

function offsetDate(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}
```

### Section 3 — Menu par défaut (à remplacer par la vraie carte)

```javascript
// ============================================
// MENU PAR DÉFAUT — remplacer avec la vraie carte
// ============================================

const DEFAULT_MENU = {
  categories: [
    {
      id: 'entrees',
      name: 'Pour commencer',
      dishes: [
        { id: 'e1', name: '[Nom entrée 1]', description: '[Description]', price: '[Prix]' },
        { id: 'e2', name: '[Nom entrée 2]', description: '[Description]', price: '[Prix]' }
      ]
    },
    {
      id: 'plats',
      name: 'Plats',
      dishes: [
        { id: 'p1', name: '[Nom plat 1]', description: '[Description]', price: '[Prix]' },
        { id: 'p2', name: '[Nom plat 2]', description: '[Description]', price: '[Prix]' }
      ]
    },
    {
      id: 'desserts',
      name: 'Pour finir',
      dishes: [
        { id: 'd1', name: '[Nom dessert 1]', description: '[Description]', price: '[Prix]' }
      ]
    }
  ]
};
```

### Section 4 — Fonctions cœur (invariantes — ne pas modifier)

```javascript
// ============================================
// CORE — ne pas modifier
// ============================================

function safeParse(rawValue, fallback) {
  if (!rawValue) return fallback;
  try { return JSON.parse(rawValue); } catch (e) { return fallback; }
}

function getReservations() {
  const deletedIds = new Set(safeParse(localStorage.getItem(DELETED_DEMO_KEY), []));
  const userRes = safeParse(localStorage.getItem('actions_recues'), []);
  const demoRes = DEMO_RESERVATIONS.filter(r => !deletedIds.has(r.id));
  const all = [...demoRes, ...userRes];
  return all.sort((a, b) => a.date.localeCompare(b.date) || a.time.localeCompare(b.time));
}

function saveUserReservations(all) {
  const user = all.filter(r => !DEMO_RESERVATIONS.find(d => d.id === r.id));
  localStorage.setItem('actions_recues', JSON.stringify(user));
}

function ensureInitialData() {
  // Les démos sont toujours injectées dynamiquement via getReservations()
  // Cette fonction existe pour compatibilité et peut rester vide
}

function setStatut(id, statut, all) {
  const updated = all.map(r => r.id === id ? { ...r, statut } : r);
  saveUserReservations(updated);
  return updated;
}

function updateCompteurs(all) {
  const today = new Date().toISOString().split('T')[0];
  const todayCount = all.filter(r => r.date === today && r.statut !== 'Annulée').length;
  const pendingCount = all.filter(r => r.statut === 'En attente').length;
  const confirmedCount = all.filter(r => r.statut === 'Confirmée').length;

  const el = id => document.getElementById(id);
  if (el('stat-today')) el('stat-today').textContent = todayCount;
  if (el('stat-pending')) el('stat-pending').textContent = pendingCount;
  if (el('stat-week')) el('stat-week').textContent = confirmedCount;
  if (el('todayBadge')) el('todayBadge').textContent =
    `${todayCount} réservation${todayCount > 1 ? 's' : ''} aujourd'hui`;
}

function renderCalendar(all, selectedDate, onSelect) {
  const grid = document.getElementById('calendarGrid');
  if (!grid) return;
  const today = new Date();
  grid.innerHTML = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    const dateStr = d.toISOString().split('T')[0];
    const count = all.filter(r => r.date === dateStr && r.statut !== 'Annulée').length;
    const isActive = dateStr === selectedDate;
    return `<div class="calendar-day ${isActive ? 'active' : ''}" onclick="${onSelect}('${dateStr}')">
      <div class="day-name">${d.toLocaleDateString('fr-FR', { weekday: 'short' })}</div>
      <div class="day-number">${d.getDate()}</div>
      ${count > 0 ? `<div class="day-count">${count}</div>` : ''}
    </div>`;
  }).join('');
}

function renderReservations(all, selectedDate, filter) {
  const container = document.getElementById('reservations-list');
  if (!container) return;

  let list = all.filter(r => r.date === selectedDate);
  if (filter === 'lunch') list = list.filter(r => parseInt(r.time) < 15);
  if (filter === 'dinner') list = list.filter(r => parseInt(r.time) >= 15);

  if (list.length === 0) {
    container.innerHTML = '<p class="empty-state">Aucune réservation pour cette sélection.</p>';
    return;
  }

  container.innerHTML = list.map(r => {
    const badgeClass = r.statut === 'Confirmée' ? 'badge-confirmee'
      : r.statut === 'Annulée' ? 'badge-annulee' : 'badge-attente';
    return `<article class="reservation-card ${r.statut.toLowerCase()}">
      <div class="reservation-header">
        <span class="reservation-time">${r.time}</span>
        <span class="reservation-guests">${r.couverts} pers.</span>
      </div>
      <div class="reservation-info">
        <p class="reservation-name">${r.prenom} ${r.nom || ''}</p>
        <p>📞 ${r.telephone}</p>
        ${r.email ? `<p>✉️ ${r.email}</p>` : ''}
        ${r.message ? `<p>💬 ${r.message}</p>` : ''}
      </div>
      <span class="badge ${badgeClass}">${r.statut}</span>
      <div class="reservation-actions">
        <button class="btn-success" type="button"
          data-id="${r.id}" data-statut="Confirmée"
          ${r.statut === 'Confirmée' ? 'disabled' : ''}>✓ Confirmer</button>
        <button class="btn-danger" type="button"
          data-id="${r.id}" data-statut="Annulée"
          ${r.statut === 'Annulée' ? 'disabled' : ''}>✗ Annuler</button>
      </div>
    </article>`;
  }).join('');

  container.querySelectorAll('button[data-id]').forEach(btn => {
    btn.addEventListener('click', () => handleStatutChange(btn.dataset.id, btn.dataset.statut));
  });
}

// ============================================
// ARDOISE DU JOUR
// ============================================

const DEFAULT_ARDOISE = {{ARDOISE_INITIALE}};

function sauvegarderArdoise() {
  const el = id => document.getElementById(id);
  const msg = el('ardoise-message');

  const ardoise = {
    disponible: el('ardoise-disponible') ? el('ardoise-disponible').checked : true,
    plat: {
      nom: el('ardoise-plat') ? el('ardoise-plat').value.trim() : '',
      prix: el('ardoise-plat-prix') ? el('ardoise-plat-prix').value.trim() : '',
      note: el('ardoise-note') ? el('ardoise-note').value.trim() : ''
    },
    entree: el('ardoise-entree') && el('ardoise-entree').value.trim() ? {
      nom: el('ardoise-entree').value.trim(),
      prix: el('ardoise-entree-prix') ? el('ardoise-entree-prix').value.trim() : ''
    } : null,
    dessert: el('ardoise-dessert') && el('ardoise-dessert').value.trim() ? {
      nom: el('ardoise-dessert').value.trim(),
      prix: el('ardoise-dessert-prix') ? el('ardoise-dessert-prix').value.trim() : ''
    } : null,
    formule: el('formule-active') && el('formule-active').checked ? {
      active: true,
      label: el('formule-label') ? el('formule-label').value.trim() : '',
      prix: el('formule-prix') ? el('formule-prix').value.trim() : ''
    } : { active: false }
  };

  const existing = safeParse(localStorage.getItem('contenu_editable'), {});
  localStorage.setItem('contenu_editable', JSON.stringify({ ...existing, ardoise }));

  if (msg) {
    msg.classList.remove('hidden');
    setTimeout(() => msg.classList.add('hidden'), 5000);
  }
}

function hydrateArdoiseForm() {
  const data = safeParse(localStorage.getItem('contenu_editable'), {});
  const a = data.ardoise || DEFAULT_ARDOISE;
  if (!a) return;
  const el = id => document.getElementById(id);

  if (el('ardoise-disponible')) el('ardoise-disponible').checked = a.disponible !== false;
  if (a.plat) {
    if (el('ardoise-plat')) el('ardoise-plat').value = a.plat.nom || '';
    if (el('ardoise-plat-prix')) el('ardoise-plat-prix').value = a.plat.prix || '';
    if (el('ardoise-note')) el('ardoise-note').value = a.plat.note || '';
  }
  if (a.entree) {
    if (el('ardoise-entree')) el('ardoise-entree').value = a.entree.nom || '';
    if (el('ardoise-entree-prix')) el('ardoise-entree-prix').value = a.entree.prix || '';
  }
  if (a.dessert) {
    if (el('ardoise-dessert')) el('ardoise-dessert').value = a.dessert.nom || '';
    if (el('ardoise-dessert-prix')) el('ardoise-dessert-prix').value = a.dessert.prix || '';
  }
  if (a.formule && a.formule.active) {
    if (el('formule-active')) el('formule-active').checked = true;
    const fields = document.getElementById('formule-fields');
    if (fields) fields.classList.remove('hidden');
    if (el('formule-label')) el('formule-label').value = a.formule.label || '';
    if (el('formule-prix')) el('formule-prix').value = a.formule.prix || '';
  }
}
```

### Section 5 — EmailJS (restauration uniquement — supprimer si non utilisé)

```javascript
// ============================================
// EMAILJS — supprimer si non utilisé
// ============================================

async function sendClientConfirmationEmail(reservation) {
  try {
    const serviceLabel = parseInt(reservation.time) < 15 ? 'Déjeuner' : 'Dîner';
    await emailjs.send(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_CLIENT, {
      to_name: `${reservation.prenom} ${reservation.nom || ''}`.trim(),
      to_email: reservation.email,
      reservation_date: new Date(reservation.date).toLocaleDateString('fr-FR', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
      }),
      reservation_time: reservation.time,
      service_label: serviceLabel,
      guests: reservation.couverts,
      client_phone: reservation.telephone,
      client_message: reservation.message || 'Aucun message spécial',
      restaurant_name: RESTAURANT_NAME,
      restaurant_team: RESTAURANT_TEAM
    });
    return true;
  } catch (e) {
    return false;
  }
}
```

---

## OUTILS PAR CATÉGORIE

| Outil | Restauration | Services/Artisan | Commerce |
|---|---|---|---|
| Login gérant | ✓ obligatoire | ✓ | ✓ |
| 3 KPI | ✓ obligatoire | ✓ | ✓ |
| Réservations + calendrier semaine | ✓ obligatoire | ✓ (RDV) | — |
| Menu & Ardoise | ✓ obligatoire | — | ✓ (catalogue) |
| Capacités (sub-section réservations) | ✓ obligatoire | ✓ (créneaux) | — |
| EmailJS confirmation client | ✓ optionnel | optionnel | — |
| Événements & Privatisations | ✓ optionnel | — | — |
| Avis clients | ✓ optionnel | ✓ optionnel | ✓ optionnel |
| Vente à emporter | ✓ optionnel | — | — |

---

## CHECKLIST QUALITÉ AVANT LIVRAISON

**Variables & données :**
- [ ] `{{NOM_ETABLISSEMENT}}` remplacé partout (title, h1, h2, emails, confirmations)
- [ ] Mot de passe `admin2024` codé en dur dans `ADMIN_PASSWORD`
- [ ] Données démo réservations : 5 entrées (2 En attente, 2 Confirmées, 1 Annulée)
- [ ] Données démo ardoise initiale : plat + prix + note réalistes
- [ ] Carte par défaut = vraie carte du restaurant (extraite Phase 2, pas générique)
- [ ] Capacités par défaut adaptées au vrai service ({{CAPACITE_DEJEUNER}} / {{CAPACITE_DINER}})

**Fonctionnel — obligatoires :**
- [ ] Login + logout fonctionnels
- [ ] Calendrier semaine → filtre jour → liste réservations
- [ ] Filtres Déjeuner / Dîner / Tous opérationnels
- [ ] Confirmer/Annuler → badge statut mis à jour sans rechargement
- [ ] Ardoise toggle "Disponible" → section masquée sur index immédiatement
- [ ] Ardoise "Mettre à jour" → confirmation inline 5s → visible sur index au rechargement
- [ ] Éditeur carte → "Sauvegarder" → confirmation inline → visible sur index au rechargement
- [ ] Capacités → bloquer le formulaire index si service complet

**Fonctionnel — optionnels (selon outils activés) :**
- [ ] [EmailJS] Email confirmation envoyé au clic "Confirmer" (une seule fois, flag)
- [ ] [Événements] Toggle Visible/Masqué → section index masquée si aucun visible
- [ ] [Avis] Badge "En attente" sur les nouveaux avis, modération fonctionnelle
- [ ] [Emporter] Statuts 4 étapes (En attente → En préparation → Prête → Remise)
- [ ] [Emporter] Toggle article Dispo/Indispo → masqué du formulaire index

**Charte visuelle (depuis STACK_STANDARD.md) :**
- [ ] Bouton admin en haut à **droite** du header index.html
- [ ] Lien discret `Espace gérant` dans le footer de index.html → `admin.html`
- [ ] Hero : image réelle + overlay rgba min 0.40 + H1 blanc police titres client
- [ ] Sections alternées bg-main / bg-alt (jamais 2 adjacentes identiques)
- [ ] Accent max 3 utilisations distinctes

**UX :**
- [ ] Admin jamais vide au premier chargement (données démo toujours présentes)
- [ ] Aucun `console.log` laissé dans le code
- [ ] Responsive 390px
- [ ] `safeParse` sur tous les `JSON.parse`
- [ ] Confirmation inline uniquement (pas d'`alert()`)
- [ ] Aucun texte Lorem ipsum, placeholder, ou générique visible

---

*Version 2 — 2026-04-15 — Outils V2 restauration : Menu & Ardoise + 3 optionnels*
