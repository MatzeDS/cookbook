import os
from contextlib import contextmanager
from typing import Iterator, cast

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.requests import Request

from cookbook.db.models import Base

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL, echo=False, pool_recycle=3600)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(engine)


@contextmanager
def get_db_session() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db


def get_db(request: Request) -> Session:
    return cast(Session, request.state.db)
