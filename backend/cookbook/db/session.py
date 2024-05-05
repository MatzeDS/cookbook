import os
from contextlib import contextmanager
from typing import Iterator, cast

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.requests import Request

from cookbook.db.models import Base

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_DATABASE = os.environ["DB_DATABASE"]

url = (
    f"mariadb+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_DATABASE}?charset=utf8mb4"
)

engine = create_engine(url, echo=False, pool_recycle=3600)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(engine)


@contextmanager
def get_db_session() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db


def get_db(request: Request) -> Session:
    return cast(Session, request.state.db)
