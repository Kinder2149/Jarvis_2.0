# STACK_STANDARD — L'ATELIER CONNECTÉ
> **RÉFÉRENCE CLAUDE** — Lu lors de la génération du PROMPT_CASCADE. Ne pas copier dans le dossier client.
> Règles techniques applicables à toutes les démos client.
> Les spécificités client sont dans PROMPT_CASCADE_[NOM].md.

---

## TECHNOLOGIES AUTORISÉES

| Élément | Choix | Interdit |
|---|---|---|
| Structure | HTML5 sémantique | Frameworks (React, Vue, etc.) |
| Style | CSS3 natif avec variables CSS | Tailwind, Bootstrap, SASS |
| Comportement | JavaScript vanilla (ES6+) | TypeScript, jQuery |
| Fonts | Google Fonts (via CDN link) | Fonts locales |
| Données | localStorage uniquement | Backend, Firebase, Supabase |
| Déploiement | GitHub Pages (statique) | Serveur, base de données |
| Emails | EmailJS — restauration uniquement, si confirmation client nécessaire | Autres services mail |

---

## ARCHITECTURE DE DONNÉES

### Clés localStorage — base (tous secteurs)

```javascript
// index.html écrit — admin.html lit
localStorage.setItem("actions_recues", JSON.stringify([...]))

// admin.html écrit — index.html lit au rechargement
localStorage.setItem("contenu_editable", JSON.stringify({...}))
```

**Format `actions_recues` (tableau) :**
```json
[
  {
    "id": "demo-1",
    "prenom": "Marie D.",
    "telephone": "06 12 34 56 78",
    "date": "2026-04-16",
    "service": "diner",
    "couverts": "2",
    "message": "...",
    "statut": "En attente",
    "source": "demo"
  }
]
```
> `id` : `"demo-1"` à `"demo-5"` pour les données démo, `Date.now()` (number) pour les soumissions utilisateur.
> `service` : `"dejeuner"` ou `"diner"` (minuscules, sans accents) — valeur interne stockée par le formulaire.
> `date` : format ISO `"YYYY-MM-DD"` — calculé dynamiquement par `offsetDate(N)` dans admin.js.

**Format `contenu_editable` (objet) :**
```json
{
  "suggestion_du_jour": {
    "plat": "...",
    "prix": "17,00 €",
    "note": "..."
  }
}
```

### Clés localStorage — restauration uniquement (modules avancés)

```javascript
// admin.html écrit — index.html lit au rechargement
localStorage.setItem("menuCard", JSON.stringify({categories: [...]}))

// admin.html écrit — index.html lit pour vérifier disponibilité
localStorage.setItem("tableCapacity", JSON.stringify({default: {dejeuner: 15, diner: 15}, dates: {}}))

// clé interne admin — IDs réservations démo supprimées
localStorage.setItem("deletedDemoIds", JSON.stringify([...]))
```

**Initialisation obligatoire :** Si `actions_recues` absent au chargement de admin.html → injecter les données de démo automatiquement.

---

## STRUCTURE ADMIN — STANDARD UNIVERSEL

### Naming normalisé

**Titre de page :** `Espace Gérant — [NOM_ETABLISSEMENT]`
**En-tête dashboard :** `<h2>Espace Gérant — [NOM_ETABLISSEMENT]</h2>`

Ne jamais utiliser de libellé générique seul ("Espace Restaurant", "Dashboard", "Admin").
Toujours associer le libellé métier + le nom de l'établissement.

### Structure obligatoire de admin.html

```
1. Écran de login (plein écran, avant tout)
   └── Logo + titre "Espace Gérant — [NOM]"
   └── Champ mot de passe + bouton œil (afficher/masquer)
   └── Bouton "Accéder à mon espace"
   └── Message d'erreur inline (pas d'alert)

2. Dashboard (visible uniquement après login)
   └── Header : logo + "Espace Gérant — [NOM]" + bouton "Se déconnecter"
   └── 3 compteurs KPI
   └── Liste des actions reçues (cartes + badges statut + boutons métier)
   └── Éditeur de contenu (ce qui change souvent)
   └── [Restauration] Onglets : Réservations / Menu & Ardoise / [optionnels activés]
```

