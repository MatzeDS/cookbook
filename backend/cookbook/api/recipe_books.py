from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from cookbook.api import schemas
from cookbook.auth import CurrentUser, get_current_user
from cookbook.db.models import Picture, Recipe, RecipeBook
from cookbook.db.session import get_db
from cookbook.utils import find, utc_now

router = APIRouter(prefix="/recipe_books", tags=["recipe_books"])


@router.get("/", response_model=Page[schemas.RecipeBook])
def get_recipe_books(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Page[RecipeBook]:
    return paginate(
        db,
        select(RecipeBook)
        .where(RecipeBook.published_at.is_not(None))
        .order_by(RecipeBook.id),
    )


@router.post("/", response_model=schemas.RecipeBook)
def post_recipe_book(
    data: schemas.NewRecipeBook,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RecipeBook:
    cover = None
    if data.cover_id:
        cover = Picture.find(db, data.cover_id, user.id)

    recipes = []
    for recipe_id in data.recipes:
        recipe: Recipe | None = db.get(Recipe, recipe_id)

        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe {recipe_id} not found",
            )

        if not recipe.published and recipe.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Recipe {recipe_id} not published",
            )

        recipes.append(recipe)

    book = RecipeBook(
        name=data.name, user_id=user.id, tags=data.tags, cover=cover, recipes=recipes
    )

    db.add(book)
    db.commit()

    return book


@router.get("/{book_id}", response_model=schemas.RecipeBook)
def get_recipe_book(
    book_id: int,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RecipeBook:
    book: RecipeBook | None = db.get(RecipeBook, book_id)

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe book not found"
        )

    if not book.published and book.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Recipe book not published"
        )

    return book


@router.patch("/{book_id}", response_model=schemas.RecipeBook)
def patch_recipe_book(
    book_id: int,
    data: schemas.PatchRecipeBook,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RecipeBook:
    book: RecipeBook | None = db.get(RecipeBook, book_id)

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe book not found"
        )

    if book.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only edit your own recipe books",
        )

    book.name = data.name
    book.tags = data.tags

    if data.cover_id:
        book.cover = Picture.find(db, data.cover_id, user.id)
    else:
        book.cover = None

    recipes = []
    for recipe_id in data.recipes:
        recipe: Recipe | None = find(book.recipes, lambda r: r.id == recipe_id)

        if not recipe:
            recipe = db.get(Recipe, recipe_id)

            if not recipe:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Recipe {recipe_id} not found",
                )

            if not recipe.published and recipe.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Recipe {recipe_id} not published",
                )

        recipes.append(recipe)

    book.updated_at = utc_now()

    db.commit()

    return book


@router.patch(
    "/{book_id}/publish",
    status_code=status.HTTP_200_OK,
    response_model=schemas.RecipeBook,
)
def publish_recipe(
    book_id: int,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RecipeBook:
    book: RecipeBook | None = db.get(RecipeBook, book_id)

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe book not found"
        )

    if book.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only publish your own recipe book",
        )

    if book.published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recipe book is already published",
        )

    book.published_at = utc_now()
    db.commit()

    return book
