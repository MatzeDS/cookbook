from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from cookbook.api import schemas
from cookbook.auth import CurrentUser, get_current_user
from cookbook.db.models import (
    ComponentIngredient,
    Ingredient,
    Picture,
    Recipe,
    RecipeComponent,
    RecipeStep,
    RecipeTool,
    StepIngredient,
    Tool,
)
from cookbook.db.session import get_db
from cookbook.utils import find, utc_now

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/", response_model=Page[schemas.Recipe])
def get_recipes(db: Annotated[Session, Depends(get_db)]) -> Page[Recipe]:
    return paginate(
        db, select(Recipe).where(Recipe.published_at.is_not(None)).order_by(Recipe.id)
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Recipe)
def post_recipe(
    data: schemas.NewRecipe,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Recipe:
    cover = None
    if data.cover_id:
        cover = Picture.find(db, data.cover_id, user.id)

    pictures = []
    for picture_id in data.picture_ids:
        pictures.append(Picture.find(db, picture_id, user.id))

    components = []
    for idx, new_component in enumerate(data.components):
        ingredients = []
        for i, new_ingredient in enumerate(new_component.ingredients):
            ingredient = Ingredient.find_or_create(
                db, new_ingredient.name, new_ingredient.unit
            )

            ingredients.append(
                ComponentIngredient(
                    ingredient_name=ingredient.name,
                    index=i,
                    value=new_ingredient.value,
                    unit=new_ingredient.unit,
                    hint=new_ingredient.hint,
                )
            )

        components.append(
            RecipeComponent(
                index=idx,
                name=new_component.name,
                description=new_component.description,
                ingredients=ingredients,
            )
        )

    steps = []
    for idx, new_step in enumerate(data.steps):
        step_picture: Picture | None = None
        if new_step.picture_id:
            step_picture = Picture.find(db, new_step.picture_id, user.id)

        step_ingredients = []
        for i, new_ingredient in enumerate(new_step.ingredients):
            ingredient = Ingredient.find_or_create(
                db, new_ingredient.name, new_ingredient.unit
            )

            step_ingredients.append(
                StepIngredient(
                    ingredient_name=ingredient.name,
                    index=i,
                    value=new_ingredient.value,
                    unit=new_ingredient.unit,
                    hint=new_ingredient.hint,
                )
            )

        steps.append(
            RecipeStep(
                index=idx,
                description=new_step.description,
                picture=step_picture,
                ingredients=step_ingredients,
            )
        )

    tools = []
    for new_tool in data.tools:
        tool = Tool.find_or_create(db, new_tool.tool_name)

        tools.append(RecipeTool(tool_name=tool.name, hint=new_tool.hint))

    recipe = Recipe(
        name=data.name,
        description=data.description,
        user_id=user.id,
        tags=data.tags,
        number=data.number,
        unit=data.unit,
        cover=cover,
        pictures=pictures,
        components=components,
        steps=steps,
        tools=tools,
    )

    db.add(recipe)
    db.commit()

    return recipe


@router.get("/{recipe_id}", response_model=schemas.Recipe)
def get_recipe(
    recipe_id: int,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Recipe:
    recipe: Recipe | None = db.get(Recipe, recipe_id)

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    if not recipe.published and recipe.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Recipe not published"
        )

    return recipe


@router.patch(
    "/{recipe_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.Recipe,
)
def patch_recipe(
    recipe_id: int,
    data: schemas.PatchRecipe,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Recipe:
    recipe: Recipe | None = db.get(Recipe, recipe_id)

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    if recipe.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only edit your own recipe",
        )

    recipe.name = data.name
    recipe.description = data.description
    recipe.tags = data.tags
    recipe.number = data.number
    recipe.unit = data.unit

    if data.cover_id:
        recipe.cover = Picture.find(db, data.cover_id, user.id)
    else:
        recipe.cover = None

    pictures = []
    for picture_id in data.picture_ids:
        picture = find(recipe.pictures, lambda pic: pic.id == picture_id)

        if picture:
            pictures.append(picture)
        else:
            pictures.append(Picture.find(db, picture_id, user.id))

    recipe.pictures = pictures

    components = []
    for idx, new_component in enumerate(data.components):
        try:
            component = recipe.components[idx]
            component.name = new_component.name
            component.description = new_component.description
        except IndexError:
            component = RecipeComponent(
                index=idx,
                name=new_component.name,
                description=new_component.description,
            )

        ingredients = []
        for i, new_ingredient in enumerate(new_component.ingredients):
            ingredient = Ingredient.find_or_create(
                db, new_ingredient.name, new_ingredient.unit
            )

            try:
                component_ingredient = component.ingredients[i]
                component_ingredient.ingredient_name = ingredient.name
                component_ingredient.value = new_ingredient.value
                component_ingredient.unit = new_ingredient.unit
                component_ingredient.hint = new_ingredient.hint
            except IndexError:
                component_ingredient = ComponentIngredient(
                    ingredient_name=ingredient.name,
                    index=i,
                    value=new_ingredient.value,
                    unit=new_ingredient.unit,
                    hint=new_ingredient.hint,
                )

            ingredients.append(component_ingredient)

        component.ingredients = ingredients
        components.append(component)

    recipe.components = components

    steps = []
    for idx, new_step in enumerate(data.steps):
        try:
            step = recipe.steps[idx]
            step.description = new_step.description
        except IndexError:
            step = RecipeStep(
                index=idx,
                description=new_step.description,
            )

        if new_step.picture_id:
            step.picture = Picture.find(db, new_step.picture_id, user.id)
        else:
            step.picture = None

        step_ingredients = []
        for i, new_ingredient in enumerate(new_step.ingredients):
            ingredient = Ingredient.find_or_create(
                db, new_ingredient.name, new_ingredient.unit
            )

            try:
                step_ingredient = step.ingredients[i]
                step_ingredient.ingredient_name = ingredient.name
                step_ingredient.value = new_ingredient.value
                step_ingredient.unit = new_ingredient.unit
                step_ingredient.hint = new_ingredient.hint
            except IndexError:
                step_ingredient = StepIngredient(
                    ingredient_name=ingredient.name,
                    index=i,
                    value=new_ingredient.value,
                    unit=new_ingredient.unit,
                    hint=new_ingredient.hint,
                )

            step_ingredients.append(step_ingredient)

        steps.append(step)

    recipe.steps = steps

    tools = []
    for new_tool in data.tools:
        tool = Tool.find_or_create(db, new_tool.tool_name)

        tools.append(RecipeTool(tool_name=tool.name, hint=new_tool.hint))

    recipe.tools = tools

    recipe.updated_at = utc_now()

    db.commit()

    return recipe


@router.patch(
    "/{recipe_id}/publish",
    status_code=status.HTTP_200_OK,
    response_model=schemas.Recipe,
)
def publish_recipe(
    recipe_id: int,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Recipe:
    recipe: Recipe | None = db.get(Recipe, recipe_id)

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    if recipe.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only publish your own recipe"
        )

    if recipe.published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Recipe is already published"
        )

    recipe.published_at = utc_now()
    db.commit()

    return recipe
