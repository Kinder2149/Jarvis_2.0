"""
Tests unitaires — pipeline_engine.py
Vérifie la machine à états du pipeline sans appels API réels.
La DB est une SQLite en mémoire, call_model est mocké.
"""
import pytest
from unittest.mock import AsyncMock, patch

from backend.services.pipeline_engine import (
    load_pipeline_definition,
    load_prompt_template,
    create_session,
    get_session_with_steps,
    validate_step,
    retry_step,
    execute_step,
)


# ─── Chargement des définitions ───────────────────────────────────────────────

class TestLoadPipelineDefinition:

    def test_bug_simple_existe(self):
        p = load_pipeline_definition("bug_simple")
        assert p["workflow_type"] == "bug_simple"
        assert len(p["steps"]) == 7

    def test_session_start_existe(self):
        p = load_pipeline_definition("session_start")
        assert p["workflow_type"] == "session_start"
        assert len(p["steps"]) == 1

    def test_tous_les_workflows_existent(self):
        for wf in ["session_start", "session_end", "bug_simple", "mission_complexe",
                   "nouveau_projet", "projet_existant"]:
            p = load_pipeline_definition(wf)
            assert p != {}, f"Workflow '{wf}' introuvable dans pipelines.json"

    def test_workflow_inconnu_retourne_dict_vide(self):
        assert load_pipeline_definition("nonexistent") == {}

    def test_bug_simple_steps_ont_les_champs_requis(self):
        steps = load_pipeline_definition("bug_simple")["steps"]
        for step in steps:
            for field in ["index", "name", "display_name", "model_type",
                          "prompt_key", "requires_validation", "output_type"]:
                assert field in step, f"Champ '{field}' manquant dans step {step.get('index')}"

    def test_bug_simple_step1_requires_validation(self):
        steps = load_pipeline_definition("bug_simple")["steps"]
        step1 = next(s for s in steps if s["index"] == 1)
        assert step1["requires_validation"] is True

    def test_bug_simple_step4_is_code_blocks(self):
        steps = load_pipeline_definition("bug_simple")["steps"]
        step4 = next(s for s in steps if s["name"] == "correction")
        assert step4["output_type"] == "code_blocks"

    def test_step_indices_continus(self):
        steps = load_pipeline_definition("bug_simple")["steps"]
        indices = sorted(s["index"] for s in steps)
        assert indices == list(range(len(steps)))


class TestLoadPromptTemplate:

    def test_analyse_bug_contient_user_input(self):
        t = load_prompt_template("analyse_bug")
        assert "{{user_input}}" in t

    def test_bug_diagnostic_contient_projet_contexte(self):
        t = load_prompt_template("bug_diagnostic")
        assert "{{projet_contexte}}" in t

    def test_cloture_contient_previous_outputs(self):
        t = load_prompt_template("cloture")
        assert "{{previous_output_" in t

    def test_prompt_inconnu_retourne_chaine_vide(self):
        assert load_prompt_template("nonexistent_prompt") == ""

    def test_tous_les_prompt_keys_existent(self):
        """Vérifie que chaque prompt_key référencé dans pipelines.json a un template."""
        import json
        from pathlib import Path
        pipelines_path = Path(__file__).parent.parent.parent / "backend" / "data" / "pipelines.json"
        with open(pipelines_path) as f:
            pipelines = json.load(f)

        missing = []
        for wf_name, wf in pipelines.items():
            for step in wf.get("steps", []):
                key = step["prompt_key"]
                # Ignorer les steps sans prompt_key (model_type=none)
                if key is None:
                    continue
                template = load_prompt_template(key)
                if not template:
                    missing.append(f"{wf_name}/{step['name']} → '{key}'")

        assert not missing, f"Prompt keys manquants dans prompts.json :\n" + "\n".join(missing)


# ─── Création de session ───────────────────────────────────────────────────────

