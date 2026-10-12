from functools import lru_cache
from pathlib import Path

SKILL_DIR = Path(__file__).parent / "skills"


@lru_cache
def load_skill(name: str) -> dict:
    text = (SKILL_DIR / f"{name}.md").read_text(encoding="utf-8")
    principles: list[str] = []
    sections: list[dict] = []
    block = None
    for line in text.splitlines():
        if line.startswith("## "):
            block = line[3:].strip().lower()
            continue
        if block == "principles" and line.startswith("- "):
            principles.append(line[2:].strip())
        elif block == "sections" and "|" in line:
            key, words, instr = [p.strip() for p in line.split("|", 2)]
            sections.append({"key": key, "words": int(words), "instruction": instr})
    return {"principles": principles, "sections": sections}