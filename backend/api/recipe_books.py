from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from api import schemas
from auth import CurrentUser, get_current_user
from db.models import RecipeBook
from db.session import get_db

router = APIRouter(
    prefix="/recipe_books",
    tags=["recipe_books"]
)


@router.get("/", response_model=Page[schemas.RecipeBook])
def get_recipe_books(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Page[RecipeBook]:
    return paginate(
        db, select(RecipeBook).where(RecipeBook.public).order_by(RecipeBook.id)
    )


@router.post("/", response_model=schemas.RecipeBook)
def post_recipe_book(
    form_data: schemas.NewRecipeBook,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RecipeBook:
    book = RecipeBook(name=form_data.name, user_id=user.id)

    db.add(book)
    db.commit()

    return book


@router.get("/{book_id}", response_model=schemas.RecipeBook)
def get_recipe_book(
    book_id: int,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    book = db.get(RecipeBook, book_id)

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe book not found"
        )

    if not book.public and book.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Recipe book not public"
        )

    return book


@router.patch("/{book_id}", response_model=schemas.RecipeBook)
def patch_recipe_book(
    book_id: int,
    form_data: schemas.PatchRecipeBook,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    book = db.get(RecipeBook, book_id)

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe book not found"
        )

    if book.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only edit your own recipe books",
        )

    return book