class TestCreateSession:

    def test_retourne_session_avec_id(self, db, project_in_db):
        session = create_session(project_in_db["id"], "bug_simple", "bug login", db)
        assert session["id"] is not None
        assert session["status"] == "CREATED"
        assert session["current_step_index"] == 0

    def test_cree_le_bon_nombre_de_steps(self, db, project_in_db):
        create_session(project_in_db["id"], "bug_simple", "test", db)
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as n FROM pipeline_steps")
        assert cursor.fetchone()["n"] == 7

    def test_step0_a_linput_initial(self, db, project_in_db):
        create_session(project_in_db["id"], "bug_simple", "ma description de bug", db)
        cursor = db.cursor()
        cursor.execute("SELECT input_data FROM pipeline_steps WHERE step_index = 0")
        assert cursor.fetchone()["input_data"] == "ma description de bug"

    def test_autres_steps_sans_input(self, db, project_in_db):
        create_session(project_in_db["id"], "bug_simple", "test", db)
        cursor = db.cursor()
        cursor.execute("SELECT input_data FROM pipeline_steps WHERE step_index > 0")
        for row in cursor.fetchall():
            assert row["input_data"] is None

    def test_tous_les_steps_demarrent_pending(self, db, project_in_db):
        create_session(project_in_db["id"], "bug_simple", "test", db)
        cursor = db.cursor()
        cursor.execute("SELECT status FROM pipeline_steps")
        for row in cursor.fetchall():
            assert row["status"] == "PENDING"

    def test_output_type_correctement_stocke(self, db, project_in_db):
        create_session(project_in_db["id"], "bug_simple", "test", db)
        cursor = db.cursor()
        cursor.execute("SELECT output_type FROM pipeline_steps WHERE step_index = 4")
        assert cursor.fetchone()["output_type"] == "code_blocks"

    def test_requires_validation_correctement_stocke(self, db, project_in_db):
        create_session(project_in_db["id"], "bug_simple", "test", db)
        cursor = db.cursor()
        cursor.execute("SELECT requires_validation FROM pipeline_steps WHERE step_index = 1")
        assert cursor.fetchone()["requires_validation"] == 1


# ─── Récupération session + steps ─────────────────────────────────────────────

class TestGetSessionWithSteps:

    def test_retourne_session_complete(self, db, project_in_db):
        created = create_session(project_in_db["id"], "bug_simple", "test", db)
        session = get_session_with_steps(created["id"], db)
        assert session is not None
        for field in ["id", "project_id", "workflow_type", "status", "steps"]:
            assert field in session

    def test_retourne_7_steps_pour_bug_simple(self, db, project_in_db):
        created = create_session(project_in_db["id"], "bug_simple", "test", db)
        session = get_session_with_steps(created["id"], db)
        assert len(session["steps"]) == 7

    def test_retourne_none_pour_session_inconnue(self, db):
        assert get_session_with_steps(99999, db) is None

    def test_steps_ont_output_type(self, db, project_in_db):
        created = create_session(project_in_db["id"], "bug_simple", "test", db)
        session = get_session_with_steps(created["id"], db)
        for step in session["steps"]:
            assert "output_type" in step

    def test_correction_step_est_code_blocks(self, db, project_in_db):
        """Régression : dict(step_row).get() doit fonctionner (pas sqlite3.Row.get)."""
        created = create_session(project_in_db["id"], "bug_simple", "test", db)
        session = get_session_with_steps(created["id"], db)
        correction = next(s for s in session["steps"] if s["step_name"] == "correction")
        assert correction["output_type"] == "code_blocks"

    def test_requires_validation_est_bool(self, db, project_in_db):
        created = create_session(project_in_db["id"], "bug_simple", "test", db)
        session = get_session_with_steps(created["id"], db)
        for step in session["steps"]:
            assert isinstance(step["requires_validation"], bool)


# ─── Validation de step ────────────────────────────────────────────────────────

