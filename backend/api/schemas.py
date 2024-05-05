from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    email: str
    full_name: str
    disabled: bool


class RecipeBook(BaseModel):
    id: int
    name: str


class NewRecipeBook(BaseModel):
    name: str


class PatchRecipeBook(BaseModel):
    name: str


class Recipe(BaseModel):
    id: int
    name: str
    description: str
    tags: str


class NewRecipe(BaseModel):
    name: str


class PatchRecipe(BaseModel):
    name: str
