import json
import logging

import httpx

from app.config import get_settings
from app.errors import AppError
from app.llm.base import map_http_error

log = logging.getLogger("llm.ollama")


class OllamaProvider:
    name = "ollama"

    def __init__(self):
        s = get_settings()
        self.base = s.ollama_base_url.rstrip("/")
        self.model = s.ollama_chat_model
        self.embed_model = s.ollama_embed_model
        self.timeout = httpx.Timeout(s.llm_timeout_seconds, connect=5)

    async def stream(self, messages: list[dict]):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": "10m",
            "options": {"num_ctx": 4096, "temperature": 0.2,"num_predict": 2048,},  # small ctx = less RAM
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                async with c.stream("POST", f"{self.base}/api/chat", json=payload) as r:
                    if r.status_code == 404:
                        raise AppError(
                            "model_not_found",
                            f"Model '{self.model}' not found. Run: ollama pull {self.model}",
                            503,
                        )
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if not line:
                            continue
                        data = json.loads(line)
                        if data.get("error"):
                            raise AppError("llm_error", str(data["error"]), 502)
                        tok = data.get("message", {}).get("content", "")
                        if tok:
                            yield tok
                        if data.get("done"):
                            break
        except AppError:
            raise
        except httpx.HTTPError as e:
            raise map_http_error(e, "Ollama")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                r = await c.post(
                    f"{self.base}/api/embed",
                    json={"model": self.embed_model, "input": texts},
                )
                if r.status_code == 404:
                    raise AppError(
                        "embed_model_not_found",
                        f"Run: ollama pull {self.embed_model}",
                        503,
                    )
                r.raise_for_status()
                return r.json()["embeddings"]
        except AppError:
            raise
        except httpx.HTTPError as e:
            raise map_http_error(e, "Ollama")