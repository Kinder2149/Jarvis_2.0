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

    def test_code_mission_existe(self):
        p = load_pipeline_definition("code_mission")
        assert p["workflow_type"] == "code_mission"
        assert len(p["steps"]) == 4

    def test_atelier_restauration_existe(self):
        p = load_pipeline_definition("atelier_restauration")
        assert p["workflow_type"] == "atelier_restauration"
        assert len(p["steps"]) == 13

    def test_seuls_deux_workflows_existent(self):
        for wf in ["code_mission", "atelier_restauration"]:
            p = load_pipeline_definition(wf)
            assert p != {}, f"Workflow '{wf}' introuvable dans pipelines.json"

    def test_workflows_obsoletes_absents(self):
        for wf in ["session_start", "session_end", "bug_simple",
                   "mission_complexe", "nouveau_projet", "projet_existant"]:
            p = load_pipeline_definition(wf)
            assert p == {}, f"Workflow obsolète '{wf}' encore présent dans pipelines.json"

    def test_workflow_inconnu_retourne_dict_vide(self):
        assert load_pipeline_definition("nonexistent") == {}

    def test_code_mission_steps_ont_les_champs_requis(self):
        steps = load_pipeline_definition("code_mission")["steps"]
        for step in steps:
            for field in ["index", "name", "display_name", "model_type",
                          "prompt_key", "requires_validation", "output_type"]:
                assert field in step, f"Champ '{field}' manquant dans step {step.get('index')}"

    def test_code_mission_verification_requires_validation(self):
        steps = load_pipeline_definition("code_mission")["steps"]
        step_verif = next(s for s in steps if s["name"] == "verification")
        assert step_verif["requires_validation"] is True

    def test_code_mission_execution_is_code_blocks(self):
        steps = load_pipeline_definition("code_mission")["steps"]
        step_exec = next(s for s in steps if s["name"] == "execution")
        assert step_exec["output_type"] == "code_blocks"

    def test_step_indices_continus(self):
        steps = load_pipeline_definition("code_mission")["steps"]
        indices = sorted(s["index"] for s in steps)
        assert indices == list(range(len(steps)))


class TestLoadPromptTemplate:

    def test_execution_non_vide(self):
        t = load_prompt_template("execution")
        assert t != ""

    def test_verification_non_vide(self):
        t = load_prompt_template("verification")
        assert t != ""

    def test_cloture_non_vide(self):
        t = load_prompt_template("cloture")
        assert t != ""

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
        session = create_session(project_in_db["id"], "code_mission", "mission login", db)
        assert session["id"] is not None
        assert session["status"] == "CREATED"
        assert session["current_step_index"] == 0

    def test_cree_le_bon_nombre_de_steps(self, db, project_in_db):
        create_session(project_in_db["id"], "code_mission", "test", db)
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as n FROM pipeline_steps")
        assert cursor.fetchone()["n"] == 4

    def test_step0_a_linput_initial(self, db, project_in_db):
        create_session(project_in_db["id"], "code_mission", "ma mission code", db)
        cursor = db.cursor()
        cursor.execute("SELECT input_data FROM pipeline_steps WHERE step_index = 0")
        assert cursor.fetchone()["input_data"] == "ma mission code"

    def test_autres_steps_sans_input(self, db, project_in_db):
        create_session(project_in_db["id"], "code_mission", "test", db)
        cursor = db.cursor()
        cursor.execute("SELECT input_data FROM pipeline_steps WHERE step_index > 0")
        for row in cursor.fetchall():
            assert row["input_data"] is None

    def test_tous_les_steps_demarrent_pending(self, db, project_in_db):
        create_session(project_in_db["id"], "code_mission", "test", db)
        cursor = db.cursor()
        cursor.execute("SELECT status FROM pipeline_steps")
        for row in cursor.fetchall():
            assert row["status"] == "PENDING"

    def test_output_type_execution_est_code_blocks(self, db, project_in_db):
        create_session(project_in_db["id"], "code_mission", "test", db)
        cursor = db.cursor()
        cursor.execute("SELECT output_type FROM pipeline_steps WHERE step_index = 1")
        assert cursor.fetchone()["output_type"] == "code_blocks"

    def test_requires_validation_verification(self, db, project_in_db):
        create_session(project_in_db["id"], "code_mission", "test", db)
        cursor = db.cursor()
        cursor.execute("SELECT requires_validation FROM pipeline_steps WHERE step_index = 2")
        assert cursor.fetchone()["requires_validation"] == 1

    def test_modele_override_persiste(self, db, project_in_db):
        create_session(project_in_db["id"], "code_mission", "test", db,
                       modele_override="anthropic/claude-sonnet-4.5")
        cursor = db.cursor()
        cursor.execute("SELECT modele_override FROM sessions WHERE id = 1")
        assert cursor.fetchone()["modele_override"] == "anthropic/claude-sonnet-4.5"


