import logging

from app.config import get_settings
from app.errors import AppError
from app.llm.cloud import CloudProvider
from app.llm.ollama import OllamaProvider

log = logging.getLogger("llm.factory")
PROVIDERS = {"ollama": OllamaProvider, "cloud": CloudProvider}


def get_provider(name: str):
    cls = PROVIDERS.get(name)
    if not cls:
        raise AppError("unknown_provider", f"Unknown provider '{name}'. Use: {list(PROVIDERS)}", 400)
    return cls()


def get_embedder() -> OllamaProvider:
    # Embeddings always use Ollama so stored vectors stay consistent
    # no matter which chat provider is selected.
    return OllamaProvider()


async def chat_stream(messages: list[dict], requested: str | None = None):
    """Yields {"type": "meta"|"token", ...}. Falls back only BEFORE the first token."""
    s = get_settings()
    primary = requested or s.llm_provider
    candidates = [primary]
    if s.fallback_provider and s.fallback_provider != primary:
        candidates.append(s.fallback_provider)

    for i, name in enumerate(candidates):
        provider = get_provider(name)
        started = False
        try:
            yield {"type": "meta", "provider": provider.name, "model": provider.model, "fallback": i > 0}
            async for tok in provider.stream(messages):
                started = True
                yield {"type": "token", "text": tok}
            return
        except AppError as e:
            log.warning("provider failed", extra={"extra_fields": {"provider": name, "code": e.code}})
            if started or i == len(candidates) - 1:
                raise