from typing import Annotated

from fastapi import Security, Depends, HTTPException, APIRouter
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from api import schemas
from auth import CurrentUser, get_current_user, Permission
from db.models import User
from db.session import get_db

router = APIRouter(
    prefix="/users",
    tags=["recipes"]
)


@router.get("/", response_model=Page[schemas.User])
def get_users(
    user: Annotated[CurrentUser, Security(get_current_user, scopes=[Permission.ADMIN])],
    db: Annotated[Session, Depends(get_db)],
) -> Page[User]:
    return paginate(db, select(User).order_by(User.username))


@router.get("/me", response_model=schemas.User)
def get_me(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    current_user = db.get(User, user.id)

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return current_user