class TestValidateStep:

    def _setup_waiting_step(self, db, project_in_db, step_index=2):
        """Place un step en WAITING_VALIDATION."""
        created = create_session(project_in_db["id"], "bug_simple", "test", db)
        session_id = created["id"]
        cursor = db.cursor()

        # Marquer les steps précédents comme COMPLETED
        for i in range(step_index):
            cursor.execute(
                "UPDATE pipeline_steps SET status='COMPLETED', output_data=? WHERE session_id=? AND step_index=?",
                (f"output_step_{i}", session_id, i)
            )

        # Mettre le step courant en WAITING_VALIDATION
        cursor.execute(
            "UPDATE pipeline_steps SET status='WAITING_VALIDATION', output_data='résultat diagnostic' "
            "WHERE session_id=? AND step_index=?",
            (session_id, step_index)
        )
        cursor.execute(
            "UPDATE sessions SET status='WAITING_VALIDATION', current_step_index=? WHERE id=?",
            (step_index, session_id)
        )
        db.commit()

        cursor.execute(
            "SELECT id FROM pipeline_steps WHERE session_id=? AND step_index=?",
            (session_id, step_index)
        )
        step_id = cursor.fetchone()["id"]
        return session_id, step_id

    def test_approbation_avance_au_step_suivant(self, db, project_in_db):
        session_id, step_id = self._setup_waiting_step(db, project_in_db, step_index=2)
        result = validate_step(session_id, step_id, {"approved": True}, db)
        assert result["status"] == "validated"
        assert result["next_step"] == 3

    def test_rejet_abandonne_la_session(self, db, project_in_db):
        session_id, step_id = self._setup_waiting_step(db, project_in_db)
        result = validate_step(session_id, step_id, {"approved": False}, db)
        assert result["status"] == "aborted"

        cursor = db.cursor()
        cursor.execute("SELECT status FROM sessions WHERE id=?", (session_id,))
        assert cursor.fetchone()["status"] == "ABORTED"

    def test_output_edite_est_sauvegarde(self, db, project_in_db):
        session_id, step_id = self._setup_waiting_step(db, project_in_db)
        validate_step(session_id, step_id, {"approved": True, "edited_output": "correction manuelle"}, db)

        cursor = db.cursor()
        cursor.execute("SELECT output_data FROM pipeline_steps WHERE id=?", (step_id,))
        assert cursor.fetchone()["output_data"] == "correction manuelle"

    def test_dernier_step_complete_la_session(self, db, project_in_db):
        """session_end n'a qu'un step avec validation → doit passer à COMPLETED."""
        created = create_session(project_in_db["id"], "session_end", "test", db)
        session_id = created["id"]
        cursor = db.cursor()
        cursor.execute(
            "UPDATE pipeline_steps SET status='WAITING_VALIDATION' WHERE session_id=?",
            (session_id,)
        )
        cursor.execute(
            "SELECT id FROM pipeline_steps WHERE session_id=? AND step_index=0",
            (session_id,)
        )
        step_id = cursor.fetchone()["id"]
        db.commit()

        result = validate_step(session_id, step_id, {"approved": True}, db)
        assert result["status"] == "completed"

    def test_step_inconnu_retourne_erreur(self, db):
        result = validate_step(1, 99999, {"approved": True}, db)
        assert result["status"] == "error"


# ─── Retry de step ────────────────────────────────────────────────────────────

class TestRetryStep:

    def test_retry_remet_step_en_pending(self, db, project_in_db):
        created = create_session(project_in_db["id"], "bug_simple", "test", db)
        session_id = created["id"]
        cursor = db.cursor()
        cursor.execute(
            "UPDATE pipeline_steps SET status='FAILED', error_message='timeout', output_data='partiel' "
            "WHERE session_id=? AND step_index=2",
            (session_id,)
        )
        cursor.execute(
            "SELECT id FROM pipeline_steps WHERE session_id=? AND step_index=2",
            (session_id,)
        )
        step_id = cursor.fetchone()["id"]
        db.commit()

        result = retry_step(session_id, step_id, db)

        assert result["status"] == "ready_for_retry"
        assert result["step_index"] == 2

        cursor.execute(
            "SELECT status, error_message, output_data FROM pipeline_steps WHERE id=?",
            (step_id,)
        )
        row = cursor.fetchone()
        assert row["status"] == "PENDING"
        assert row["error_message"] is None
        assert row["output_data"] is None

    def test_retry_step_inconnu_retourne_erreur(self, db):
        result = retry_step(1, 99999, db)
        assert result["status"] == "error"


