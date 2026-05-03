"""
Tests d'intégration — découpage automatique (chunking) dans execute_step.
call_model est mocké. Vérifie :
- Mission 3 fichiers → 3 lignes pipeline_steps sub_step_index + 1 ligne agrégat
- Output agrégé contient les 3 blocs de code
- Mission 1 petit fichier → pas de chunking, comportement inchangé
"""
import pytest
from unittest.mock import AsyncMock, patch

from backend.services.pipeline_engine import create_session, execute_step, get_session_with_steps


HAIKU_ID = "anthropic/claude-haiku-4.5"

MISSION_PROMPT_3_FICHIERS = """# MISSION CODE — Refactoring multi-fichiers

## Objectif
Ajouter un champ `email` dans les 3 fichiers du projet.

## Fichiers concernés
- `fichier_a.py` — Modèle principal
- `fichier_b.py` — Router secondaire
- `fichier_c.py` — Service helper

## Contraintes
- Pas de breaking change

## Critères de réussite
- Tests verts
"""

MISSION_PROMPT_1_FICHIER = """# MISSION CODE — Correction simple

## Objectif
Corriger un bug dans main.py

## Fichiers concernés
- `main.py` — Point d'entrée principal

## Contraintes
- Minimum de changements

## Critères de réussite
- Build passe
"""


@pytest.fixture
def sample_config():
    return {
        "api_keys": {"openrouter_key": "sk-or-test"},
        "model_preferences": {
            "code": HAIKU_ID,
            "analysis": HAIKU_ID,
            "structuring": HAIKU_ID,
            "routing": HAIKU_ID,
        },
    }


@pytest.fixture
def project_with_3_files(tmp_path):
    """Projet avec 3 fichiers ciblés dans le dossier, suffisamment grands pour déclencher le chunking."""
    project_dir = tmp_path / "projet_chunked"
    project_dir.mkdir()

    large_content = "x" * 250_000  # ~71 429 tokens chacun → 3 × 214 286 > 192 000 (seuil Haiku)

    (project_dir / "fichier_a.py").write_text(f"# fichier_a.py\n{large_content}", encoding="utf-8")
    (project_dir / "fichier_b.py").write_text(f"# fichier_b.py\n{large_content}", encoding="utf-8")
    (project_dir / "fichier_c.py").write_text(f"# fichier_c.py\n{large_content}", encoding="utf-8")

    (project_dir / "PROJET_CONTEXTE.md").write_text(
        "## 1. IDENTITE\n| Nom | Test |\n## 8. SESSION EN COURS\ntest\n",
        encoding="utf-8"
    )
    return project_dir


@pytest.fixture
def project_with_1_small_file(tmp_path):
    """Projet avec 1 petit fichier — ne déclenche pas le chunking."""
    project_dir = tmp_path / "projet_single"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def main(): pass\n", encoding="utf-8")
    (project_dir / "PROJET_CONTEXTE.md").write_text(
        "## 1. IDENTITE\n| Nom | Test |\n## 8. SESSION EN COURS\ntest\n",
        encoding="utf-8"
    )
    return project_dir


def _make_sub_output(file_path: str) -> str:
    lang = "python" if file_path.endswith(".py") else "text"
    return f"```{lang}\n# {file_path}\n# contenu modifié pour {file_path}\nprint('done')\n```"


