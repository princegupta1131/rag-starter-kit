"""
Prompt templates live in plain .md files next to this one so they're easy to read and edit.
Placeholders look like {{question}}.
"""
from pathlib import Path

_DIR = Path(__file__).parent


def load(name: str, **values: str) -> str:
    text = (_DIR / f"{name}.md").read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def format_history(history: list[dict], last_turns: int = 6) -> str:
    turns = history[-last_turns:]
    if not turns:
        return "(none)"
    return "\n".join(f"{t['role'].capitalize()}: {t['content']}" for t in turns)
