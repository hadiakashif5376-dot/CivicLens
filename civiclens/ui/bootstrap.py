"""Start-up: read settings from Streamlit secrets or environment variables, connect, create tables."""
import os

import streamlit as st

from ..core import config, db, models  # noqa: F401  (importing models registers every table)
from ..core.seed import seed


def _settings() -> config.Settings:
    values = dict(os.environ)
    try:
        for key, value in st.secrets.items():  # raises when there is no secrets file, which is fine locally
            if isinstance(value, (str, int, float, bool)):
                values[key] = value
    except Exception:
        pass
    return config.from_mapping(values)


@st.cache_resource(show_spinner="Starting CivicLens...")
def _prepare(database_url: str, officer_email: str, officer_password: str) -> bool:
    db.configure(database_url)
    with db.session_scope() as s:
        seed(s, officer_email, officer_password)
    return True


def init() -> config.Settings:
    settings = _settings()
    db.configure(settings.database_url)  # cheap when already configured
    db.create_tables()  # runs on every start, so new tables like ai_analyses get created
    _prepare(settings.database_url, settings.officer_email, settings.officer_password)
    return settings