# ─── Récupération session + steps ─────────────────────────────────────────────

class TestGetSessionWithSteps:

    def test_retourne_session_complete(self, db, project_in_db):
        created = create_session(project_in_db["id"], "code_mission", "test", db)
        session = get_session_with_steps(created["id"], db)
        assert session is not None
        for field in ["id", "project_id", "workflow_type", "status", "steps"]:
            assert field in session

    def test_retourne_4_steps_pour_code_mission(self, db, project_in_db):
        created = create_session(project_in_db["id"], "code_mission", "test", db)
        session = get_session_with_steps(created["id"], db)
        assert len(session["steps"]) == 4

    def test_retourne_none_pour_session_inconnue(self, db):
        assert get_session_with_steps(99999, db) is None

    def test_steps_ont_output_type(self, db, project_in_db):
        created = create_session(project_in_db["id"], "code_mission", "test", db)
        session = get_session_with_steps(created["id"], db)
        for step in session["steps"]:
            assert "output_type" in step

    def test_execution_step_est_code_blocks(self, db, project_in_db):
        """Régression : dict(step_row).get() doit fonctionner (pas sqlite3.Row.get)."""
        created = create_session(project_in_db["id"], "code_mission", "test", db)
        session = get_session_with_steps(created["id"], db)
        execution = next(s for s in session["steps"] if s["step_name"] == "execution")
        assert execution["output_type"] == "code_blocks"

    def test_requires_validation_est_bool(self, db, project_in_db):
        created = create_session(project_in_db["id"], "code_mission", "test", db)
        session = get_session_with_steps(created["id"], db)
        for step in session["steps"]:
            assert isinstance(step["requires_validation"], bool)


# ─── Validation de step ────────────────────────────────────────────────────────

class TestValidateStep:

    def _setup_waiting_step(self, db, project_in_db, step_index=2):
        """Place le step verification (index=2) de code_mission en WAITING_VALIDATION."""
        created = create_session(project_in_db["id"], "code_mission", "test", db)
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
            "UPDATE pipeline_steps SET status='WAITING_VALIDATION', output_data='résultat vérification' "
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
        assert result["status"] == "rejected"

        cursor = db.cursor()
        cursor.execute("SELECT status FROM sessions WHERE id=?", (session_id,))
        assert cursor.fetchone()["status"] == "WAITING_VALIDATION"

    def test_output_edite_est_sauvegarde(self, db, project_in_db):
        session_id, step_id = self._setup_waiting_step(db, project_in_db)
        validate_step(session_id, step_id, {"approved": True, "edited_output": "vérification manuelle"}, db)

        cursor = db.cursor()
        cursor.execute("SELECT output_data FROM pipeline_steps WHERE id=?", (step_id,))
        assert cursor.fetchone()["output_data"] == "vérification manuelle"

    def test_step_inconnu_retourne_erreur(self, db):
        result = validate_step(1, 99999, {"approved": True}, db)
        assert result["status"] == "error"


# ─── Retry de step ────────────────────────────────────────────────────────────

