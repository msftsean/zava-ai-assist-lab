"""FastAPI router for the guardrails demo (mounted at ``/demo``)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.demo import audit, runtime_config
from app.demo.pipeline import run_guardrails_pipeline
from app.demo.scenarios import list_scenarios
from app.safety.filter_profiles import CATEGORIES, list_profiles

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"

router = APIRouter(prefix="/demo", tags=["demo"])
router.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="demo-static")


# ── Schemas ─────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)


class ConfigUpdateRequest(BaseModel):
    profile_name: Optional[str] = None
    custom_thresholds: Optional[Dict[str, int]] = None
    blocklist: Optional[List[str]] = None
    prompt_shield_enabled: Optional[bool] = None


# ── Routes ──────────────────────────────────────────────────────────────


@router.get("/", response_class=FileResponse)
async def demo_index():
    """Serve the demo single-page UI."""
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(500, "Demo UI is missing")
    return FileResponse(str(index))


@router.get("/scenarios")
async def get_scenarios() -> Dict[str, Any]:
    return {"scenarios": list_scenarios()}


@router.get("/profiles")
async def get_profiles() -> Dict[str, Any]:
    profiles = [
        {"name": p.name, "description": p.description, "thresholds": dict(p.thresholds)}
        for p in list_profiles()
    ]
    return {"profiles": profiles, "categories": list(CATEGORIES)}


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    return runtime_config.get_config().to_dict()


@router.post("/config")
async def post_config(req: ConfigUpdateRequest) -> Dict[str, Any]:
    try:
        new_cfg = runtime_config.update_config(
            profile_name=req.profile_name,
            custom_thresholds=req.custom_thresholds,
            blocklist=req.blocklist,
            prompt_shield_enabled=req.prompt_shield_enabled,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return new_cfg.to_dict()


@router.post("/chat")
async def post_chat(req: ChatRequest) -> JSONResponse:
    trace = run_guardrails_pipeline(req.prompt)
    return JSONResponse(content=trace.to_dict())


@router.get("/audit")
async def get_audit(limit: int = 50) -> Dict[str, Any]:
    return {"entries": audit.list_entries(limit=limit), "size": audit.size()}


@router.delete("/audit")
async def delete_audit() -> Dict[str, int]:
    cleared = audit.clear()
    return {"cleared": cleared}
