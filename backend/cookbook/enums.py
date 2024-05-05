from enum import Enum


class IngredientUnit(str, Enum):
    MILLILITER = "ml"
    LITER = "l"
    MILLIGRAM = "mg"
    GRAM = "g"
    KILOGRAM = "kg"


class RecipeUnit(str, Enum):
    SERVING = "SERVING"
    PERSON = "PERSON"
    PIECE = "PIECE"
