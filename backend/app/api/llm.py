from fastapi import APIRouter
from app.config import get_settings

router = APIRouter(tags=["llm"])


@router.get("/llm/config")
async def llm_config():
    s = get_settings()
    return {
        "default": s.llm_provider,
        "fallback": s.fallback_provider or None,
        "providers": [
            {"name": "ollama", "model": s.ollama_chat_model, "configured": True},
            {"name": "cloud", "model": s.cloud_model, "configured": bool(s.cloud_api_key)},
        ],
    }