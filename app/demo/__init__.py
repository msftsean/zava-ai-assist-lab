"""Guardrails Demo package.

A self-contained demonstration of Azure AI Content Safety behavior:

  * Pre-prompt input filtering (Content Safety AnalyzeText)
  * Prompt injection detection (Azure Prompt Shields, regex fallback)
  * Configurable filter profiles + custom blocklist
  * Azure OpenAI chat call gated by the safety pipeline
  * Post-response output filtering
  * In-memory audit ring buffer surfaced via REST endpoints

The package is mounted on the existing FastAPI app under the ``/demo`` prefix.
"""

from app.demo.router import router

__all__ = ["router"]
