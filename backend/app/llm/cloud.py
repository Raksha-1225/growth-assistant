import json
import logging

import httpx

from app.config import get_settings
from app.errors import AppError
from app.llm.base import map_http_error

log = logging.getLogger("llm.cloud")


class CloudProvider:
    name = "cloud"

    def __init__(self):
        s = get_settings()
        self.base = s.cloud_base_url.rstrip("/")
        self.model = s.cloud_model
        self.key = s.cloud_api_key
        self.timeout = httpx.Timeout(s.llm_timeout_seconds, connect=5)

    async def stream(self, messages: list[dict]):
        if not self.key:
            raise AppError("llm_not_configured", "CLOUD_API_KEY is not set in .env", 503)
        payload = {"model": self.model, "messages": messages, "stream": True, "temperature": 0.2}
        headers = {"Authorization": f"Bearer {self.key}"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                async with c.stream(
                    "POST", f"{self.base}/chat/completions", json=payload, headers=headers
                ) as r:
                    if r.status_code in (401, 403):
                        raise AppError("llm_auth_failed", "Cloud API key was rejected", 502)
                    if r.status_code == 429:
                        raise AppError(
                            "llm_rate_limited",
                            "Cloud free-tier rate limit hit. Wait a bit or switch to Ollama.",
                            429,
                        )
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        chunk = line[5:].strip()
                        if chunk == "[DONE]":
                            break
                        choices = json.loads(chunk).get("choices") or []
                        if choices:
                            tok = choices[0].get("delta", {}).get("content")
                            if tok:
                                yield tok
        except AppError:
            raise
        except httpx.HTTPError as e:
            raise map_http_error(e, "Cloud LLM")