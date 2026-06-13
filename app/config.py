"""
Configuration module for the AI Assist RAG application.

Reads settings from environment variables with sensible defaults
for Azure Government cloud deployments. Uses pydantic-settings
for validation and .env file support.
"""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Azure Cloud ──────────────────────────────────────────────
    azure_cloud: str = "AzureUSGovernment"
    azure_location: str = "usgovvirginia"

    # ── Azure OpenAI ─────────────────────────────────────────────
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_chat_deployment: str = Field(
        default="gpt-4.1",
        validation_alias=AliasChoices(
            "azure_openai_chat_deployment", "azure_openai_deployment"
        ),
    )
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    # ── Azure AI Search ──────────────────────────────────────────
    azure_search_endpoint: str = ""
    azure_search_api_key: str = ""
    azure_search_index_name: str = "sop-index"

    # ── Azure Blob Storage ───────────────────────────────────────
    azure_storage_connection_string: str = ""
    azure_storage_container: str = "sop-documents"

    # ── Azure AI Content Safety ──────────────────────────────────
    azure_content_safety_endpoint: str = ""
    azure_content_safety_api_key: str = ""

    # ── PostgreSQL + pgvector ────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_assist"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    # ── Application ──────────────────────────────────────────────
    chunk_size: int = 500
    chunk_overlap: int = 50
    log_level: str = "INFO"

    # ── Guardrails Demo ──────────────────────────────────────────
    enable_prompt_shields: bool = True
    prompt_shields_api_version: str = "2024-09-01"
    demo_audit_max: int = 200
    # Output-stage Violence threshold (0-6). Set higher than the input
    # threshold so legitimate public-safety guidance — which Content Safety
    # can score up to Violence 4 — isn't falsely blocked at output, while the
    # stricter input threshold still blocks genuinely harmful requests.
    demo_output_violence_threshold: int = 5

    @property
    def azure_openai_base_url(self) -> str:
        """Return the correct Azure OpenAI base URL for the configured cloud.

        Azure Government uses `.openai.azure.us` while Azure Commercial
        uses `.openai.azure.com`.
        """
        if self.azure_openai_endpoint:
            return self.azure_openai_endpoint.rstrip("/")

        # Derive from cloud type when no explicit endpoint is set
        if self.azure_cloud == "AzureUSGovernment":
            return "https://<your-resource>.openai.azure.us"
        return "https://<your-resource>.openai.azure.com"

    @property
    def postgres_dsn(self) -> str:
        """Build a PostgreSQL connection string."""
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"dbname={self.postgres_db} user={self.postgres_user} "
            f"password={self.postgres_password}"
        )


# Singleton settings instance – import this wherever config is needed.
settings = Settings()
