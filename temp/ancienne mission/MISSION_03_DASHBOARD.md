# MISSION 03 — Dashboard

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2 — lire entièrement)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Dashboard — Vue Bilan (index.html)

OBJECTIF :
Implémenter la page d'accueil de JARVIS : un tableau de bord chronologique
qui mélange chats et modules code, permettant le "bilan du matin".
L'utilisateur voit d'un coup d'œil ce qui s'est passé, quels pipelines ont tourné,
quels chats ont eu lieu, et s'il y a des pipelines actifs en attente.

PÉRIMÈTRE :
Fichiers à modifier :
- frontend/index.html  (ajouter le contenu dans #page-dashboard)

Fichiers à créer :
- frontend/assets/js/dashboard.js

Prérequis : Mission 02 doit être terminée (layout + api.js + shared.js + sidebar.js + ui.js).

---

INSTRUCTIONS DÉTAILLÉES :

### frontend/index.html

Le shell est déjà en place (Mission 02). Ajouter dans `#page-dashboard` le squelette HTML :

```html
<div id="page-dashboard">
  <!-- Header bilan -->
  <div class="dashboard-header">
    <h1 class="dashboard-title">Bonjour</h1>
    <div class="dashboard-subtitle" id="dashboard-subtitle">Chargement...</div>
  </div>

  <!-- Pipeline actif (caché si aucun) -->
  <div id="active-pipeline-section" class="dashboard-section" style="display:none">
    <h2 class="section-title">⚡ Module Code actif</h2>
    <div id="active-pipeline-list"></div>
  </div>

  <!-- Filtres date -->
  <div class="dashboard-filters">
    <button class="filter-btn filter-btn--active" data-period="today">Aujourd'hui</button>
    <button class="filter-btn" data-period="yesterday">Hier</button>
    <button class="filter-btn" data-period="week">Cette semaine</button>
  </div>

  <!-- Timeline activité -->
  <div class="dashboard-section">
    <h2 class="section-title">Activité récente</h2>
    <div id="activity-timeline"></div>
  </div>

  <!-- Stats résumé -->
  <div id="dashboard-stats" class="dashboard-stats"></div>
</div>
```

---

### frontend/assets/js/dashboard.js

**Chargement des données :**
Au DOMContentLoaded, charger en parallèle via Promise.all :
- `API.getProjects()` → pour associer les noms de projets aux sessions
- `API.getConversations()` → toutes les conversations (avec last_message_at + last_message_preview)
- `API.getLogs({lines: 200})` → pour détecter l'activité récente des sessions

Également charger les sessions de chaque projet pour avoir les coûts :
Pour chaque projet retourné, faire `API.getProjectSessions(project.id)` en parallèle.

**Construction de la timeline :**
Fusionner conversations et sessions dans une seule liste, triée par date descendante.
Chaque item de la timeline est un objet normalisé :
```js
{
  type: 'chat' | 'module',
  id: ...,
  title: ...,         // titre conversation ou workflow_type de la session
  project_id: ...,
  project_name: ...,  // résolu depuis la liste des projets
  date: ...,          // ISO string pour tri
  status: ...,        // pour les modules : COMPLETED/RUNNING/ERROR/etc.
  cost: ...,          // pour les modules : total_cost_usd
  preview: ...,       // pour les chats : last_message_preview
  href: ...,          // URL de navigation vers cet item
}
```

**Rendu d'un item timeline :**
```html
<div class="timeline-item timeline-item--{type}" onclick="navigate vers href">
  <div class="timeline-icon">{💬 ou ⚙️}</div>
  <div class="timeline-content">
    <div class="timeline-title">{title}</div>
    <div class="timeline-meta">
      <span class="timeline-project">{project_name ou "Sans projet"}</span>
      <span class="timeline-date">{formatDate(date)}</span>
      {si module : statusBadge(status)}
      {si module et cost > 0 : costBadge(cost)}
    </div>
    {si chat et preview : <div class="timeline-preview">{preview tronqué à 80 chars}</div>}
  </div>
</div>
```

Clic sur un item → navigation vers son `href` (chat.html?id=X ou module-code.html?session=Y).

**Section pipeline actif :**
Filtrer les sessions dont `status` n'est pas dans ['COMPLETED', 'ABORTED'].
Si au moins une : rendre `#active-pipeline-section` visible.
Pour chaque session active :
```html
<div class="active-pipeline-card card card--interactive">
  <div class="active-pipeline-info">
    <span class="active-dot"></span>
    <strong>{workflow_type}</strong>
    <span class="text-muted">· {project_name} · Step {current_step_index + 1}</span>
  </div>
  <a href="module-code.html?session={id}&project_id={project_id}" class="btn-primary btn-sm">
    → Reprendre
  </a>
</div>
```

**Filtres date :**
Boutons Aujourd'hui / Hier / Cette semaine.
Clic → filtrer la timeline et recalculer les stats.
Bouton actif → class `filter-btn--active`.

**Header bilan :**
`#dashboard-subtitle` : afficher "X sessions · Y chats · Coût total : $Z" pour la période sélectionnée.
Si période = "today" et aucune activité → "Aucune activité aujourd'hui".

**Stats résumé (bas de page) :**
3 cards côte à côte :
- Sessions cette semaine : N
- Conversations cette semaine : N
- Coût cette semaine : $X.XXX

**CSS spécifique à ajouter dans style.css :**
```
.dashboard-header : margin-bottom 2rem
.dashboard-title : font-size 1.8rem, font-weight 600
.dashboard-subtitle : color var(--text-muted), margin-top 0.25rem
.dashboard-filters : display flex, gap 8px, margin-bottom 1.5rem
.filter-btn : btn-secondary style + border-radius 9999px + padding 6px 16px
.filter-btn--active : background var(--accent), color white, border-color var(--accent)
.dashboard-section : margin-bottom 2rem
.section-title : font-size 1rem, font-weight 600, color var(--text-muted), text-transform uppercase, letter-spacing 0.05em, margin-bottom 1rem
.timeline-item : display flex, gap 12px, padding 12px, border-radius 8px, cursor pointer, hover background var(--bg-card), margin-bottom 4px, transition 0.15s
.timeline-icon : width 32px, height 32px, border-radius 50%, background var(--bg-input), display flex, align-items center, justify-content center, flex-shrink 0
.timeline-content : flex 1, min-width 0
.timeline-title : font-weight 500, white-space nowrap, overflow hidden, text-overflow ellipsis
.timeline-meta : display flex, align-items center, gap 8px, margin-top 2px, font-size 0.8rem
.timeline-project : color var(--accent), font-size 0.8rem
.timeline-date : color var(--text-muted)
.timeline-preview : color var(--text-muted), font-size 0.85rem, margin-top 4px, white-space nowrap, overflow hidden, text-overflow ellipsis
.active-pipeline-card : display flex, align-items center, justify-content space-between, padding 12px 16px, margin-bottom 8px
.active-dot : width 8px, height 8px, border-radius 50%, background var(--success), animation pulse 1.5s infinite, margin-right 8px
.dashboard-stats : display grid, grid-template-columns repeat(3, 1fr), gap 1rem, margin-top 2rem
.stat-card : card style + text-align center
.stat-value : font-size 1.5rem, font-weight 600, color var(--accent)
.stat-label : font-size 0.8rem, color var(--text-muted), margin-top 4px
```

---

TESTS MANUELS (3 étapes) :

1. Ouvrir http://localhost:8000 → la page charge, le dashboard s'affiche avec la timeline.
   Si des conversations et/ou sessions existent → elles apparaissent mélangées par date.
   Le header "Bonjour" affiche le bon résumé.

2. Si une session est active (non COMPLETED/ABORTED) → la section "Module Code actif" est visible
   avec le bouton "Reprendre" qui pointe vers le bon URL.

3. Cliquer sur les filtres "Hier" et "Cette semaine" → la timeline se filtre correctement.
   Cliquer sur un item chat → navigation vers chat.html avec les bons params.
   Cliquer sur un item module → navigation vers module-code.html avec les bons params.

FIN DE MISSION :
- Tests manuels validés
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
