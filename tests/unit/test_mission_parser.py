"""
Tests unitaires — mission_parser.py
Vérifie le parsing de prompts mission produits par Module Réflexion.
"""
import pytest
from backend.services.mission_parser import parse_mission_prompt


PROMPT_COMPLET = """# MISSION CODE — Refonte authentification

## Objectif
Implémenter un système d'authentification JWT pour sécuriser l'API backend.
L'objectif est que chaque appel API valide un token Bearer dans le header Authorization.

## Contexte
Décision figée 2026-01-15 : utiliser JWT avec expiration 24h.
Les routes /api/projects et /api/pipelines doivent être sécurisées.

## Fichiers concernés
- `backend/routers/auth.py` — nouveau fichier d'authentification
- `backend/main.py` — ajout du middleware JWT
- `frontend/assets/js/api.js` — envoi du token dans les headers

## Contraintes
- Ne pas casser les tests existants
- Zéro dépendance externe non présente dans requirements.txt

## Critères de réussite (test manuel en français)
1. Appeler /api/projects sans token → 401
2. Appeler /api/projects avec token valide → 200
3. Token expiré → 401 avec message explicite

## Recommandation modèle
`anthropic/claude-haiku-4.5` — mission simple, 3 fichiers max
"""

PROMPT_MINIMAL = """## Objectif
Corriger le bug d'affichage dans le header.

## Fichiers concernés
- `frontend/assets/style.css` — correction CSS header
"""

PROMPT_SANS_OBJECTIF = """## Fichiers concernés
- `backend/main.py` — fichier principal
"""

PROMPT_SANS_FICHIERS = """## Objectif
Faire quelque chose d'important.
"""

PROMPT_VIDE = ""


class TestParseMissionPromptComplet:

    def test_retourne_dict(self):
        result = parse_mission_prompt(PROMPT_COMPLET)
        assert isinstance(result, dict)

    def test_titre_extrait(self):
        result = parse_mission_prompt(PROMPT_COMPLET)
        assert "Refonte authentification" in result["titre"]

    def test_objectif_non_vide(self):
        result = parse_mission_prompt(PROMPT_COMPLET)
        assert result["objectif"]
        assert "JWT" in result["objectif"]

    def test_fichiers_concernes_liste(self):
        result = parse_mission_prompt(PROMPT_COMPLET)
        assert isinstance(result["fichiers_concernes"], list)
        assert len(result["fichiers_concernes"]) == 3

    def test_fichier_path_correct(self):
        result = parse_mission_prompt(PROMPT_COMPLET)
        paths = [f["path"] for f in result["fichiers_concernes"]]
        assert "backend/routers/auth.py" in paths

    def test_contraintes_liste(self):
        result = parse_mission_prompt(PROMPT_COMPLET)
        assert isinstance(result["contraintes"], list)
        assert len(result["contraintes"]) >= 1

    def test_criteres_reussite_liste(self):
        result = parse_mission_prompt(PROMPT_COMPLET)
        assert isinstance(result["criteres_reussite"], list)
        assert len(result["criteres_reussite"]) >= 1

    def test_modele_recommande_detecte(self):
        result = parse_mission_prompt(PROMPT_COMPLET)
        assert result["modele_recommande"] == "anthropic/claude-haiku-4.5"

    def test_raw_present(self):
        result = parse_mission_prompt(PROMPT_COMPLET)
        assert result["raw"] == PROMPT_COMPLET.strip()

    def test_warnings_vide_sur_prompt_complet(self):
        result = parse_mission_prompt(PROMPT_COMPLET)
        assert result["parse_warnings"] == []


class TestParseMissionPromptMinimal:

    def test_minimal_parse_ok(self):
        result = parse_mission_prompt(PROMPT_MINIMAL)
        assert result["objectif"]
        assert len(result["fichiers_concernes"]) >= 1

    def test_contexte_vide_avec_warning(self):
        result = parse_mission_prompt(PROMPT_MINIMAL)
        assert result["contexte"] == ""
        assert any("Contexte" in w for w in result["parse_warnings"])

    def test_contraintes_vide_avec_warning(self):
        result = parse_mission_prompt(PROMPT_MINIMAL)
        assert result["contraintes"] == []
        assert any("Contraintes" in w for w in result["parse_warnings"])

    def test_criteres_vide_avec_warning(self):
        result = parse_mission_prompt(PROMPT_MINIMAL)
        assert result["criteres_reussite"] == []
        assert any("Crit" in w for w in result["parse_warnings"])

    def test_modele_none_avec_warning(self):
        result = parse_mission_prompt(PROMPT_MINIMAL)
        assert result["modele_recommande"] is None
        assert any("modèle" in w.lower() or "model" in w.lower() for w in result["parse_warnings"])


class TestParseMissionPromptErreurs:

    def test_texte_vide_leve_value_error(self):
        with pytest.raises(ValueError, match="vide"):
            parse_mission_prompt(PROMPT_VIDE)

    def test_sans_objectif_leve_value_error(self):
        with pytest.raises(ValueError, match="Objectif"):
            parse_mission_prompt(PROMPT_SANS_OBJECTIF)

    def test_sans_fichiers_leve_value_error(self):
        with pytest.raises(ValueError, match="Fichiers"):
            parse_mission_prompt(PROMPT_SANS_FICHIERS)


class TestExtractModelId:

    def test_claude_haiku_detecte(self):
        prompt = PROMPT_COMPLET
        result = parse_mission_prompt(prompt)
        assert result["modele_recommande"] == "anthropic/claude-haiku-4.5"

    def test_claude_sonnet_detecte(self):
        prompt_sonnet = PROMPT_MINIMAL + "\n## Recommandation modèle\n`anthropic/claude-sonnet-4.5` — mission complexe\n"
        result = parse_mission_prompt(prompt_sonnet)
        assert result["modele_recommande"] == "anthropic/claude-sonnet-4.5"

    def test_gemini_detecte(self):
        prompt_gemini = PROMPT_MINIMAL + "\n## Recommandation modèle\n`google/gemini-2.5-flash` — tâche légère\n"
        result = parse_mission_prompt(prompt_gemini)
        assert result["modele_recommande"] == "google/gemini-2.5-flash"
