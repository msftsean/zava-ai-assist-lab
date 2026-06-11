"""Tests for keyless / Entra ID auth helpers in app.safety.azure_auth."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from azure.core.credentials import AzureKeyCredential

from app.safety import azure_auth


def setup_function(_):
    azure_auth.reset_credential_cache()


def test_get_credential_uses_key_when_present():
    with patch("app.config.settings") as mock_settings:
        mock_settings.azure_content_safety_api_key = "abc123"
        cred = azure_auth.get_content_safety_credential()
    assert isinstance(cred, AzureKeyCredential)
    assert cred.key == "abc123"


def test_get_credential_falls_back_to_default_when_key_empty():
    fake_default = MagicMock(name="DefaultAzureCredential")
    with patch("app.config.settings") as mock_settings, patch(
        "azure.identity.DefaultAzureCredential", return_value=fake_default
    ) as mock_dac:
        mock_settings.azure_content_safety_api_key = ""
        cred = azure_auth.get_content_safety_credential()
    assert cred is fake_default
    mock_dac.assert_called_once()


def test_get_credential_treats_whitespace_key_as_empty():
    fake_default = MagicMock(name="DefaultAzureCredential")
    with patch("app.config.settings") as mock_settings, patch(
        "azure.identity.DefaultAzureCredential", return_value=fake_default
    ):
        mock_settings.azure_content_safety_api_key = "   "
        cred = azure_auth.get_content_safety_credential()
    assert cred is fake_default


def test_default_credential_is_cached():
    fake_default = MagicMock(name="DefaultAzureCredential")
    with patch("app.config.settings") as mock_settings, patch(
        "azure.identity.DefaultAzureCredential", return_value=fake_default
    ) as mock_dac:
        mock_settings.azure_content_safety_api_key = ""
        azure_auth.get_content_safety_credential()
        azure_auth.get_content_safety_credential()
        azure_auth.get_content_safety_credential()
    assert mock_dac.call_count == 1


def test_bearer_token_helper():
    fake_token = MagicMock(token="ey-fake-jwt")
    fake_default = MagicMock()
    fake_default.get_token.return_value = fake_token
    with patch("azure.identity.DefaultAzureCredential", return_value=fake_default):
        token = azure_auth.get_content_safety_bearer_token()
    assert token == "ey-fake-jwt"
    fake_default.get_token.assert_called_once_with(
        "https://cognitiveservices.azure.com/.default"
    )
