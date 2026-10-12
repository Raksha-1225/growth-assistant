import re
from typing import Literal

Intent = Literal["qa", "essay", "artifact"]

ESSAY_STRONG = re.compile(r"\b(ship\s*30|atomic essay)\b", re.I)
ESSAY_WEAK = re.compile(r"\b(essay|article|blog post|newsletter)\b", re.I)
ARTIFACT_NOUN = re.compile(
    r"\b(html|css|markdown|artifact|landing page|web ?page|one-?pager|checklist|cheat ?sheet|"
    r"template|playbook|document|doc|report|table|dashboard|infographic)\b", re.I)
ACTION = re.compile(
    r"\b(create|make|build|generate|write|draft|design|turn|convert|produce|put together)\b", re.I)


def route(message: str, mode: str = "auto") -> Intent:
    if mode in ("qa", "essay", "artifact"):
        return mode  # explicit override from the UI
    if ESSAY_STRONG.search(message):
        return "essay"
    if ESSAY_WEAK.search(message) and ACTION.search(message):
        return "essay"
    if ARTIFACT_NOUN.search(message) and ACTION.search(message):
        return "artifact"
    return "qa"