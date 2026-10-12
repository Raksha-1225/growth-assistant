
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatSession, Message
from app.db.session import get_db
from app.errors import AppError
from app.schemas import MessageOut, SessionCreate, SessionOut


router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
)


async def get_session_or_404(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> ChatSession:
    session = await db.get(ChatSession, session_id)

    if not session:
        raise AppError(
            "session_not_found",
            "Session not found",
            404,
        )

    return session


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(
    body: SessionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    metadata = {
        **body.user_metadata,
        "user_agent": request.headers.get(
            "user-agent", ""
        )[:200],
    }

    session = ChatSession(
        title=body.title or "New chat",
        user_metadata=metadata,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
):
    rows = await db.scalars(
        select(ChatSession)
        .order_by(ChatSession.updated_at.desc())
        .limit(50)
    )

    return list(rows)


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await get_session_or_404(db, session_id)


@router.get(
    "/{session_id}/messages",
    response_model=list[MessageOut],
)
async def get_messages(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_session_or_404(db, session_id)

    rows = await db.scalars(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.id)
    )

    return list(rows)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    session = await get_session_or_404(
        db,
        session_id,
    )

    await db.delete(session)
    await db.commit()