**Mot de passe admin :** `admin` — codé en dur dans admin.js (pas de vrai backend)

Code de validation obligatoire dans admin.js — reproduire exactement, ne pas modifier le mot de passe :

```javascript
const MOT_DE_PASSE_ADMIN = 'admin';

function verifierMotDePasse(saisie) {
  return saisie === MOT_DE_PASSE_ADMIN;
}
```

> ⚠️ INTERDIT : `admin123`, `password`, tout autre valeur. Le mot de passe est toujours `admin`, sans exception.

### 3 compteurs KPI (adapter le vocabulaire au secteur)

| Restauration | Services/Artisan | Commerce |
|---|---|---|
| Demandes aujourd'hui | Rendez-vous aujourd'hui | Commandes aujourd'hui |
| En attente de confirmation | En attente | En attente |
| Confirmées cette semaine | Confirmés cette semaine | Traités cette semaine |

---

## RÈGLES CSS

```css
:root {
  --bg-main: [HEX depuis PROMPT_CASCADE];
  --bg-alt: [HEX depuis PROMPT_CASCADE];
  --accent: [HEX depuis PROMPT_CASCADE];
  --text-main: [HEX depuis PROMPT_CASCADE];
  --text-secondary: [HEX depuis PROMPT_CASCADE];
  --card-bg: [calculé : légèrement plus clair que --bg-main];
  --border-soft: [calculé : très discret];
  --success: #3d9b5f;
  --warning: #b6883f;
  --danger: #a64848;
}
```

**Variables obligatoires** : toujours définies dans `:root`, jamais de couleurs en dur dans les sélecteurs.

---

## CHARTE VISUELLE — RÈGLES D'APPLICATION

> Ces règles s'appliquent à toutes les démos. Elles explicitent COMMENT utiliser les variables CSS du client.
> Cascade ne choisit pas — il applique. Tout écart par rapport à ces règles est un bug.

### Hero (section d'ouverture)

- **Fond** : image réelle du client en `background-image` CSS uniquement — jamais de `<img>` dans le hero — propriétés obligatoires : `background-size: cover; background-position: center; background-repeat: no-repeat; min-height: 90vh`
- **Position et z-index** : `position: relative; z-index: 1;` — JAMAIS de z-index supérieur à 10 sur le hero — le hero doit TOUJOURS rester en arrière-plan du reste de la page
- **Overlay** : `rgba(0, 0, 0, 0.40)` minimum — jamais d'image sans overlay (lisibilité garantie) — l'overlay doit avoir `position: absolute; z-index: 1;` et le contenu hero `position: relative; z-index: 2;`
- **Logo** : affiché en haut à gauche dans la nav, blanc si l'image est sombre
- **H1** : police titres du client (Google Font), blanc, `font-size` min `2.5rem` desktop, `2rem` mobile
- **Sous-titre** : accroche réelle du client, blanc, `font-size` `1.1rem`, opacité `0.9`
- **CTA principal** : fond `--accent`, texte blanc, centré sous le H1, visible sans scroll sur 1280px

CSS obligatoire pour le hero — reproduire exactement, ne pas modifier les valeurs de position ni z-index :

```css
/* === HERO — STRUCTURE OBLIGATOIRE === */
.hero {
  position: relative;        /* JAMAIS fixed, JAMAIS sticky, JAMAIS absolute */
  z-index: 1;                /* JAMAIS supérieur à 10 */
  min-height: 90vh;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  inset: 0;                  /* équivalent top:0 right:0 bottom:0 left:0 */
  background: rgba(0, 0, 0, 0.40);
  z-index: 1;                /* derrière le contenu hero, devant l'image */
}

.hero-content {
  position: relative;
  z-index: 2;                /* devant l'overlay, mais pas plus */
}

/* Sections APRÈS le hero — toujours visibles, jamais cachées */
section:not(.hero) {
  position: relative;
  z-index: 0;                /* en dessous du hero — c'est NORMAL et VOULU */
}
```

