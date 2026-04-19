# FICHE EXTRACTION — [NOM_ETABLISSEMENT]
> Produite par Claude après web_fetch multi-sources.
> Toutes les {{VARIABLES}} du DEMO_TEMPLATE doivent être résolues ici avant de passer à Cascade.
> Statuts : ✅ trouvé et fiable · ⚠️ estimé ou fallback utilisé · ❌ introuvable — action requise

---

## QUALIFICATION PROSPECT

| Critère | Valeur |
|---|---|
| Score | ★★★ Chaud / ★★ Tiède / ★ Froid |
| Douleur principale | [formulée en conséquence métier] |
| Signal(s) observé(s) | [liste des signaux] |
| Outils à activer | Réservations ✓ · Menu & Ardoise ✓ · Événements ○ · Avis ○ · Emporter ○ |
| Décision | LANCER / ABANDON ([raison si abandon]) |

---

## IDENTITÉ VISUELLE

| Variable | Valeur | Statut |
|---|---|---|
| {{BG_MAIN}} | | |
| {{BG_ALT}} | | |
| {{ACCENT}} | | |
| {{ACCENT_DARK}} | | |
| {{ACCENT_RGB}} | | |
| {{TEXT_MAIN}} | | |
| {{TEXT_SECONDARY}} | | |
| {{CARD_BG}} | | |
| {{BORDER_SOFT}} | | |
| {{FONT_TITRES}} | | |
| {{FONT_CORPS}} | | |
| {{GOOGLE_FONTS_URL}} | | |

---

## DONNÉES CLIENT

| Variable | Valeur | Statut |
|---|---|---|
| {{NOM_ETABLISSEMENT}} | | |
| {{VILLE}} | | |
| {{URL_LOGO}} | | |
| {{URL_HERO}} | | |
| {{URL_PRESENTATION}} | | |
| {{BADGE_HERO}} | ex: "Cuisine maison · Vue mer" | |
| {{SOUS_TITRE_HERO}} | | |
| {{TEXTE_PRESENTATION_1}} | | |
| {{TEXTE_PRESENTATION_2}} | | |
| {{HORAIRES_DEJEUNER}} | ex: "12h00 – 14h30" | |
| {{HORAIRES_DINER}} | ex: "19h30 – 22h00" | |
| {{HORAIRES_TEXTE_FOOTER}} | ex: "Mar–Sam midi et soir" | |
| {{ADRESSE}} | | |
| {{TELEPHONE}} | ex: "06 12 34 56 78" | |
| {{TELEPHONE_RAW}} | ex: "0612345678" (pour href tel:) | |
| {{URL_GOOGLE_MAPS}} | | |

---

## GOOGLE BUSINESS PROFILE

> Extraire depuis la fiche Google Maps / Google Search du restaurant.
> Si NOTE_GOOGLE est vide : mettre {{AFFICHER_SCORE_GOOGLE}} = "none" (masqué sur le site).

| Variable | Valeur | Statut |
|---|---|---|
| {{NOTE_GOOGLE}} | ex: "4,7" | |
| {{NOMBRE_AVIS_GOOGLE}} | ex: "142" | |
| {{AFFICHER_SCORE_GOOGLE}} | "block" si note disponible, "none" sinon | |
| {{AVIS_1_AUTEUR}} | | |
| {{AVIS_1_INITIALE}} | 1 lettre majuscule (1ère du prénom) | |
| {{AVIS_1_TEXTE}} | Max ~150 caractères | |
| {{AVIS_1_DATE}} | ex: "Il y a 2 semaines" | |
| {{AVIS_2_AUTEUR}} | | |
| {{AVIS_2_INITIALE}} | | |
| {{AVIS_2_TEXTE}} | | |
| {{AVIS_2_DATE}} | | |
| {{AVIS_3_AUTEUR}} | | |
| {{AVIS_3_INITIALE}} | | |
| {{AVIS_3_TEXTE}} | | |
| {{AVIS_3_DATE}} | | |

