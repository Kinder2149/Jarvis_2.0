"""
Tests unitaires — file_service.py
Vérifie le rollback atomique de apply_files() et la sécurité des chemins.
"""
import pytest
from pathlib import Path
from backend.services.file_service import apply_files


class TestApplyFilesNominal:
    """apply_files() : cas nominal avec 2 fichiers."""

    def test_deux_fichiers_ecrits_correctement(self, tmp_path):
        """2 fichiers écrits → contenu correct après apply."""
        changes = [
            {"path": str(tmp_path / "file1.py"), "content": "# file 1\nprint('hello')"},
            {"path": str(tmp_path / "file2.py"), "content": "# file 2\nprint('world')"},
        ]
        
        result = apply_files(changes)
        
        assert result is True
        assert (tmp_path / "file1.py").read_text(encoding="utf-8") == "# file 1\nprint('hello')"
        assert (tmp_path / "file2.py").read_text(encoding="utf-8") == "# file 2\nprint('world')"

    def test_fichier_existant_ecrase(self, tmp_path):
        """Fichier existant → écrasé avec nouveau contenu."""
        file_path = tmp_path / "existing.py"
        file_path.write_text("ancien contenu", encoding="utf-8")
        
        changes = [{"path": str(file_path), "content": "nouveau contenu"}]
        result = apply_files(changes)
        
        assert result is True
        assert file_path.read_text(encoding="utf-8") == "nouveau contenu"

    def test_dossiers_parents_crees_automatiquement(self, tmp_path):
        """Dossiers parents absents → créés automatiquement."""
        nested_path = tmp_path / "backend" / "routes" / "auth.py"
        changes = [{"path": str(nested_path), "content": "# auth"}]
        
        result = apply_files(changes)
        
        assert result is True
        assert nested_path.exists()
        assert nested_path.read_text(encoding="utf-8") == "# auth"


class TestApplyFilesRollbackPhase2:
    """apply_files() : rollback phase 2 (écriture tmp échoue)."""

    def test_ecriture_tmp_echoue_aucun_fichier_cree(self, tmp_path):
        """Si écriture tmp échoue → exception levée."""
        # Test simplifié : chemin invalide force l'échec
        changes = [
            {"path": str(tmp_path / "file1.py"), "content": "ok"},
            {"path": str(tmp_path / "\x00invalid"), "content": "fail"},  # Caractère null invalide
        ]
        
        with pytest.raises(Exception):
            apply_files(changes)
        
        # Vérifier qu'aucun fichier n'a été créé
        assert not (tmp_path / "file1.py").exists()


class TestApplyFilesRollbackPhase3:
    """apply_files() : rollback phase 3 (rename échoue)."""

    def test_rename_echoue_fichiers_restaures(self, tmp_path):
        """Si rename échoue → rollback tenté."""
        from unittest.mock import patch
        
        # Créer 2 fichiers existants
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("original 1", encoding="utf-8")
        file2.write_text("original 2", encoding="utf-8")
        
        changes = [
            {"path": str(file1), "content": "modifié 1"},
            {"path": str(file2), "content": "modifié 2"},
        ]
        
        # Simuler échec rename avec mock
        original_replace = Path.replace
        call_count = [0]
        
        def mock_replace(self, target):
            call_count[0] += 1
            if call_count[0] == 2:  # Échoue au 2ème rename
                raise PermissionError("Simulated error")
            return original_replace(self, target)
        
        with patch.object(Path, 'replace', mock_replace):
            with pytest.raises(Exception):
                apply_files(changes)
        
        # Vérifier que file1 est restauré à son état d'origine
        assert file1.read_text(encoding="utf-8") == "original 1"

    def test_rollback_message_clair(self, tmp_path):
        """Exception levée contient 'Rollback effectué'."""
        from unittest.mock import patch
        
        file1 = tmp_path / "file1.py"
        file1.write_text("original", encoding="utf-8")
        
        changes = [{"path": str(file1), "content": "modifié"}]
        
        # Simuler échec rename
        with patch.object(Path, 'replace', side_effect=PermissionError("Simulated")):
            with pytest.raises(Exception) as exc_info:
                apply_files(changes)
            
            assert "Rollback effectué" in str(exc_info.value)


class TestApplyFilesSecurity:
    """apply_files() : sécurité des chemins."""

    def test_chemin_avec_double_point_leve_exception(self, tmp_path):
        """Chemin avec '..' → exception levée AVANT toute écriture."""
        changes = [{"path": str(tmp_path / ".." / "malicious.py"), "content": "hack"}]
        
        with pytest.raises(Exception) as exc_info:
            apply_files(changes)
        
        assert "Vérification échouée" in str(exc_info.value) or "non sécurisé" in str(exc_info.value)
        assert not (tmp_path.parent / "malicious.py").exists()

    def test_nom_fichier_vide_leve_exception(self, tmp_path):
        """Nom de fichier vide → exception levée."""
        # Utiliser un chemin qui se termine par un séparateur
        changes = [{"path": str(tmp_path) + "\\", "content": "test"}]
        
        with pytest.raises(Exception):
            apply_files(changes)