> ⚠️ INTERDIT sur .hero : `position: fixed`, `position: sticky`, `z-index > 10`, `overflow: visible` avec contenu absolu.
> ⚠️ INTERDIT : image dans le hero via `<img>` — uniquement `background-image` CSS.

### Sections du corps (alternance obligatoire)

- **Section impaire** (1ère, 3ème, 5ème...) : fond `--bg-main`
- **Section paire** (2ème, 4ème, 6ème...) : fond `--bg-alt`
- **Jamais 2 sections adjacentes de même fond** — si nécessaire, recalculer l'ordre
- **Padding** : `4rem 0` desktop, `2.5rem 0` mobile — jamais inférieur

### Accent (`--accent`)

Utilisations autorisées :
- CTA principaux et secondaires (fond)
- Badges de statut actif
- Prix mis en avant
- Bordure gauche des cartes en évidence
- Fond léger de la section Ardoise (8-10% opacité uniquement)

**Interdit :**
- Fond d'une section entière à 100% opacité
- Plus de 3 utilisations visuellement distinctes sur une même page
- Texte sur fond `--accent` sauf blanc ou très clair (contraste WCAG AA minimum)

### Typographies

- **H1, H2** : toujours la Google Font titre du client — jamais de fallback seul sur un titre visible
- **H3, corps** : police secondaire du client si fournie, sinon `system-ui, sans-serif`
- **Maximum 2 polices** sur la page — jamais 3
- **Font-weight** : titres `600` ou `700`, corps `400`, accent `500`

### Cartes et composants

- **Fond carte** : `--card-bg` (légèrement plus clair que `--bg-main`)
- **Bordure** : `1px solid var(--border-soft)` — jamais de bordure colorée sauf état actif/sélectionné
- **Border-radius** : `8px` pour les cartes, `4px` pour les boutons et badges
- **Ombre** : `0 2px 8px rgba(0,0,0,0.08)` maximum — jamais d'ombre forte

### Mobile (390px minimum)

- Navigation : logo à gauche, bouton admin à droite — pas de menu hamburger nécessaire
- Hero : `min-height: 85vh`, texte centré
- Formulaires : champs pleine largeur, bouton submit pleine largeur
- Cartes : empilées en colonne unique
- Onglets admin : scroll horizontal si + de 3 onglets

---

## RÈGLES HTML

