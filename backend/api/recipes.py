from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from api import schemas
from auth import CurrentUser, get_current_user
from db.models import Recipe
from db.session import get_db

router = APIRouter(
    prefix="/recipes",
    tags=["recipes"]
)


@router.get("/", response_model=Page[schemas.Recipe])
def get_recipes(db: Annotated[Session, Depends(get_db)]) -> Page[Recipe]:
    return paginate(db, select(Recipe).order_by(Recipe.id))


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.Recipe
)
def post_recipe(
    form_data: schemas.NewRecipe,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Recipe:
    recipe = Recipe(user_id=user.id, name=form_data.name)

    db.add(recipe)
    db.commit()

    return recipe


@router.get("/{recipe_id}", response_model=schemas.Recipe)
def get_recipe(recipe_id: int, db: Annotated[Session, Depends(get_db)]):
    recipe = db.get(Recipe, recipe_id)

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    return recipe


@router.patch(
    "/{recipe_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.Recipe,
)
def patch_recipe(
    recipe_id: int,
    form_data: schemas.PatchRecipe,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    recipe = db.get(Recipe, recipe_id)

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    if recipe.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the correct permissions to edit the recipe",
        )

    return recipe
