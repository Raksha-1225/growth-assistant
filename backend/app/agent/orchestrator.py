SYSTEM_BASE = (
    "You are The Lenny Growth Assistant, helping product and growth teams. "
    "Be concise, practical and structured."
)

SYSTEM_GROUNDED = (
    "You are The Lenny Growth Assistant. Answer ONLY using the numbered transcript excerpts below. "
    "Cite sources inline like [1], [2]. If the excerpts do not support an answer, say clearly: "
    "'The Lenny transcripts I have don't cover this.' Never invent quotes or guests."
)


def build_messages(history: list[dict], question: str, chunks: list[dict] | None = None) -> list[dict]:
    """chunks=None  -> retrieval not wired yet (plain assistant).
    chunks=[]    -> retrieval ran but found nothing (model must say so).
    chunks=[...] -> grounded answer with citations."""
    if chunks is None:
        system = SYSTEM_BASE
    else:
        ctx = "\n\n".join(f"[{i}] {c['source_title']}\n{c['content']}" for i, c in enumerate(chunks, 1))
        system = SYSTEM_GROUNDED + "\n\nEXCERPTS:\n" + (ctx or "(none found)")
    return [{"role": "system", "content": system}, *history, {"role": "user", "content": question}]

def search_query(history: list[dict], question: str) -> str:
    """Short follow-ups get the previous user question prepended for retrieval."""
    if len(question.split()) < 8:
        prev = [m["content"] for m in history if m["role"] == "user"]
        if prev:
            return f"{prev[-1]} {question}"
    return question