import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk
from app.rag.embedder import embed_query

log = logging.getLogger("rag.retriever")


async def retrieve(db: AsyncSession, query: str, k: int, min_score: float) -> list[dict]:
    qvec = await embed_query(query)
    dist = Chunk.embedding.cosine_distance(qvec).label("dist")
    rows = (await db.execute(select(Chunk, dist).order_by(dist).limit(k))).all()

    results = [
        {
            "source_title": c.source_title,
            "source_path": c.source_path,
            "content": c.content,
            "score": round(1 - float(d), 4),
        }
        for c, d in rows
    ]
    kept = [r for r in results if r["score"] >= min_score]
    log.info(
        "retrieval",
        extra={"extra_fields": {
            "query": query[:120],
            "scores": [r["score"] for r in results],
            "kept": len(kept),
            "min_score": min_score,
        }},
    )
    return kept