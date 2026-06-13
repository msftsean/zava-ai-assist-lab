"""
Unit tests for app/config.py
=============================
Validates that the ``Settings`` configuration class correctly:

  • Loads default values for Azure Government cloud
  • Differentiates between Gov and Commercial endpoint patterns
  • Resolves the OpenAI base URL based on ``azure_cloud``

These tests override environment variables using monkeypatch so they are
safe to run without a real ``.env`` file.

Zava Lab guidance
----------------
These tests demonstrate how ``pydantic-settings`` resolves env vars.
Try modifying defaults and watching which tests break — it's a great
way to understand config-driven architecture.
"""

import pytest


# ═══════════════════════════════════════════════════════════════════════════
# Default configuration
# ═══════════════════════════════════════════════════════════════════════════


class TestDefaultConfigValues:
    """Verify the out-of-the-box defaults match Azure Gov expectations."""

    def test_default_config_values(self, monkeypatch):
        """Key defaults should be present and non-empty where appropriate."""
        # Import Settings fresh so monkeypatch env vars take effect
        from app.config import Settings

        cfg = Settings()

        # Azure Gov is the default cloud
        assert cfg.azure_cloud == "AzureUSGovernment"
        assert cfg.azure_location == "usgovvirginia"

        # OpenAI defaults
        assert cfg.azure_openai_chat_deployment == "gpt-4.1"
        assert cfg.azure_openai_embedding_deployment == "text-embedding-3-small"
        assert cfg.azure_openai_api_version == "2024-02-15-preview"

        # Search defaults
        assert cfg.azure_search_index_name == "sop-index-test"  # from test env fixture

        # Application defaults
        assert cfg.chunk_size == 500
        assert cfg.chunk_overlap == 50
        assert cfg.log_level == "DEBUG"  # overridden by conftest

    def test_postgres_dsn_format(self, monkeypatch):
        """The computed ``postgres_dsn`` should be a valid libpq string."""
        from app.config import Settings

        cfg = Settings()
        dsn = cfg.postgres_dsn

        assert "host=" in dsn
        assert "port=" in dsn
        assert "dbname=" in dsn
        assert "user=" in dsn
        assert "password=" in dsn


# ═══════════════════════════════════════════════════════════════════════════
# Government cloud
# ═══════════════════════════════════════════════════════════════════════════


class TestGovCloudConfig:
    """Ensure Gov-cloud specific endpoint derivation works."""

    def test_gov_cloud_config(self, monkeypatch):
        """When cloud=AzureUSGovernment and no explicit endpoint, derive .azure.us."""
        monkeypatch.setenv("AZURE_CLOUD", "AzureUSGovernment")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
        from app.config import Settings

        cfg = Settings()
        url = cfg.azure_openai_base_url

        # Should fall back to the .azure.us pattern
        assert ".azure.us" in url

    def test_gov_cloud_explicit_endpoint(self, monkeypatch):
        """An explicitly set endpoint should be returned as-is."""
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-resource.openai.azure.us")
        from app.config import Settings

        cfg = Settings()
        assert cfg.azure_openai_base_url == "https://my-resource.openai.azure.us"


# ═══════════════════════════════════════════════════════════════════════════
# Commercial cloud
# ═══════════════════════════════════════════════════════════════════════════


class TestCommercialCloudConfig:
    """Verify config when targeting Azure Commercial."""

    def test_commercial_cloud_config(self, monkeypatch):
        """Setting cloud to AzureCloud should yield .azure.com endpoints."""
        monkeypatch.setenv("AZURE_CLOUD", "AzureCloud")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
        from app.config import Settings

        cfg = Settings()
        url = cfg.azure_openai_base_url

        assert ".azure.com" in url

    def test_commercial_cloud_preserves_explicit_endpoint(self, monkeypatch):
        """An explicit endpoint takes precedence even in Commercial cloud."""
        monkeypatch.setenv("AZURE_CLOUD", "AzureCloud")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://custom.openai.azure.com")
        from app.config import Settings

        cfg = Settings()
        assert cfg.azure_openai_base_url == "https://custom.openai.azure.com"


# ═══════════════════════════════════════════════════════════════════════════
# OpenAI endpoint resolution
# ═══════════════════════════════════════════════════════════════════════════


class TestOpenAIEndpointResolution:
    """Test the ``azure_openai_base_url`` property edge cases."""

    def test_openai_endpoint_resolution(self, monkeypatch):
        """A trailing slash in the endpoint should be stripped."""
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-resource.openai.azure.us/")
        from app.config import Settings

        cfg = Settings()
        assert not cfg.azure_openai_base_url.endswith("/")

    def test_openai_endpoint_empty_falls_back(self, monkeypatch):
        """When endpoint is empty, fallback URL is derived from cloud type."""
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
        monkeypatch.setenv("AZURE_CLOUD", "AzureUSGovernment")
        from app.config import Settings

        cfg = Settings()
        assert cfg.azure_openai_base_url != ""
        assert "azure.us" in cfg.azure_openai_base_url
