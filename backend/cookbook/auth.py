import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated, Any, Dict, List, Sequence, Tuple, cast
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from starlette import status

from cookbook.db.models import RefreshToken, User
from cookbook.db.session import get_db

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

TokenData = Dict[str, Any]


class AccessToken(BaseModel):
    sub: str
    scopes: int


class Permission(str, Enum):
    ADMIN = "admin"


class CurrentUser(BaseModel):
    id: str
    permissions: List[Permission]


permission_bit_map = {
    Permission.ADMIN: 1 << 0,
}


def create_permission_bitmask(permissions: Sequence[str]) -> int:
    bitmap = 0

    for permission in permissions:
        bitmap |= permission_bit_map[cast(Permission, permission)]

    return bitmap


def create_permission_list(scopes: int) -> List[Permission]:
    return [
        permission
        for permission, bit in permission_bit_map.items()
        if bit & scopes == bit
    ]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user(db, username)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def get_user(db: Session, username: str) -> User | None:
    return (
        db.execute(select(User).where(User.username == username))
        .scalars()
        .one_or_none()
    )


def create_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> Tuple[str, datetime]:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM), expire


def create_access_token(user: User) -> Tuple[str, datetime]:
    data = {"sub": user.id, "scopes": user.permissions}

    return create_token(data, timedelta(minutes=15))


def create_refresh_token(db: Session, user: User) -> Tuple[str, datetime]:
    refresh_id = uuid4().hex
    data = {"sub": user.id, "jti": refresh_id}

    token, expires = create_token(data, timedelta(minutes=365))

    db_refresh_token = RefreshToken(id=refresh_id, expires_at=expires)
    db.add(db_refresh_token)
    db.commit()

    return token, expires


def get_token_data(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> TokenData:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = cast(
            TokenData,
            jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                leeway=timedelta(seconds=10),
            ),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


def get_access_token(
    token_data: TokenData = Depends(get_token_data),
) -> AccessToken:
    token_sub = token_data.get("sub")

    if not token_sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AccessToken.model_validate(token_data)


def get_current_user(
    security_scopes: SecurityScopes = SecurityScopes(),
    access_token: AccessToken = Depends(get_access_token),
) -> CurrentUser:
    if security_scopes.scopes:
        security_permissions = create_permission_bitmask(security_scopes.scopes)
        token_permissions = access_token.scopes

        if security_permissions & token_permissions != security_permissions:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={
                    "WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'
                },
            )

    return CurrentUser(
        id=access_token.sub,
        permissions=create_permission_list(access_token.scopes),
    )


def get_refresh_token(request: Request, db: Session = Depends(get_db)) -> RefreshToken:
    token = request.cookies.get("request_token")

    token_data = get_token_data(token)
    token_sub = token_data.get("sub")
    refresh_token_id = token_data.get("jti")

    if not token_sub or not refresh_token_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    refresh_token = db.get(RefreshToken, refresh_token_id)

    if not refresh_token:
        db.execute(delete(RefreshToken).where(RefreshToken.user_id == token_sub))

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return refresh_token
