from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk
from app.db.session import get_db

router = APIRouter(tags=["knowledge"])


@router.get("/knowledge/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    chunks = await db.scalar(select(func.count(Chunk.id)))
    episodes = await db.scalar(select(func.count(func.distinct(Chunk.source_path))))
    return {"episodes": episodes, "chunks": chunks}