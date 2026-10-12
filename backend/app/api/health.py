
import httpx

from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.db.session import engine


router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/health/ready")
async def ready():
    settings = get_settings()
    checks = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        checks["database"] = "ok"

    except Exception as e:
        checks["database"] = f"down: {type(e).__name__}"

    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(
                f"{settings.ollama_base_url}/api/tags"
            )
            response.raise_for_status()

        checks["ollama"] = "ok"

    except Exception as e:
        checks["ollama"] = f"down: {type(e).__name__}"

    checks["provider"] = settings.llm_provider

    is_ready = all(
        checks[name] == "ok"
        for name in ("database", "ollama")
    )

    return {
        "status": "ready" if is_ready else "degraded",
        "checks": checks,
    }
