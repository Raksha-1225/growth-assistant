import httpx
from app.errors import AppError


def map_http_error(e: Exception, label: str) -> AppError:
    """Turn httpx failures into structured, user-friendly errors."""
    if isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout)):
        return AppError("llm_unavailable", f"{label} is not reachable. Is it running?", 503)
    if isinstance(e, httpx.TimeoutException):
        return AppError("llm_timeout", f"{label} timed out. Try a smaller model or a shorter question.", 504)
    if isinstance(e, httpx.HTTPStatusError):
        return AppError("llm_error", f"{label} returned HTTP {e.response.status_code}", 502)
    return AppError("llm_unavailable", f"{label} request failed: {type(e).__name__}", 503)