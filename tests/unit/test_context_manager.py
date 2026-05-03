"""
Tests unitaires — context_manager.py
Vérifie la construction de l'enveloppe de contexte et l'injection dans les templates.
"""
import pytest
from backend.services.context_manager import inject_into_template, build_context_envelope


class TestInjectIntoTemplate:
    """inject_into_template() : remplace les placeholders {{...}} par les valeurs de l'enveloppe."""

    def _envelope(self, **overrides):
        base = {
            "user_input": "",
            "projet_contexte": "",
            "stack_standard": "",
            "file_list": "",
            "previous_outputs": {}
        }
        base.update(overrides)
        return base

    def test_replaces_user_input(self):
        template = "Bug décrit : {{user_input}}"
        envelope = self._envelope(user_input="login échoue avec 500")
        assert inject_into_template(template, envelope) == "Bug décrit : login échoue avec 500"

    def test_replaces_projet_contexte(self):
        template = "Projet : {{projet_contexte}}"
        envelope = self._envelope(projet_contexte="JARVIS 2.0 — FastAPI + SQLite")
        assert inject_into_template(template, envelope) == "Projet : JARVIS 2.0 — FastAPI + SQLite"

    def test_replaces_stack_standard(self):
        template = "Stack : {{stack_standard}}"
        envelope = self._envelope(stack_standard="FastAPI + SQLite + HTML vanilla")
        assert inject_into_template(template, envelope) == "Stack : FastAPI + SQLite + HTML vanilla"

    def test_replaces_previous_output(self):
        template = "Routing : {{previous_output_routing}}"
        envelope = self._envelope(previous_outputs={"routing": '{"classification": "bug_simple"}'})
        assert inject_into_template(template, envelope) == 'Routing : {"classification": "bug_simple"}'

    def test_multiple_previous_outputs(self):
        template = "A={{previous_output_step_a}} B={{previous_output_step_b}}"
        envelope = self._envelope(previous_outputs={"step_a": "out_a", "step_b": "out_b"})
        result = inject_into_template(template, envelope)
        assert result == "A=out_a B=out_b"

    def test_variables_non_substituees_nettoyees(self):
        """Les variables non substituées sont nettoyées du résultat final."""
        template = "Diagnostic : {{previous_output_diagnostic}}\nExecution : {{previous_output_execution}}"
        envelope = self._envelope(
            previous_outputs={"diagnostic": "contenu"},
            projet_contexte="", stack_standard="", user_input="",
            file_list="", graphify_report=""
        )
        result = inject_into_template(template, envelope)
        assert "{{previous_output_execution}}" not in result
        assert "contenu" in result

    def test_empty_placeholder_when_value_is_empty(self):
        template = "[{{projet_contexte}}]"
        envelope = self._envelope(projet_contexte="")
        assert inject_into_template(template, envelope) == "[]"

    def test_multiple_replacements_in_one_template(self):
        template = "Input={{user_input}} Stack={{stack_standard}}"
        envelope = self._envelope(user_input="mon input", stack_standard="FastAPI")
        assert inject_into_template(template, envelope) == "Input=mon input Stack=FastAPI"


class TestBuildContextEnvelope:
    """build_context_envelope() : construit l'enveloppe selon la config du step."""

    def _step_config(self, **overrides):
        base = {
            "context_envelope": {
                "projet_contexte_sections": [],
                "stack_standard": False,
                "previous_steps_output": [],
                "user_input": False,
                "include_file_list": False
            }
        }
        base["context_envelope"].update(overrides)
        return base

    async def test_user_input_included_when_configured(self, tmp_path):
        config = self._step_config(user_input=True)
        envelope = await build_context_envelope(config, str(tmp_path), {}, "ma demande")
        assert envelope["user_input"] == "ma demande"

    async def test_user_input_excluded_when_not_configured(self, tmp_path):
        config = self._step_config(user_input=False)
        envelope = await build_context_envelope(config, str(tmp_path), {}, "ne doit pas apparaître")
        assert envelope["user_input"] == ""

    async def test_previous_output_included_when_listed(self, tmp_path):
        config = self._step_config(previous_steps_output=["routing"])
        previous = {"routing": "bug_simple", "autre_step": "ignoré"}
        envelope = await build_context_envelope(config, str(tmp_path), previous, "")
        assert envelope["previous_outputs"]["routing"] == "bug_simple"
        assert "autre_step" not in envelope["previous_outputs"]

    async def test_previous_output_empty_when_not_listed(self, tmp_path):
        config = self._step_config(previous_steps_output=[])
        previous = {"routing": "bug_simple"}
        envelope = await build_context_envelope(config, str(tmp_path), previous, "")
        assert envelope["previous_outputs"] == {}

    async def test_stack_standard_loaded_when_file_exists(self, tmp_path):
        stack_file = tmp_path / "STACK_CODE.md"
        stack_file.write_text("FastAPI + SQLite + HTML vanilla")
        config = self._step_config(stack_standard=True)
        envelope = await build_context_envelope(config, str(tmp_path), {}, "")
        assert envelope["stack_standard"] == "FastAPI + SQLite + HTML vanilla"

    async def test_stack_standard_empty_when_file_missing(self, tmp_path):
        config = self._step_config(stack_standard=True)
        envelope = await build_context_envelope(config, str(tmp_path), {}, "")
        assert envelope["stack_standard"] == ""

    async def test_stack_standard_empty_when_not_configured(self, tmp_path):
        config = self._step_config(stack_standard=False)
        envelope = await build_context_envelope(config, str(tmp_path), {}, "")
        assert envelope["stack_standard"] == ""

    async def test_file_list_included_when_configured(self, tmp_path):
        (tmp_path / "main.py").write_text("# main")
        (tmp_path / "utils.py").write_text("# utils")
        config = self._step_config(include_file_list=True)
        envelope = await build_context_envelope(config, str(tmp_path), {}, "")
        assert envelope["file_list"] != ""

    async def test_file_list_empty_when_not_configured(self, tmp_path):
        config = self._step_config(include_file_list=False)
        envelope = await build_context_envelope(config, str(tmp_path), {}, "")
        assert envelope["file_list"] == ""

    async def test_envelope_has_all_required_keys(self, tmp_path):
        config = self._step_config()
        envelope = await build_context_envelope(config, str(tmp_path), {}, "")
        assert "projet_contexte" in envelope
        assert "stack_standard" in envelope
        assert "user_input" in envelope
        assert "file_list" in envelope
        assert "previous_outputs" in envelope


