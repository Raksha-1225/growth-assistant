"""Usage (inside the container):
  python -m app.rag.ingest --limit 5          # first 5 episodes
  python -m app.rag.ingest --limit 40 --force # re-ingest (refresh)
"""
import argparse
import asyncio
from pathlib import Path

from sqlalchemy import delete, func, select, text

from app.config import get_settings
from app.db.models import Base, Chunk
from app.db.session import SessionLocal, engine
from app.errors import AppError
from app.logging_conf import setup_logging
from app.rag.chunker import chunk_text, parse_frontmatter
from app.rag.embedder import embed_documents


async def ingest(limit: int | None, force: bool) -> None:
    s = get_settings()
    setup_logging(s.log_level)
    root = Path(s.transcripts_dir)
    if not root.exists():
        print(f"Transcripts folder not found: {root}\n"
              "Clone them first: git clone --depth 1 "
              "https://github.com/ChatPRD/lennys-podcast-transcripts.git data/transcripts")
        return

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    files = sorted(root.rglob("*.md"))
    files = [f for f in files if f.name.lower() != "readme.md"]
    if limit:
        files = files[:limit]
    print(f"Found {len(files)} transcript files to process")

    total_chunks = 0
    for n, f in enumerate(files, 1):
        rel = f.relative_to(root).as_posix()
        try:
            async with SessionLocal() as db:
                exists = await db.scalar(
                    select(func.count(Chunk.id)).where(Chunk.source_path == rel)
                )
                if exists and not force:
                    print(f"[{n}/{len(files)}] skip (already ingested): {rel}")
                    continue

                meta, body = parse_frontmatter(f.read_text(encoding="utf-8", errors="ignore"))
                guest = meta.get("guest") or f.parent.name
                title = meta.get("title") or f.stem
                source_title = f"{guest}: {title}" if guest and title != guest else title

                pieces = chunk_text(body)
                if not pieces:
                    print(f"[{n}/{len(files)}] empty, skipped: {rel}")
                    continue
                vectors = await embed_documents(pieces)

                if exists:
                    await db.execute(delete(Chunk).where(Chunk.source_path == rel))
                db.add_all([
                    Chunk(source_title=source_title, source_path=rel,
                          chunk_index=i, content=c, embedding=v)
                    for i, (c, v) in enumerate(zip(pieces, vectors))
                ])
                await db.commit()
                total_chunks += len(pieces)
                print(f"[{n}/{len(files)}] {len(pieces)} chunks: {source_title[:70]}")
        except AppError as e:  # Ollama down / model missing: no point continuing
            print(f"Stopped: {e.message}")
            return
        except Exception as e:
            print(f"[{n}/{len(files)}] FAILED {rel}: {type(e).__name__}: {e}")

    async with engine.begin() as conn:
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS chunks_embedding_idx "
            "ON chunks USING hnsw (embedding vector_cosine_ops)"
        ))
    print(f"Done. Added {total_chunks} chunks.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="max episodes to process")
    ap.add_argument("--force", action="store_true", help="re-ingest existing episodes")
    args = ap.parse_args()
    asyncio.run(ingest(args.limit, args.force))