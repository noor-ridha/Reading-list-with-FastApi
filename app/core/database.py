from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True) #checks a connection is alive before handing it out, avoiding "server closed the connection" errors after idle periods.

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]: #generator dependency,FastApi calls it per-request and guarantee the session closes even on exceptions.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()