"""
Tests unitaires — model_router.py
Vérifie la sélection des modèles selon la config et la gestion d'erreurs HTTP.
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.model_router import get_model_id, call_model


class TestGetModelId:
    """get_model_id() : retourne le bon identifiant selon le type."""

    def test_routing_model(self, sample_config):
        assert get_model_id("routing", sample_config) == "google/gemini-2.0-flash-001"

    def test_structuring_model(self, sample_config):
        assert get_model_id("structuring", sample_config) == "anthropic/claude-haiku-4.5"

    def test_code_model(self, sample_config):
        assert get_model_id("code", sample_config) == "anthropic/claude-sonnet-4.5"

    def test_analysis_model(self, sample_config):
        assert get_model_id("analysis", sample_config) == "anthropic/claude-opus-4.5"

    def test_unknown_type_returns_empty_string(self, sample_config):
        assert get_model_id("nonexistent", sample_config) == ""

    def test_empty_config_returns_empty_string(self):
        assert get_model_id("routing", {}) == ""

    def test_config_without_model_preferences(self):
        config = {"api_keys": {"openrouter_key": "sk-or-test"}}
        assert get_model_id("routing", config) == ""

    def test_no_deprecated_model_ids(self, sample_config):
        """Aucun modèle déprécié ne doit être configuré."""
        deprecated = [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "google/gemini-flash-2.0",
            "anthropic/claude-haiku-4-5",
        ]
        for model_type in ["routing", "structuring", "code", "analysis"]:
            model = get_model_id(model_type, sample_config)
            assert model not in deprecated, (
                f"Modèle déprécié '{model}' utilisé pour '{model_type}'"
            )


class TestCallModelErrors:
    """call_model() : gestion des erreurs HTTP avec messages lisibles."""

    @pytest.mark.asyncio
    async def test_http_401_message_lisible(self, db, sample_config):
        """HTTP 401 → message contient 'Clé API invalide'."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception) as exc_info:
                await call_model(
                    "google/gemini-2.0-flash-001",
                    [{"role": "user", "content": "test"}],
                    sample_config["api_keys"],
                    1, "test_step", "routing", db
                )
            
            assert "Clé API invalide" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_429_message_lisible(self, db, sample_config):
        """HTTP 429 → message contient 'Quota dépassé'."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception) as exc_info:
                await call_model(
                    "google/gemini-2.0-flash-001",
                    [{"role": "user", "content": "test"}],
                    sample_config["api_keys"],
                    1, "test_step", "routing", db
                )
            
            assert "Quota dépassé" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_404_message_lisible(self, db, sample_config):
        """HTTP 404 → message contient 'Modèle introuvable'."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Model not found"
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception) as exc_info:
                await call_model(
                    "google/gemini-invalid-model",
                    [{"role": "user", "content": "test"}],
                    sample_config["api_keys"],
                    1, "test_step", "routing", db
                )
            
            assert "Modèle introuvable" in str(exc_info.value)
            assert "gemini-invalid-model" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_message_lisible(self, db, sample_config):
        """TimeoutException → message contient 'injoignable'."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )
            
            with pytest.raises(Exception) as exc_info:
                await call_model(
                    "google/gemini-2.0-flash-001",
                    [{"role": "user", "content": "test"}],
                    sample_config["api_keys"],
                    1, "test_step", "routing", db
                )
            
            assert "injoignable" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_network_error_message_lisible(self, db, sample_config):
        """NetworkError → message contient 'injoignable'."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.NetworkError("Connection failed")
            )
            
            with pytest.raises(Exception) as exc_info:
                await call_model(
                    "google/gemini-2.0-flash-001",
                    [{"role": "user", "content": "test"}],
                    sample_config["api_keys"],
                    1, "test_step", "routing", db
                )
            
            assert "injoignable" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_500_message_contient_status_code(self, db, sample_config):
        """HTTP 500 → message contient le status code."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_response.json.side_effect = Exception("Not JSON")
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception) as exc_info:
                await call_model(
                    "google/gemini-2.0-flash-001",
                    [{"role": "user", "content": "test"}],
                    sample_config["api_keys"],
                    1, "test_step", "routing", db
                )
            
            assert "500" in str(exc_info.value)
