from datetime import datetime
from typing import List

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    ForeignKey,
    Text,
    Table,
    Column,
    Enum,
    ForeignKeyConstraint,
    Float,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from db.date_time_utc import DateTimeUTC
from enums import IngredientUnit, RecipeUnit
from utils import utc_now


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)

    username: Mapped[str] = mapped_column(String(32), index=True, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(64))
    email: Mapped[str] = mapped_column(String(127))
    full_name: Mapped[str] = mapped_column(String(32))
    disabled: Mapped[bool] = mapped_column(Boolean)
    permissions: Mapped[int] = mapped_column(Integer)
    registered_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username})"


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)

    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("user.id"), index=True)
    user: Mapped[str] = relationship("User")
    created_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTimeUTC)

    def __repr__(self) -> str:
        return f"RefreshToken(id={self.id}, expires_at={self.expires_at})"


class Picture(Base):
    __tablename__ = "picture"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    path: Mapped[str] = mapped_column(String(255))
    alt: Mapped[str] = mapped_column(String(127))
    height: Mapped[int] = mapped_column(Integer)
    weight: Mapped[int] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"Picture(id={self.id}, path={self.path})"


class Tool(Base):
    __tablename__ = "tool"

    name: Mapped[str] = mapped_column(String(63), primary_key=True)

    def __repr__(self) -> str:
        return f"Tool(name={self.name})"


class RecipeTool(Base):
    __tablename__ = "recipe_tool",

    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipe.id"), primary_key=True)
    tool_name: Mapped[str] = mapped_column(String(63), ForeignKey("tool.name"), primary_key=True)


class Ingredient(Base):
    __tablename__ = "ingredient"

    name: Mapped[str] = mapped_column(String(63), primary_key=True)
    default_unit: Mapped[IngredientUnit] = mapped_column(Enum(IngredientUnit))

    def __repr__(self) -> str:
        return f"Ingredient(name={self.name})"


class StepIngredient(Base):
    __tablename__ = "step_ingredient"

    recipe_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_step_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingredient_name: Mapped[str] = mapped_column(
        String(63), ForeignKey("ingredient.name"), primary_key=True
    )
    index: Mapped[int] = mapped_column(Integer, primary_key=True)

    value: Mapped[float] = mapped_column()
    unit: Mapped[IngredientUnit] = mapped_column(Enum(IngredientUnit))
    hint: Mapped[str] = mapped_column(String(127))

    __table_args__ = (
        ForeignKeyConstraint(
            ["recipe_id", "recipe_step_index"],
            ["recipe_step.recipe_id", "recipe_step.index"],
        ),
    )

    def __repr__(self) -> str:
        return (
            "StepIngredient("
            f"recipe_id={self.recipe_id}, "
            f"recipe_step_index={self.recipe_step_index}, "
            f"ingredient_name={self.ingredient_name})"
            f"index={self.index}"
        )


class RecipeStep(Base):
    __tablename__ = "recipe_step"

    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipe.id"), primary_key=True
    )
    index: Mapped[int] = mapped_column(Integer, primary_key=True)

    description: Mapped[str] = mapped_column(Text)

    picture_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("picture.id"), nullable=True
    )
    picture: Mapped[Picture | None] = relationship("picture")

    ingredients: Mapped[List[StepIngredient]] = relationship("StepIngredient")

    def __repr__(self) -> str:
        return f"RecipeStep(recipe_id={self.recipe_id}, index={self.index})"


class ComponentIngredient(Base):
    __tablename__ = "component_ingredient"

    recipe_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_component_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ingredient.id"), primary_key=True
    )
    index: Mapped[int] = mapped_column(Integer, primary_key=True)

    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[IngredientUnit] = mapped_column(Enum(IngredientUnit))
    hint: Mapped[str] = mapped_column(String(127))

    __table_args__ = (
        ForeignKeyConstraint(
            ["recipe_id", "recipe_component_index"],
            ["recipe_component.recipe_id", "recipe_component.index"],
        ),
    )

    def __repr__(self) -> str:
        return (
            "ComponentIngredient("
            f"recipe_id={self.recipe_id}, "
            f"recipe_component_index={self.recipe_component_index}, "
            f"ingredient_id={self.ingredient_id})"
            f"index={self.index}"
        )


class RecipeComponent(Base):
    __tablename__ = "recipe_component"

    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipe.id"), primary_key=True
    )
    index: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(127))
    description: Mapped[str] = mapped_column(Text)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="components")
    ingredients: Mapped[List[ComponentIngredient]] = relationship("ComponentIngredient")

    def __repr__(self) -> str:
        return f"RecipeComponent(recipe_id={self.recipe_id} index={self.index})"


recipe_book_recipes = Table(
    "recipe_book_recipes",
    Base.metadata,
    Column("recipe_book_id", ForeignKey("recipe_book.id"), primary_key=True),
    Column("recipe_id", ForeignKey("recipe.id"), primary_key=True),
)


recipe_pictures = Table(
    "recipe_book_pictures",
    Base.metadata,
    Column("recipe_book_id", ForeignKey("recipe_book.id"), primary_key=True),
    Column("picture_id", ForeignKey("picture.id"), primary_key=True),
)


class Recipe(Base):
    __tablename__ = "recipe"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    public: Mapped[bool] = mapped_column(Boolean, default=False)

    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("user.id"), index=True)
    created_by: Mapped[User] = relationship("User")
    created_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)

    rating: Mapped[int] = mapped_column(Integer)
    _tags: Mapped[str] = mapped_column(String(255))

    @hybrid_property
    def tags(self) -> List[str]:
        return self._tags.split(",")

    @tags.expression
    def tags_expression(cls):
        return func.split_part(cls._tags, ",")

    number: Mapped[int] = mapped_column(Integer)
    unit: Mapped[RecipeUnit] = mapped_column(Enum(RecipeUnit))

    pictures: Mapped[List[Picture]] = relationship(secondary=recipe_pictures)

    components: Mapped[List[RecipeComponent]] = relationship(
        "RecipeComponent", back_populates="recipe"
    )

    tools: Mapped[List[Tool]] = relationship(
        secondary=recipe_tools, back_populates="recipes"
    )

    recipe_books: Mapped[List["RecipeBook"]] = relationship(
        secondary=recipe_book_recipes, back_populates="recipes"
    )

    def ingredients(self) -> List[ComponentIngredient]:
        return [
            ingredient for comp in self.components for ingredient in comp.ingredients
        ]

    def __repr__(self) -> str:
        return f"Recipe(id={self.id}, name={self.name})"


class RecipeBook(Base):
    __tablename__ = "recipe_book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(127))
    public: Mapped[bool] = mapped_column(Boolean, default=False)

    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("user.id"), index=True)
    created_by: Mapped[User] = relationship("User")
    created_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)

    tags: Mapped[str] = mapped_column(String(255))

    cover_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("picture.id", ondelete="CASCADE")
    )
    cover: Mapped[Picture] = relationship("Picture")

    recipes: Mapped[List[Recipe]] = relationship(
        secondary=recipe_book_recipes, back_populates="recipe_books"
    )

    def __repr__(self) -> str:
        return f"RecipeBook(id={self.id}, name={self.name})"
