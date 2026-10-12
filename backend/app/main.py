
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import artifacts, chat, health, knowledge, llm, sessions
from app.config import get_settings
from app.errors import register_handlers
from app.logging_conf import setup_logging

from contextlib import asynccontextmanager

from sqlalchemy import text

from app.db.models import Base
from app.db.session import engine

settings = get_settings()
setup_logging(settings.log_level)

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("CREATE EXTENSION IF NOT EXISTS vector")
            )

            await conn.run_sync(
                Base.metadata.create_all
            )

        log.info("database ready")

    except Exception:
        log.exception(
            "database init failed; API returns 503 "
            "until DB is reachable"
        )

    yield


app = FastAPI(
    title="Lenny Growth Assistant",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_handlers(app)


@app.middleware("http")
async def request_context(
    request: Request,
    call_next,
):
    request.state.request_id = str(uuid.uuid4())[:8]

    start = time.perf_counter()
    response = await call_next(request)

    elapsed_ms = round(
        (time.perf_counter() - start) * 1000
    )

    log.info(
        "request",
        extra={
            "extra_fields": {
                "request_id": request.state.request_id,
                "path": request.url.path,
                "status": response.status_code,
                "ms": elapsed_ms,
            }
        },
    )

    response.headers["X-Request-ID"] = (
        request.state.request_id
    )

    return response


app.include_router(health.router)
app.include_router(artifacts.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(llm.router)
app.include_router(knowledge.router)
