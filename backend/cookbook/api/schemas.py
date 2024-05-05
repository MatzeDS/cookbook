from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from cookbook.enums import IngredientUnit, RecipeUnit


class SchemaModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class Token(SchemaModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(alias="tokenType")


class UserRef(SchemaModel):
    id: str
    username: str
    full_name: str = Field(alias="fullName")


class User(UserRef):
    email: str
    disabled: str
    registered_at: datetime = Field(alias="registeredAt")


class Picture(SchemaModel):
    id: int
    filename: str
    path: str
    alt: str
    height: int
    width: int


class Tool(SchemaModel):
    tool_name: str = Field(alias="name")
    hint: str


class Ingredient(SchemaModel):
    ingredient_name: str = Field(alias="name")
    index: int
    value: float
    unit: IngredientUnit
    hint: str


class RecipeComponent(SchemaModel):
    index: int
    name: str
    description: str
    ingredients: List[Ingredient]


class RecipeStep(SchemaModel):
    index: int
    description: str
    picture: Picture
    ingredients: List[Ingredient]


class RecipeItem(SchemaModel):
    id: int
    name: str
    description: str
    published: bool

    created_by: UserRef = Field(alias="createdBy")
    created_at: datetime = Field(alias="createdAt")

    rating: int
    tags: List[str]

    cover: Optional[Picture]


class Recipe(RecipeItem):
    updated_at: datetime = Field(alias="updatedAt")
    published_at: Optional[datetime] = Field(alias="publishedAt")

    number: int
    unit: RecipeUnit

    pictures: List[Picture]
    components: List[RecipeComponent]
    steps: List[RecipeStep]
    tools: List[Tool]


class NewIngredient(SchemaModel):
    name: str
    value: float
    unit: IngredientUnit
    hint: str = ""


class NewComponent(SchemaModel):
    name: str
    description: str
    ingredients: List[NewIngredient]


class NewStep(SchemaModel):
    description: str
    picture_id: str
    ingredients: List[NewIngredient]


class NewRecipe(SchemaModel):
    name: str
    description: str
    tags: List[str]
    number: int
    unit: RecipeUnit
    cover_id: str = Field(alias="coverId")
    picture_ids: List[str] = Field(alias="pictureIds")
    components: List[NewComponent]
    steps: List[NewStep]
    tools: List[Tool]


class PatchRecipe(SchemaModel):
    name: str
    description: str
    tags: List[str]
    number: int
    unit: RecipeUnit
    cover_id: str = Field(alias="coverId")
    picture_ids: List[str] = Field(alias="pictureIds")
    components: List[NewComponent]
    steps: List[NewStep]
    tools: List[Tool]


class RecipeBookItem(SchemaModel):
    id: int
    name: str
    published: bool

    created_by: UserRef = Field(alias="createdBy")
    created_at: datetime = Field(alias="createdAt")

    tags: List[str]

    cover: Optional[Picture]


class RecipeBook(RecipeBookItem):
    updated_at: datetime = Field(alias="updatedAt")
    published_at: Optional[datetime] = Field(alias="publishedAt")

    recipes: List[Recipe]


class NewRecipeBook(SchemaModel):
    name: str
    tags: List[str]
    cover_id: str
    recipes: List[int]


class PatchRecipeBook(SchemaModel):
    name: str
    tags: List[str]
    cover_id: str
    recipes: List[int]
