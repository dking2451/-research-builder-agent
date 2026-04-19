from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal: Optional[sessionmaker[Session]] = None


def init_db(database_url: str) -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        return
    _engine = create_engine(database_url, pool_pre_ping=True, future=True)
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
        future=True,
        expire_on_commit=False,
    )


def get_engine():
    if _engine is None:
        raise RuntimeError("Database not initialized; call init_db() on startup")
    return _engine


def get_db_session() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized; call init_db() on startup")
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
