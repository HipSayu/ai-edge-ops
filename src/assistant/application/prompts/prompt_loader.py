from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "templates"


class PromptLoader:
    """Loads `prompts/<name>.md` once per process (edit a prompt -> restart)."""

    @staticmethod
    @lru_cache
    def load(name: str) -> str:
        return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()

    @classmethod
    def render(cls, name: str, **values: object) -> str:
        """The prompt with each `{key}` replaced; other braces (JSON examples) are left alone."""
        text = cls.load(name)
        for key, value in values.items():
            text = text.replace(f"{{{key}}}", str(value))
        return text
