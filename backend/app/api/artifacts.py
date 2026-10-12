import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Artifact
from app.db.session import get_db
from app.errors import AppError
from app.schemas import ArtifactOut

router = APIRouter(tags=["artifacts"])


@router.get("/sessions/{session_id}/artifacts", response_model=list[ArtifactOut])
async def list_artifacts(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(
        select(Artifact).where(Artifact.session_id == session_id).order_by(Artifact.created_at.desc())
    )
    return list(rows)


@router.get("/artifacts/{artifact_id}", response_model=ArtifactOut)
async def get_artifact(artifact_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    a = await db.get(Artifact, artifact_id)
    if not a:
        raise AppError("artifact_not_found", "Artifact not found", 404)
    return a