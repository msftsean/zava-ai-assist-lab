"""
Azure auth helpers for the safety modules
==========================================

Supports two modes:

1. **API key** — when ``AZURE_CONTENT_SAFETY_API_KEY`` is set, use it.
2. **Entra ID** — when the key is empty, use :class:`DefaultAzureCredential`
   (managed identity / az CLI / env / VS Code). Required when the resource
   has ``disableLocalAuth=true`` (common on Azure AI Foundry).

The Cognitive Services scope for token requests is
``https://cognitiveservices.azure.com/.default``. The caller (or AAD admin)
must have the ``Cognitive Services User`` role on the resource.
"""

from __future__ import annotations

import logging
from typing import Union

from azure.core.credentials import AzureKeyCredential, TokenCredential

logger = logging.getLogger(__name__)

COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"

# Module-level cache so we don't re-create the credential on every call.
_cached_token_credential: TokenCredential | None = None


def _get_default_credential() -> TokenCredential:
    """Return a cached :class:`DefaultAzureCredential` instance."""
    global _cached_token_credential
    if _cached_token_credential is None:
        from azure.identity import DefaultAzureCredential

        logger.info(
            "Content Safety API key not set — using DefaultAzureCredential "
            "(Entra ID). Ensure the caller has 'Cognitive Services User' role."
        )
        _cached_token_credential = DefaultAzureCredential()
    return _cached_token_credential


def get_content_safety_credential() -> Union[AzureKeyCredential, TokenCredential]:
    """Pick the right credential for Content Safety based on configuration.

    Returns:
        ``AzureKeyCredential`` if a key is set, otherwise
        ``DefaultAzureCredential`` for Entra ID auth.
    """
    from app.config import settings

    api_key = (settings.azure_content_safety_api_key or "").strip()
    if api_key:
        return AzureKeyCredential(api_key)
    return _get_default_credential()


def get_content_safety_bearer_token() -> str:
    """Acquire a bearer token for direct REST calls (e.g. Prompt Shields).

    Used by ``prompt_shield.scan_with_azure`` because that path makes raw
    HTTP requests rather than going through the SDK client.

    Returns:
        Access token string suitable for ``Authorization: Bearer <token>``.
    """
    cred = _get_default_credential()
    token = cred.get_token(COGNITIVE_SERVICES_SCOPE)
    return token.token


def reset_credential_cache() -> None:
    """Test hook: drop the cached credential so a fresh one is created."""
    global _cached_token_credential
    _cached_token_credential = None
