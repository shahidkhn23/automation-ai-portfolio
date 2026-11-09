"""Student Rights Check - spots common traps in German contracts and letters."""

from .rules import analyse
from .report import load_kb, to_dict, to_markdown


def check(text: str, today=None) -> dict:
    """Analyse a document and return a structured, verified report."""
    return to_dict(analyse(text, today), load_kb())


__all__ = ["check", "analyse", "to_markdown"]
__version__ = "0.1.0"
