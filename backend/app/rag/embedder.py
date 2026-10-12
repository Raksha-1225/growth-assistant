from app.llm.factory import get_embedder

# nomic-embed-text expects these task prefixes
DOC_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "


async def embed_documents(texts: list[str], batch: int = 16) -> list[list[float]]:
    emb = get_embedder()
    out: list[list[float]] = []
    for i in range(0, len(texts), batch):
        out += await emb.embed([DOC_PREFIX + t for t in texts[i:i + batch]])
    return out


async def embed_query(q: str) -> list[float]:
    return (await get_embedder().embed([QUERY_PREFIX + q]))[0]