class TestChunkingIntegration:

    @pytest.mark.asyncio
    async def test_mission_3_fichiers_produit_sous_steps(self, db, sample_config, project_with_3_files):
        """Mission avec 3 gros fichiers → 3 lignes sub_step_index + 1 ligne agrégat."""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO projects (name, path, type) VALUES (?, ?, ?)",
            ("Test Chunked", str(project_with_3_files), "web")
        )
        db.commit()
        project_id = cursor.lastrowid

        session = create_session(project_id, "code_mission", MISSION_PROMPT_3_FICHIERS, db)
        session_id = session["id"]

        sub_outputs = [
            _make_sub_output("fichier_a.py"),
            _make_sub_output("fichier_b.py"),
            _make_sub_output("fichier_c.py"),
        ]
        call_count = {"n": 0}

        async def mock_call(model_id, messages, api_keys, session_id, step_name, model_type, db_conn):
            idx = call_count["n"] % len(sub_outputs)
            call_count["n"] += 1
            return sub_outputs[idx]

        with patch("backend.services.pipeline_engine.call_model", side_effect=mock_call):
            with patch("backend.services.model_router.call_model", side_effect=mock_call):
                result = await execute_step(
                    session_id, 1, str(project_with_3_files), db, sample_config
                )

        rows = cursor.execute(
            """SELECT sub_step_index FROM pipeline_steps
               WHERE session_id = ? AND step_index = 1
               ORDER BY sub_step_index""",
            (session_id,)
        ).fetchall()

        sub_indices = [r["sub_step_index"] for r in rows]

        assert 0 in sub_indices, "sub_step_index=0 attendu"
        assert 1 in sub_indices, "sub_step_index=1 attendu"
        assert 2 in sub_indices, "sub_step_index=2 attendu"
        assert None in sub_indices, "ligne agrégat (sub_step_index=NULL) attendue"

    @pytest.mark.asyncio
    async def test_output_agrege_contient_tous_les_blocs(self, db, sample_config, project_with_3_files):
        """L'output de la ligne agrégat contient les 3 blocs de code."""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO projects (name, path, type) VALUES (?, ?, ?)",
            ("Test Aggregated", str(project_with_3_files), "web")
        )
        db.commit()
        project_id = cursor.lastrowid

        session = create_session(project_id, "code_mission", MISSION_PROMPT_3_FICHIERS, db)
        session_id = session["id"]

        sub_outputs = [
            _make_sub_output("fichier_a.py"),
            _make_sub_output("fichier_b.py"),
            _make_sub_output("fichier_c.py"),
        ]
        call_count = {"n": 0}

        async def mock_call(model_id, messages, api_keys, session_id, step_name, model_type, db_conn):
            idx = call_count["n"] % len(sub_outputs)
            call_count["n"] += 1
            return sub_outputs[idx]

        with patch("backend.services.pipeline_engine.call_model", side_effect=mock_call):
            await execute_step(session_id, 1, str(project_with_3_files), db, sample_config)

        aggregat_row = cursor.execute(
            """SELECT output_data FROM pipeline_steps
               WHERE session_id = ? AND step_index = 1 AND sub_step_index IS NULL""",
            (session_id,)
        ).fetchone()

        assert aggregat_row is not None, "Ligne agrégat manquante"
        output = aggregat_row["output_data"]
        assert output is not None and output.strip() != "", "Output agrégat vide"

        for file_path in ("fichier_a.py", "fichier_b.py", "fichier_c.py"):
            assert file_path in output, f"Bloc {file_path} absent de l'output agrégé"

    @pytest.mark.asyncio
    async def test_mission_1_petit_fichier_pas_de_chunking(self, db, sample_config, project_with_1_small_file):
        """Mission 1 petit fichier → single_call, pas de sub_step_index."""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO projects (name, path, type) VALUES (?, ?, ?)",
            ("Test Single", str(project_with_1_small_file), "web")
        )
        db.commit()
        project_id = cursor.lastrowid

        session = create_session(project_id, "code_mission", MISSION_PROMPT_1_FICHIER, db)
        session_id = session["id"]

        mock_output = "```python\n# main.py\ndef main(): print('fixed')\n```"

        with patch("backend.services.pipeline_engine.call_model",
                   new_callable=AsyncMock, return_value=mock_output):
            result = await execute_step(
                session_id, 1, str(project_with_1_small_file), db, sample_config
            )

        rows = cursor.execute(
            """SELECT sub_step_index FROM pipeline_steps
               WHERE session_id = ? AND step_index = 1""",
            (session_id,)
        ).fetchall()

        sub_indices = [r["sub_step_index"] for r in rows]
        non_null = [s for s in sub_indices if s is not None]

        assert non_null == [], f"Aucune ligne sub_step attendue pour single_call, trouvé: {non_null}"
        assert None in sub_indices, "Ligne principale (sub_step_index=NULL) attendue"

    @pytest.mark.asyncio
    async def test_mission_mono_fichier_output_inchange(self, db, sample_config, project_with_1_small_file):
        """Mission mono-fichier : output stocké normalement, status correct."""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO projects (name, path, type) VALUES (?, ?, ?)",
            ("Test Mono", str(project_with_1_small_file), "web")
        )
        db.commit()
        project_id = cursor.lastrowid

        session = create_session(project_id, "code_mission", MISSION_PROMPT_1_FICHIER, db)
        session_id = session["id"]

        mock_output = "```python\n# main.py\ndef main(): print('ok')\n```"

        with patch("backend.services.pipeline_engine.call_model",
                   new_callable=AsyncMock, return_value=mock_output):
            await execute_step(session_id, 1, str(project_with_1_small_file), db, sample_config)

        row = cursor.execute(
            """SELECT output_data, status FROM pipeline_steps
               WHERE session_id = ? AND step_index = 1 AND sub_step_index IS NULL""",
            (session_id,)
        ).fetchone()

        assert row is not None
        assert row["output_data"] == mock_output