- Pas de `<form>` avec `action` ou `method` — toute soumission gérée par JS + localStorage
- Tout bouton de soumission : `type="button"` géré par JS ou `type="submit"` avec `preventDefault()`
- Libellés boutons : toujours en langage métier. Interdit : "Submit", "OK", "Send", "Dashboard"
- Confirmation après soumission : message inline visible 4s (pas d'alert, pas de pop-up)
- Favicon : `<link rel="icon">` pointant vers l'URL du logo client

---

## RÈGLES JAVASCRIPT

- Un fichier par contexte : `script.js` pour index, `admin.js` pour admin
- Fonctions nommées de façon lisible : `renderReservations()`, `setStatut()`, etc.
- Pas de `console.log` laissé dans le code livré
- Gestion d'erreur sur tout `JSON.parse()` via `safeParse()` :

```javascript
function safeParse(rawValue, fallbackValue) {
  if (!rawValue) return fallbackValue;
  try {
    return JSON.parse(rawValue);
  } catch (e) {
    return fallbackValue;
  }
}
```

- Données démo injectées si localStorage absent :

```javascript
function ensureInitialData() {
  const existing = localStorage.getItem("actions_recues");
  if (!existing) {
    localStorage.setItem("actions_recues", JSON.stringify(defaultData));
  }
}
document.addEventListener("DOMContentLoaded", ensureInitialData);
```

---

## RÈGLES UX — NON NÉGOCIABLES

| Règle | Standard |
|---|---|
| CTA principal | Visible sans scroll sur desktop 1280px |
| Bouton admin | En haut à droite du header de index.html + lien discret `Espace gérant` dans le footer |
| Libellés | Toujours en langage métier |
| Confirmation formulaire | Message inline visible 4s, couleur --accent |
| Admin au premier chargement | 5 entrées de démo présentes, jamais vide |
| Textes | 100% réels — zéro Lorem ipsum, zéro placeholder visible |
| Mobile | Lisible et navigable sur 390px minimum |
| Naming admin | Toujours "[Libellé métier] — [NOM_ETABLISSEMENT]" |

---

## STRUCTURE DU HEADER INDEX.HTML

```html
<header>
  <nav>
    <a href="#top" class="nav-logo">
      <img src="[URL_LOGO]" alt="Logo [NOM]" />
    </a>
    <a href="admin.html" class="btn-admin">🔒 Espace [NOM_METIER]</a>
  </nav>
  <!-- hero content -->
</header>
```

Le bouton admin est dans la `<nav>`, visible en haut à droite. Un lien discret `Espace gérant` est aussi présent dans le `<footer>` (texte petit, couleur `var(--text-sec)`).

---

## EMAILJS — RESTAURATION UNIQUEMENT

Si le client souhaite les emails de confirmation automatiques :

```html
<!-- Dans <head> de admin.html -->
<script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>
<script>(function(){ emailjs.init("{{EMAILJS_PUBLIC_KEY}}"); })();</script>
```

**2 templates à configurer dans le compte EmailJS client :**
- `template_notif_admin` : notification à l'établissement à chaque nouvelle réservation
- `template_confirm_client` : email de confirmation envoyé au client quand l'admin clique "Confirmer"

**Variables à passer dans les templates :**
`to_name`, `to_email`, `reservation_date`, `reservation_time`, `service_label`, `guests`, `client_phone`, `client_message`, `restaurant_name`, `restaurant_team`

**Garde-fous :**
- Flag `clientConfirmationSent` sur chaque réservation pour éviter les renvois
- Envoi séquentiel (pas parallèle)
- `try/catch` sur chaque `emailjs.send()`

---

## CHECKLIST FINALE AVANT LIVRAISON

**Fonctionnel :**
- [ ] Variables CSS définies dans `:root` avec les vraies valeurs
- [ ] Bouton admin en haut à droite du header + lien discret `Espace gérant` dans le footer
- [ ] Hero visible sans scroll — CTA en libellé métier
- [ ] Formulaire → localStorage → admin reçoit
- [ ] 5 données démo pré-chargées au premier chargement admin
- [ ] Éditeur admin → modification visible sur index au rechargement
- [ ] Login admin fonctionne avec le mot de passe "admin"
- [ ] Favicon présent
- [ ] Aucun texte générique visible
- [ ] Mobile lisible 390px
- [ ] Aucun console.log laissé

**Naming :**
- [ ] Titre `<title>` : "Espace Gérant — [NOM_ETABLISSEMENT]"
- [ ] En-tête dashboard : "[NOM_ETABLISSEMENT]" visible en toutes lettres
- [ ] Aucun libellé générique seul ("Espace Restaurant", "Admin", "Dashboard")

**[Restauration — outils activés selon PROMPT_CASCADE] :**
- [ ] Onglet Réservations : calendrier semaine + filtres déjeuner/dîner (toujours présent)
- [ ] Onglet Menu & Ardoise : ardoise du jour + éditeur carte → visible sur index (toujours présent)
- [ ] Onglet Événements : liste + toggle visible/masqué (si activé)
- [ ] Onglet Avis : modération + toggle visible/masqué (si activé)
- [ ] Onglet Emporter : commandes + gestion articles + créneaux (si activé)

**Charte visuelle :**
- [ ] Hero : image réelle + overlay rgba min 0.40 + H1 blanc police titres client
- [ ] Sections alternées : bg-main / bg-alt sans 2 adjacentes identiques
- [ ] Accent utilisé max 3 fois de façon distincte (CTA, badges, ardoise fond léger)
- [ ] Maximum 2 Google Fonts sur la page
- [ ] Bouton admin : en haut à **droite** du header + lien discret `Espace gérant` dans le footer

---

*Générique — version 2026-04-15 — Ajout charte visuelle + outils V2 restauration*
