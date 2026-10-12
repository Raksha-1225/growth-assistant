import json
import logging
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.agent.artifacts import (build_artifact_messages, clean_output, sources_markdown,
                                 wants_html, word_count)
from app.agent.essay import stream_essay
from app.agent.orchestrator import build_messages, search_query
from app.agent.router import route
from app.config import get_settings
from app.db.models import Artifact, Chunk, ChatSession, Message
from app.db.session import SessionLocal
from app.errors import AppError
from app.llm.factory import chat_stream
from app.rag.retriever import retrieve
from app.schemas import ChatRequest

router = APIRouter(prefix="/sessions", tags=["chat"])
log = logging.getLogger("chat")

NO_MATCH = ("The Lenny transcripts I have don't cover this. "
            "Try rephrasing, or ask about a product or growth topic Lenny's guests discuss.")
KB_EMPTY = ("The knowledge base is empty. Run: "
            "docker compose exec backend python -m app.rag.ingest --limit 30")


def sse(obj: dict) -> str:
    return f"data: {json.dumps(obj)}\n\n"


async def save_assistant(session_id, content, sources, provider=None, model=None) -> int:
    async with SessionLocal() as db:
        msg = Message(session_id=session_id, role="assistant", content=content,
                      sources=sources, provider=provider, model=model)
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg.id


@router.post("/{session_id}/chat")
async def chat(session_id: uuid.UUID, body: ChatRequest):
    s = get_settings()
    async with SessionLocal() as db:
        session = await db.get(ChatSession, session_id)
        if not session:
            raise AppError("session_not_found", "Session not found", 404)
        rows = await db.scalars(
            select(Message).where(Message.session_id == session_id)
            .order_by(Message.id.desc()).limit(6)
        )
        history = [{"role": m.role, "content": m.content} for m in reversed(list(rows))]
        db.add(Message(session_id=session_id, role="user", content=body.message))
        if session.title == "New chat":
            session.title = body.message[:60]
        session.updated_at = func.now()
        await db.commit()

    intent = route(body.message, body.mode)
    query = search_query(history, body.message)

    async def event_stream():
        try:
            yield sse({"type": "route", "intent": intent})
            yield sse({"type": "status", "text": "Searching transcripts…"})
            async with SessionLocal() as db:
                chunks = await retrieve(db, query, s.retrieval_top_k, s.retrieval_min_score)
                kb_size = None if chunks else await db.scalar(select(func.count(Chunk.id)))

            sources = [
                {"n": i, "title": c["source_title"], "path": c["source_path"],
                 "score": c["score"], "snippet": c["content"][:220]}
                for i, c in enumerate(chunks, 1)
            ]
            yield sse({"type": "sources", "sources": sources})

            # An artifact can be built from the conversation alone; everything else needs excerpts.
            has_context = bool(chunks) or (
                intent == "artifact" and any(m["role"] == "assistant" for m in history))
            if not has_context:
                text_out = KB_EMPTY if not kb_size else NO_MATCH
                yield sse({"type": "meta", "provider": "none", "model": "none", "fallback": False})
                yield sse({"type": "token", "text": text_out})
                mid = await save_assistant(session_id, text_out, [])
                yield sse({"type": "done", "message_id": mid, "sources": []})
                return

            kind = "markdown"
            if intent == "qa":
                gen = chat_stream(build_messages(history, body.message, chunks), body.provider)
            elif intent == "essay":
                gen = stream_essay(query, chunks, body.provider)
            else:
                kind = "html" if wants_html(body.message) else "markdown"
                gen = chat_stream(
                    build_artifact_messages(kind, body.message, chunks, history), body.provider)

            yield sse({"type": "status", "text": "Writing…" if intent != "qa" else "Thinking…"})
            parts: list[str] = []
            meta: dict = {}
            async for ev in gen:
                if ev["type"] == "meta":
                    meta = ev
                    yield sse(ev)
                else:
                    parts.append(ev["text"])
                    # QA streams into the chat bubble; artifacts stream into the viewer
                    yield sse(ev if intent == "qa" else {"type": "artifact_delta", "text": ev["text"]})

            raw = "".join(parts).strip()
            if len(raw) < 20:
                raise AppError("empty_response", "The model returned an empty answer", 502)

            if intent == "qa":
                mid = await save_assistant(session_id, raw, sources,
                                           meta.get("provider"), meta.get("model"))
                yield sse({"type": "done", "message_id": mid, "sources": sources})
                return

            content, title = clean_output(raw, kind)
            words = word_count(content)
            if kind == "markdown":
                content += sources_markdown(chunks)
            async with SessionLocal() as db:
                art = Artifact(session_id=session_id, kind=kind, title=title, content=content)
                db.add(art)
                await db.commit()
                await db.refresh(art)

            detail = f"{kind}, ~{words} words" if intent == "essay" else kind
            summary = f"I created **{title}** ({detail}). It's open in the viewer."
            yield sse({"type": "token", "text": summary})
            mid = await save_assistant(session_id, summary, sources,
                                       meta.get("provider"), meta.get("model"))
            yield sse({"type": "artifact", "artifact": {
                "id": str(art.id), "kind": kind, "title": title, "content": content,
                "created_at": art.created_at.isoformat()}})
            yield sse({"type": "done", "message_id": mid, "sources": sources})
        except AppError as e:
            yield sse({"type": "error", "code": e.code, "message": e.message})
        except SQLAlchemyError:
            log.exception("db failure during chat")
            yield sse({"type": "error", "code": "database_unavailable",
                       "message": "Database is unavailable, try again shortly"})
        except Exception:
            log.exception("chat stream failed")
            yield sse({"type": "error", "code": "internal_error", "message": "Something went wrong"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )