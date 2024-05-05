import os
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import FileResponse

from cookbook.api import schemas
from cookbook.auth import CurrentUser, get_current_user
from cookbook.db.models import Picture
from cookbook.db.session import get_db

DATA_DIR = os.environ.get("DATA_DIR", "/tmp")
MAX_FILE_SIZE = 5242880
ACCEPTED_FILE_TYPES = [
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/svg",
    "image/webp",
]
ACCEPTED_FILE_EXTENSIONS = ["png", "jpeg", "jpg", "svg", "webp"]

router = APIRouter(prefix="/pictures", tags=["pictures"])


def create_picture_path(file_extension: str) -> str:
    p = Path(DATA_DIR) / "pictures" / f"{uuid4()}{file_extension}"
    return str(p)


@router.post("/", response_model=schemas.RecipeBook)
def upload_picture(
    alt: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Picture:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename"
        )

    ext = os.path.splitext(file.filename)[1][1:]

    if (
        file.content_type not in ACCEPTED_FILE_TYPES
        and ext not in ACCEPTED_FILE_EXTENSIONS
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only jpg and png pictures allowed",
        )

    if file.size is None or file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Picture is to big",
        )

    with Image.open(file.file) as img:
        width, height = img.size

    path = create_picture_path(ext)
    picture = Picture(
        user_id=user.id,
        filename=file.filename,
        path=path,
        alt=alt,
        width=width,
        height=height,
    )
    picture.save_file(file.file)

    db.add(picture)
    db.commit()

    return picture


@router.get("/{picture_id}")
def get_picture(
    picture_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    pic = db.get(Picture, picture_id)

    if not pic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Picture not found"
        )

    return FileResponse(pic.path)
