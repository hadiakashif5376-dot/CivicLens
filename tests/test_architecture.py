"""Keeps the layers apart so the app stays modular as it grows."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1] / "civiclens"


def _sources(folder):
    return [(p, p.read_text()) for p in (ROOT / folder).rglob("*.py")]


def test_core_never_imports_streamlit():
    for path, text in _sources("core"):
        assert "import streamlit" not in text and "from streamlit" not in text, path


def test_pages_only_use_services():
    """Pages call services. Only bootstrap.py may reach the database layer, to connect at start-up."""
    for path, text in _sources("ui"):
        assert "sqlalchemy" not in text, path
        assert "core.models" not in text, path
        if path.name != "bootstrap.py":
            assert not re.search(r"core(\.| import )[^\n]*\bdb\b", text), path
