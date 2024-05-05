from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from cookbook.api import schemas
from cookbook.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_refresh_token,
)
from cookbook.db.models import RefreshToken, User
from cookbook.db.session import get_db

router = APIRouter(prefix="/token", tags=["token"])


@router.post("/", response_model=schemas.Token)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> schemas.Token:
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, _ = create_access_token(user)
    refresh_token, expires = create_refresh_token(db, user)

    response.set_cookie(
        "refresh_token",
        refresh_token,
        expires=expires,
        secure=True,
        httponly=True,
    )

    return schemas.Token(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(
    response: Response,
    refresh_token: RefreshToken = Depends(get_refresh_token),
    db: Session = Depends(get_db),
) -> schemas.Token:
    user_id = refresh_token.user_id
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, _ = create_access_token(user)
    new_refresh_token, expires = create_refresh_token(db, user)

    response.set_cookie(
        "refresh_token",
        new_refresh_token,
        expires=expires,
        secure=True,
        httponly=True,
    )

    return schemas.Token(access_token=access_token, token_type="bearer")
