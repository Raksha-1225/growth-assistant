
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=200,
    )

    user_metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    user_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    sources: list[Any]
    provider: str | None
    model: str | None
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    provider: Literal["ollama", "cloud"] | None = None
    mode: Literal["auto", "qa", "essay", "artifact"] = "auto"


class ArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    kind: str
    title: str
    content: str
    created_at: datetime