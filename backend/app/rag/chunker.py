import re


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Split optional YAML frontmatter (simple key: value lines) from the body."""
    meta: dict = {}
    body = raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            for line in raw[3:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip("\"'")
            body = raw[end + 4:]
    return meta, body.strip()


def chunk_text(body: str, target: int = 250, overlap: int = 40) -> list[str]:
    """Paragraph-aware chunks of ~target words, with a small overlap between chunks."""
    paras: list[str] = []
    for p in re.split(r"\n+", body):
        p = p.strip()
        if not p:
            continue
        words = p.split()
        if len(words) > target * 1.5:  # very long line: hard-split by words
            for i in range(0, len(words), target):
                paras.append(" ".join(words[i:i + target]))
        else:
            paras.append(p)

    chunks: list[str] = []
    cur: list[str] = []
    n = 0
    for p in paras:
        w = len(p.split())
        if cur and n + w > target:
            chunks.append("\n".join(cur))
            carry: list[str] = []
            cn = 0
            for prev in reversed(cur):
                pw = len(prev.split())
                if cn + pw > overlap:
                    break
                carry.insert(0, prev)
                cn += pw
            cur, n = carry, cn
        cur.append(p)
        n += w
    if cur:
        chunks.append("\n".join(cur))
    return chunks