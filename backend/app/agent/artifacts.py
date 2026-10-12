import re

FENCE_RE = re.compile(r"^```[a-zA-Z]*\n(.*?)\n?```\s*$", re.S)
HTML_HINT = re.compile(r"\b(html|css|web ?page|landing page|dashboard|infographic)\b", re.I)
MAX_CHARS = 200_000


def wants_html(message: str) -> bool:
    return bool(HTML_HINT.search(message))


def word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))


def build_artifact_messages(kind: str, request: str, chunks: list[dict], history: list[dict]) -> list[dict]:
    ctx = "\n\n".join(
        f"[{i}] {c['source_title']}\n{c['content'][:900]}" for i, c in enumerate(chunks, 1)
    ) or "(none)"
    convo = "\n".join(f"{m['role'].upper()}: {m['content'][:1200]}" for m in history[-2:]) or "(none)"
    if kind == "html":
        fmt = ("Output ONE complete HTML document: <!DOCTYPE html>, <html>, a <head> with <title> and an inline "
               "<style> block, and a <body>. HTML and CSS only: no JavaScript, no external files, fonts, images "
               "or links. Make it clean, responsive and readable.")
    else:
        fmt = "Output a Markdown document. The first line must be '# Title'. Use headings, bullets and selective **bold**."
    system = (
        "You create standalone documents for a product and growth team using ONLY the material below. "
        "Never invent facts, quotes, guests or numbers. Attribute ideas to the guest by name.\n\n"
        f"TRANSCRIPT EXCERPTS:\n{ctx}\n\nRECENT CONVERSATION:\n{convo}\n\nFORMAT: {fmt}\n"
        "Output ONLY the document itself: no explanation and no code fences."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": request}]


def clean_output(raw: str, kind: str) -> tuple[str, str]:
    """Strip code fences / chatter and pull out a title."""
    text = raw.strip()
    m = FENCE_RE.match(text)
    if m:
        text = m.group(1).strip()
    if kind == "html":
        low = text.lower()
        starts = [i for i in (low.find("<!doctype"), low.find("<html")) if i != -1]
        if starts and min(starts) > 0:
            text = text[min(starts):]
        t = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
        title = t.group(1).strip() if t else "HTML artifact"
    else:
        t = re.search(r"^#\s+(.+)$", text, re.M)
        title = t.group(1).strip() if t else "Document"
    return text[:MAX_CHARS], (title or "Untitled")[:200]


def sources_markdown(chunks: list[dict]) -> str:
    titles: list[str] = []
    for c in chunks:
        if c["source_title"] not in titles:
            titles.append(c["source_title"])
    if not titles:
        return ""
    return "\n\n---\n**Sources (Lenny's Podcast transcripts)**\n" + "\n".join(f"- {t}" for t in titles)