class TestRetryStep:

    def test_retry_remet_step_en_pending(self, db, project_in_db):
        created = create_session(project_in_db["id"], "code_mission", "test", db)
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
    async def test_step0_sante_cadrage_auto_completed(self, db, project_in_db, sample_config):
        """Step 0 de code_mission (sante_cadrage) : model_type=none → auto_completed."""
        created = create_session(project_in_db["id"], "code_mission", "ma mission", db)

        result = await execute_step(
            created["id"], 0, project_in_db["path"], db, sample_config
        )

        assert result["status"] == "auto_completed"
        assert result["next_step"] == 1

    @pytest.mark.asyncio
    async def test_step_execution_passe_a_auto_completed(self, db, project_in_db, sample_config):
        """Step 1 de code_mission (execution) : pas de validation → auto_completed."""
        created = create_session(project_in_db["id"], "code_mission", "ma mission", db)
        session_id = created["id"]
        cursor = db.cursor()

        # Compléter step 0 manuellement
        cursor.execute(
            "UPDATE pipeline_steps SET status='COMPLETED', output_data=? WHERE session_id=? AND step_index=?",
            ("cadrage ok", session_id, 0)
        )
        cursor.execute(
            "UPDATE sessions SET current_step_index=1 WHERE id=?", (session_id,)
        )
        db.commit()

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "```python\n# backend/main.py\nprint('hello')\n```"

            result = await execute_step(session_id, 1, project_in_db["path"], db, sample_config)

        assert result["status"] == "auto_completed"
        assert result["next_step"] == 2

    @pytest.mark.asyncio
    async def test_step_verification_passe_a_waiting(self, db, project_in_db, sample_config):
        """Step 2 de code_mission (verification) : requires_validation → waiting_validation."""
        created = create_session(project_in_db["id"], "code_mission", "ma mission", db)
        session_id = created["id"]
        cursor = db.cursor()

        # Compléter steps 0 et 1
        for i in range(2):
            cursor.execute(
                "UPDATE pipeline_steps SET status='COMPLETED', output_data=? WHERE session_id=? AND step_index=?",
                (f"output_{i}", session_id, i)
            )
        cursor.execute(
            "UPDATE sessions SET current_step_index=2 WHERE id=?", (session_id,)
        )
        db.commit()

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Checklist : 1. Tester le bouton → OK"

            result = await execute_step(session_id, 2, project_in_db["path"], db, sample_config)

        assert result["status"] == "waiting_validation"

    @pytest.mark.asyncio
    async def test_step_failed_quand_call_model_echoue(self, db, project_in_db, sample_config):
        """Un appel API en erreur doit passer le step en FAILED."""
        created = create_session(project_in_db["id"], "code_mission", "ma mission", db)
        session_id = created["id"]
        cursor = db.cursor()
        cursor.execute(
            "UPDATE pipeline_steps SET status='COMPLETED', output_data='ok' WHERE session_id=? AND step_index=0",
            (session_id,)
        )
        cursor.execute("UPDATE sessions SET current_step_index=1 WHERE id=?", (session_id,))
        db.commit()

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("OpenRouter error 404: model not found")

            result = await execute_step(
                created["id"], 1, project_in_db["path"], db, sample_config
            )

        assert result["status"] == "failed"
        assert "404" in result["error"] or "not found" in result["error"]

        cursor = db.cursor()
        cursor.execute(
            "SELECT status FROM pipeline_steps WHERE session_id=? AND step_index=1",
            (created["id"],)
        )
        assert cursor.fetchone()["status"] == "FAILED"

    @pytest.mark.asyncio
    async def test_dernier_step_auto_retourne_completed(self, db, project_in_db, sample_config):
        """Le dernier step (cloture) sans validation doit retourner 'completed'."""
        created = create_session(project_in_db["id"], "code_mission", "test", db)
        session_id = created["id"]
        cursor = db.cursor()

        # Compléter les steps 0, 1, 2
        for i in range(3):
            cursor.execute(
                "UPDATE pipeline_steps SET status='COMPLETED', output_data=? WHERE session_id=? AND step_index=?",
                (f"output_{i}", session_id, i)
            )
        cursor.execute("UPDATE sessions SET current_step_index=3 WHERE id=?", (session_id,))
        db.commit()

        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"section_8": "résumé", "changelog_line": "ligne"}'

            result = await execute_step(
                created["id"], 3, project_in_db["path"], db, sample_config
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