class TestWriteClotureDocsNew:
    """write_cloture_docs() : écriture PROJET_CONTEXTE.md section 8 et CHANGELOG.md."""

    def test_section_8_remplacee_correctement(self, tmp_path):
        """PROJET_CONTEXTE.md avec section 8 → section 8 remplacée."""
        from backend.services.context_manager import write_cloture_docs
        
        pc = tmp_path / "PROJET_CONTEXTE.md"
        pc.write_text(
            "# Projet\n## 8. SESSION EN COURS\nAncien contenu\n## 9. BACKLOG\n1. Tâche",
            encoding="utf-8"
        )
        
        output_json = {
            "section_8": "Nouveau contenu session",
            "changelog_line": "2026-04-16 | Test | Description | file.py"
        }
        
        write_cloture_docs(output_json, str(tmp_path))
        
        content = pc.read_text(encoding="utf-8")
        assert "Nouveau contenu session" in content
        assert "Ancien contenu" not in content
        assert "## 9. BACKLOG" in content

    def test_section_8_ajoutee_si_absente(self, tmp_path):
        """PROJET_CONTEXTE.md sans section 8 → section 8 ajoutée en fin."""
        from backend.services.context_manager import write_cloture_docs
        
        pc = tmp_path / "PROJET_CONTEXTE.md"
        pc.write_text(
            "# Projet\n## 1. IDENTITE\nContenu\n## 2. STACK\nStack",
            encoding="utf-8"
        )
        
        output_json = {"section_8": "Session ajoutée"}
        
        write_cloture_docs(output_json, str(tmp_path))
        
        content = pc.read_text(encoding="utf-8")
        assert "## 8. SESSION EN COURS" in content
        assert "Session ajoutée" in content

    def test_changelog_ligne_ajoutee_apres_entete(self, tmp_path):
        """CHANGELOG.md existe → ligne ajoutée après l'en-tête."""
        from backend.services.context_manager import write_cloture_docs
        
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# CHANGELOG\n\n| Date | Mission | Description | Fichiers |\n|------|---------|-------------|----------|\n| 2026-04-15 | T1 | D1 | f1.py |\n",
            encoding="utf-8"
        )
        
        output_json = {"changelog_line": "| 2026-04-16 | T2 | D2 | f2.py |"}
        
        write_cloture_docs(output_json, str(tmp_path))
        
        content = changelog.read_text(encoding="utf-8")
        lines = content.split('\n')
        
        # La nouvelle ligne doit être après l'en-tête (ligne 3) et avant l'ancienne (ligne 4)
        assert "| 2026-04-16 | T2 | D2 | f2.py |" in content
        assert lines.index("| 2026-04-16 | T2 | D2 | f2.py |") < lines.index("| 2026-04-15 | T1 | D1 | f1.py |")

    def test_changelog_cree_si_absent(self, tmp_path):
        """CHANGELOG.md absent → fichier créé avec la ligne."""
        from backend.services.context_manager import write_cloture_docs
        
        output_json = {"changelog_line": "| 2026-04-16 | Test | Desc | file.py |"}
        
        write_cloture_docs(output_json, str(tmp_path))
        
        changelog = tmp_path / "CHANGELOG.md"
        assert changelog.exists()
        content = changelog.read_text(encoding="utf-8")
        assert "# CHANGELOG" in content
        assert "| Date | Mission | Description | Fichiers |" in content
        assert "| 2026-04-16 | Test | Desc | file.py |" in content

    def test_erreur_silencieuse_si_fichier_absent(self, tmp_path):
        """Si PROJET_CONTEXTE.md absent → pas d'exception levée."""
        from backend.services.context_manager import write_cloture_docs
        
        output_json = {"section_8": "Contenu"}
        
        # Ne doit pas lever d'exception
        write_cloture_docs(output_json, str(tmp_path))
