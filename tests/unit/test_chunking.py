"""Tests unitaires — service chunking (C02)."""
import re
import pytest

from backend.services.chunking import (
    estimate_tokens,
    estimate_tokens_budget,
    split_mission_by_files,
    merge_code_outputs,
    MODEL_WINDOWS,
    OUTPUT_MARGIN,
    SYSTEM_OVERHEAD,
    TOKENS_PER_CHAR,
    _DEFAULT_WINDOW,
)

HAIKU_ID = "anthropic/claude-haiku-4.5"
SONNET_ID = "anthropic/claude-sonnet-4.5"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mission_data():
    return {
        "objectif": "Refactoring des fichiers du projet",
        "contexte": "Projet FastAPI Python",
        "contraintes": ["Pas de breaking change", "Tests verts obligatoires"],
        "criteres_reussite": ["Toutes les routes répondent", "Coverage > 80%"],
    }


def _content_of_tokens(n_tokens: int) -> str:
    """Génère un contenu d'environ n_tokens tokens."""
    chars_needed = int(n_tokens / TOKENS_PER_CHAR) + 1
    return "x" * chars_needed


# ---------------------------------------------------------------------------
# TestEstimateTokens
# ---------------------------------------------------------------------------

class TestEstimateTokens:

    def test_estimate_tokens_petit_texte(self):
        """100 chars → ~28 tokens (100 / 3.5 ≈ 28)."""
        text = "a" * 100
        result = estimate_tokens(text)
        assert 25 <= result <= 32

    def test_estimate_tokens_texte_vide(self):
        assert estimate_tokens("") == 0

    def test_estimate_tokens_proportionnel(self):
        """1000 chars donne environ 10× les tokens de 100 chars."""
        t1 = estimate_tokens("a" * 100)
        t2 = estimate_tokens("a" * 1000)
        assert 9 <= t2 / t1 <= 11

    def test_estimate_tokens_minimum_un(self):
        """Un seul char doit retourner au moins 1 token."""
        assert estimate_tokens("x") >= 1


# ---------------------------------------------------------------------------
# TestEstimateTokensBudget
# ---------------------------------------------------------------------------

class TestEstimateTokensBudget:

    def test_retourne_dict_complet(self):
        result = estimate_tokens_budget("objectif simple", {"fichier.py": "print('hi')"}, HAIKU_ID)
        for key in ("model_window", "prompt_tokens_estimated", "files_tokens_estimated",
                    "system_overhead", "output_margin", "total_input_estimated",
                    "fits_in_one_call", "recommended_strategy"):
            assert key in result

    def test_single_call_petits_fichiers(self):
        """Prompt + 2 petits fichiers avec Haiku → single_call."""
        mission = "Corriger le bug de login dans le backend"
        files = {
            "backend/auth.py": "def login(): pass",
            "backend/models.py": "class User: pass",
        }
        result = estimate_tokens_budget(mission, files, HAIKU_ID)
        assert result["recommended_strategy"] == "single_call"
        assert result["fits_in_one_call"] is True

    def test_chunk_by_file_gros_fichiers(self):
        """5 fichiers larges avec Haiku → chunk_by_file.

        Chaque fichier ≈ 42 857 tokens (150 000 chars / 3.5).
        Total files ≈ 214 285 tokens > (200 000 - 8 000 - 2 000) = 190 000 → chunk_by_file.
        """
        large_content = "x" * 150_000  # ~42 857 tokens chacun
        files = {f"module_{i}.py": large_content for i in range(5)}
        result = estimate_tokens_budget("Refactoring complet", files, HAIKU_ID)
        assert result["recommended_strategy"] == "chunk_by_file"
        assert result["fits_in_one_call"] is False

    def test_model_window_correct_haiku(self):
        result = estimate_tokens_budget("", {}, HAIKU_ID)
        assert result["model_window"] == MODEL_WINDOWS[HAIKU_ID]

    def test_model_window_correct_sonnet(self):
        result = estimate_tokens_budget("", {}, SONNET_ID)
        assert result["model_window"] == MODEL_WINDOWS[SONNET_ID]

    def test_model_inconnu_utilise_defaut(self):
        """Modèle inconnu → utilise _DEFAULT_WINDOW."""
        result = estimate_tokens_budget("test", {}, "inconnu/modele-xyz")
        assert result["model_window"] == _DEFAULT_WINDOW

    def test_system_overhead_inclus(self):
        result = estimate_tokens_budget("test", {}, HAIKU_ID)
        assert result["system_overhead"] == SYSTEM_OVERHEAD

    def test_output_margin_inclus(self):
        result = estimate_tokens_budget("test", {}, HAIKU_ID)
        assert result["output_margin"] == OUTPUT_MARGIN

    def test_total_input_calcul_coherent(self):
        mission = "a" * 350  # ~100 tokens
        files = {"f.py": "b" * 350}  # ~100 tokens
        result = estimate_tokens_budget(mission, files, HAIKU_ID)
        expected = result["prompt_tokens_estimated"] + result["files_tokens_estimated"] + SYSTEM_OVERHEAD
        assert result["total_input_estimated"] == expected

    def test_fichiers_vides_single_call(self):
        """Aucun fichier ciblé → toujours single_call."""
        result = estimate_tokens_budget("objectif court", {}, HAIKU_ID)
        assert result["recommended_strategy"] == "single_call"


