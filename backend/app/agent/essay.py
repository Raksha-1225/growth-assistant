import logging

from app.agent.skill_loader import load_skill
from app.llm.factory import chat_stream

log = logging.getLogger("agent.essay")


def _section_messages(skill: dict, idx: int, topic: str, chunks: list[dict], written: str) -> list[dict]:
    sec = skill["sections"][idx]
    rules = "\n".join(f"- {p}" for p in skill["principles"])
    ctx = "\n\n".join(
        f"[{i}] {c['source_title']}\n{c['content'][:900]}" for i, c in enumerate(chunks, 1)
    )
    system = (
        f"You are writing section {idx + 1} of {len(skill['sections'])} of a Ship 30 for 30 style essay.\n"
        f"TOPIC: {topic}\n\nWRITING RULES:\n{rules}\n\n"
        f"SOURCE EXCERPTS (use ONLY these facts, cite as [1], [2]):\n{ctx}\n\n"
        f"THIS SECTION ({sec['key']}, about {sec['words']} words): {sec['instruction']}\n\n"
        "Write ONLY this section, in Markdown. Do not repeat earlier sections. "
        "Do not add a sources list or any commentary."
    )
    tail = " ".join(written.split()[-250:])
    user = (f"ESSAY SO FAR (its ending):\n{tail}\n\nNow write the next section."
            if tail else "Write the first section now.")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


async def stream_essay(topic: str, chunks: list[dict], provider: str | None):
    """Yields the same events as chat_stream, one skill section at a time."""
    skill = load_skill("ship30")
    written = ""
    sent_meta = False
    for idx in range(len(skill["sections"])):
        section = ""
        async for ev in chat_stream(_section_messages(skill, idx, topic, chunks, written), provider):
            if ev["type"] == "meta":
                provider = ev["provider"]  # pin so one essay never mixes models
                if not sent_meta:
                    sent_meta = True
                    yield ev
                continue
            section += ev["text"]
            yield ev
        written += section.strip() + "\n\n"
        yield {"type": "token", "text": "\n\n"}
        log.info("essay section done", extra={"extra_fields": {
            "section": skill["sections"][idx]["key"], "words": len(section.split())}})