# ─── execute_step (mocké) ─────────────────────────────────────────────────────

class TestExecuteStep:
    """execute_step() avec call_model mocké pour tester la machine à états."""

    @pytest.mark.asyncio
    async def test_step_sans_validation_passe_a_auto_completed(self, db, project_in_db, sample_config):
        """Step 0 de bug_simple (routing) : pas de validation → auto_completed."""
        created = create_session(project_in_db["id"], "bug_simple", "bug login", db)

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"classification": "bug_simple", "description": "login 500"}'

            result = await execute_step(
                created["id"], 0, project_in_db["path"], db, sample_config
            )

        assert result["status"] == "auto_completed"
        assert result["next_step"] == 1
        assert result["output"] != ""

    @pytest.mark.asyncio
    async def test_step_avec_validation_passe_a_waiting(self, db, project_in_db, sample_config):
        """Step 1 de bug_simple (collecte_infos) : requires_validation → waiting_validation."""
        created = create_session(project_in_db["id"], "bug_simple", "bug login", db)
        session_id = created["id"]
        cursor = db.cursor()

        # Compléter step 0 manuellement
        cursor.execute(
            "UPDATE pipeline_steps SET status='COMPLETED', output_data=? WHERE session_id=? AND step_index=?",
            ("output_0", session_id, 0)
        )
        cursor.execute(
            "UPDATE sessions SET current_step_index=1 WHERE id=?", (session_id,)
        )
        db.commit()

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Questions : 1. Quel est le message d'erreur ? 2. Quel fichier ?"

            result = await execute_step(session_id, 1, project_in_db["path"], db, sample_config)

        assert result["status"] == "waiting_validation"
        assert "output" in result

    @pytest.mark.asyncio
    async def test_step_failed_quand_call_model_echoue(self, db, project_in_db, sample_config):
        """Un appel API en erreur doit passer le step en FAILED."""
        created = create_session(project_in_db["id"], "bug_simple", "bug test", db)

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("OpenRouter error 404: model not found")

            result = await execute_step(
                created["id"], 0, project_in_db["path"], db, sample_config
            )

        assert result["status"] == "failed"
        assert "404" in result["error"] or "not found" in result["error"]

        cursor = db.cursor()
        cursor.execute(
            "SELECT status FROM pipeline_steps WHERE session_id=? AND step_index=0",
            (created["id"],)
        )
        assert cursor.fetchone()["status"] == "FAILED"

    @pytest.mark.asyncio
    async def test_dernier_step_auto_retourne_completed(self, db, project_in_db, sample_config):
        """Le dernier step sans validation doit retourner 'completed', pas 'auto_completed'."""
        # session_start n'a qu'un step sans validation
        created = create_session(project_in_db["id"], "session_start", "test", db)

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Résumé orientation en 5 lignes."

            result = await execute_step(
                created["id"], 0, project_in_db["path"], db, sample_config
            )

        assert result["status"] == "completed"


# ─── Tests extraction JSON ────────────────────────────────────────────────────

class TestExtractJsonSafe:
    """_extract_json_safe() : extraction JSON depuis output modèle."""
    
    def test_extract_json_safe_json_pur(self):
        from backend.services.pipeline_engine import _extract_json_safe
        result = _extract_json_safe('{"section_8": "contenu", "changelog_line": "ligne"}')
        assert result["section_8"] == "contenu"
    
    def test_extract_json_safe_avec_markdown(self):
        from backend.services.pipeline_engine import _extract_json_safe
        text = '```json\n{"section_8": "contenu", "changelog_line": "ligne"}\n```'
        result = _extract_json_safe(text)
        assert result["section_8"] == "contenu"