# ---------------------------------------------------------------------------
# TestSplitMissionByFiles
# ---------------------------------------------------------------------------

class TestSplitMissionByFiles:

    def test_3_fichiers_produit_3_sous_taches(self):
        files = {
            "frontend/index.html": "<html>...</html>",
            "frontend/app.js": "console.log('hello')",
            "backend/main.py": "from fastapi import FastAPI",
        }
        tasks = split_mission_by_files(_mission_data(), files, HAIKU_ID)
        assert len(tasks) == 3

    def test_sub_step_index_sequentiel(self):
        files = {
            "file_a.py": "code a",
            "file_b.py": "code b",
            "file_c.py": "code c",
        }
        tasks = split_mission_by_files(_mission_data(), files, HAIKU_ID)
        assert [t["sub_step_index"] for t in tasks] == [0, 1, 2]

    def test_chaque_tache_contient_file_path(self):
        files = {
            "backend/router.py": "from fastapi import APIRouter",
            "backend/service.py": "class MyService: pass",
        }
        tasks = split_mission_by_files(_mission_data(), files, HAIKU_ID)
        paths = [t["file_path"] for t in tasks]
        assert "backend/router.py" in paths
        assert "backend/service.py" in paths

    def test_chaque_tache_a_prompt_non_vide(self):
        files = {"main.py": "print('hello')"}
        tasks = split_mission_by_files(_mission_data(), files, HAIKU_ID)
        assert tasks[0]["prompt"].strip() != ""

    def test_prompt_contient_objectif(self):
        files = {"app.py": "def main(): pass"}
        tasks = split_mission_by_files(_mission_data(), files, HAIKU_ID)
        assert "Refactoring" in tasks[0]["prompt"]

    def test_prompt_contient_file_path(self):
        files = {"backend/api.py": "from fastapi import FastAPI"}
        tasks = split_mission_by_files(_mission_data(), files, HAIKU_ID)
        assert "backend/api.py" in tasks[0]["prompt"]

    def test_tokens_estimes_presents_et_positifs(self):
        files = {"app.py": "def main(): pass"}
        tasks = split_mission_by_files(_mission_data(), files, HAIKU_ID)
        assert tasks[0]["tokens_estimated"] > 0

    def test_fichier_trop_gros_leve_value_error(self):
        """1 fichier de ~1 MB avec Haiku → ValueError mission trop volumineuse.

        1 000 000 chars / 3.5 ≈ 285 714 tokens > 190 000 available → ValueError.
        """
        huge_content = "x" * 1_000_000
        files = {"gros_fichier.py": huge_content}
        with pytest.raises(ValueError, match="Mission trop volumineuse"):
            split_mission_by_files(_mission_data(), files, HAIKU_ID)

    def test_un_fichier_produit_1_sous_tache(self):
        files = {"unique.py": "print('unique')"}
        tasks = split_mission_by_files(_mission_data(), files, HAIKU_ID)
        assert len(tasks) == 1
        assert tasks[0]["sub_step_index"] == 0

    def test_clefs_requises_presentes(self):
        files = {"f.py": "code"}
        tasks = split_mission_by_files(_mission_data(), files, HAIKU_ID)
        for key in ("sub_step_index", "file_path", "prompt", "tokens_estimated"):
            assert key in tasks[0]


# ---------------------------------------------------------------------------
# TestMergeCodeOutputs
# ---------------------------------------------------------------------------

class TestMergeCodeOutputs:

    def test_3_outputs_concatenes_dans_ordre(self):
        outputs = [
            "```python\n# file_a.py\ncode_a\n```",
            "```python\n# file_b.py\ncode_b\n```",
            "```python\n# file_c.py\ncode_c\n```",
        ]
        result = merge_code_outputs(outputs)
        pos_a = result.index("file_a.py")
        pos_b = result.index("file_b.py")
        pos_c = result.index("file_c.py")
        assert pos_a < pos_b < pos_c

    def test_outputs_vides_ignores(self):
        outputs = ["```python\n# file.py\ncode\n```", "", "   "]
        result = merge_code_outputs(outputs)
        assert "file.py" in result
        assert result.count("```") == 2

    def test_sortie_parseable_apply_code_blocks(self):
        """Output merged doit être parseable par apply_code_blocks_to_project."""
        outputs = [
            "```python\n# backend/main.py\nfrom fastapi import FastAPI\n```",
            "```html\n# frontend/index.html\n<html></html>\n```",
        ]
        result = merge_code_outputs(outputs)
        blocks = re.findall(r'```[a-zA-Z]*\n(.*?)```', result, re.DOTALL)
        assert len(blocks) == 2

    def test_merge_liste_vide(self):
        assert merge_code_outputs([]) == ""

    def test_merge_single_output(self):
        out = "```python\n# app.py\ncode\n```"
        result = merge_code_outputs([out])
        assert result.strip() == out.strip()