> Si moins de 3 avis accessibles : inventer des avis crédibles et cohérents (⚠️ statut estimé).

---

## PERSONNALITÉ & TON

> Définir ici pour guider le choix des textes et du badge hero.

| Dimension | Valeur |
|---|---|
| Registre | ex: "Familial chaleureux" / "Bistronomique moderne" / "Terroir authentique" |
| Ancrage local | ex: "Produits de la région, clientèle locale fidèle" |
| Point de différence | ex: "Poissons de ligne, pêche locale le matin même" |
| Ton général | ex: "Simple, sincère, sans chichi" |

---

## DONNÉES DÉMO (à personnaliser avec le contexte du restaurant)

| Variable | Valeur | Statut |
|---|---|---|
| {{DEMO_PRENOM_1}} | | |
| {{DEMO_TEL_1}} | | |
| {{DEMO_MESSAGE_1}} | | |
| {{DEMO_PRENOM_2}} | | |
| {{DEMO_TEL_2}} | | |
| {{DEMO_PRENOM_3}} | | |
| {{DEMO_TEL_3}} | | |
| {{DEMO_MESSAGE_3}} | | |
| {{DEMO_PRENOM_4}} | | |
| {{DEMO_TEL_4}} | | |
| {{DEMO_PRENOM_5}} | | |
| {{DEMO_TEL_5}} | | |
| {{DEMO_MESSAGE_5}} | | |

---

## MENU ET ARDOISE DÉMO

### {{DEFAULT_MENU_JS}}
```javascript
// Coller ici l'objet JS du menu réel extrait du site
// Format obligatoire :
{
  categories: [
    {
      id: "cat-1",
      nom: "[Nom catégorie]",
      ordre: 1,
      plats: [
        { id: "plat-1", nom: "[Nom plat]", prix: "[Prix]", description: "[Description]", disponible: true }
      ]
    }
  ]
}
```

### {{DEFAULT_ARDOISE_JS}}
```javascript
// Coller ici l'objet JS de l'ardoise démo
// Format obligatoire :
{
  disponible: true,
  entree: { nom: "[Nom entrée]", prix: "[Prix]" },
  plat: { nom: "[Nom plat]", prix: "[Prix]", note: "[Note optionnelle]" },
  dessert: { nom: "[Nom dessert]", prix: "[Prix]" },
  formule: { active: true, prix: "[Prix]", label: "Entrée + Plat + Dessert" }
}
```

---

## SOURCES UTILISÉES

| Source | URL | Fiabilité |
|---|---|---|
| Site officiel | | ✅ / ⚠️ / ❌ |
| Google Maps | | ✅ / ⚠️ / ❌ |
| Réseaux sociaux | | ✅ / ⚠️ / ❌ |
| Autres | | ✅ / ⚠️ / ❌ |

---

## NOTES & OBSERVATIONS

[Tout élément contextuel utile pour la démo : ambiance, spécialités, public cible, événements récents, etc.]

---

## VALIDATION AVANT PASSAGE À CASCADE

- [ ] Toutes les variables obligatoires sont remplies (aucune `{{` restante)
- [ ] Les couleurs sont cohérentes avec l'identité visuelle observée
- [ ] Le menu contient au minimum 3 catégories (Entrées, Plats, Desserts)
- [ ] L'ardoise est complète (plat minimum requis)
- [ ] Les données démo sont personnalisées (pas de "Marie D." générique)
- [ ] Les horaires sont réalistes et cohérents
- [ ] Les URLs (logo, hero, présentation, Google Maps) sont valides et accessibles
- [ ] {{TELEPHONE_RAW}} ne contient que des chiffres (pour href tel:)
- [ ] 3 avis clients renseignés avec initiales, textes et dates
- [ ] {{AFFICHER_SCORE_GOOGLE}} = "block" ou "none" selon disponibilité
- [ ] {{BADGE_HERO}} reflète la personnalité réelle du restaurant
- [ ] Le score prospect justifie le lancement de la démo

---

*Template version 1.0 — L'Atelier Connecté — 2026-04-19*
