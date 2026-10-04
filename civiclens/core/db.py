"""Database access. Nothing here knows about Streamlit."""
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


_engine = None
_factory = None
_url: Optional[str] = None


def normalize_url(url: str) -> str:
    """Accept the plain postgres:// and postgresql:// strings that hosting dashboards hand out."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


def configure(url: str, force: bool = False):
    """Create the engine once. Calling it again with the same URL is a cheap no-op."""
    global _engine, _factory, _url
    url = normalize_url(url)
    if _engine is not None and _url == url and not force:
        return _engine
    if _engine is not None:
        _engine.dispose()
    options = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if url in ("sqlite://", "sqlite:///:memory:"):
            options["poolclass"] = StaticPool  # one shared connection, so an in-memory database survives between calls
    else:
        options["pool_pre_ping"] = True  # hosted databases drop idle connections
    _engine = create_engine(url, **options)
    _factory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    _url = url
    return _engine


def _need_engine():
    if _engine is None:
        raise RuntimeError("Call db.configure(url) before using the database.")
    return _engine


def create_tables() -> None:
# Import models to register all tables with Base.metadata
from . import models

Base.metadata.create_all(_need_engine())


def drop_tables() -> None:
    Base.metadata.drop_all(_need_engine())


@contextmanager
def session_scope():
    """One unit of work: commit on success, roll back on any error."""
    _need_engine()
    session = _factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
