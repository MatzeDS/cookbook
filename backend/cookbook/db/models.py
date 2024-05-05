import os.path
import shutil
from datetime import datetime
from typing import BinaryIO, List, Optional
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from starlette import status

from cookbook.db.date_time_utc import DateTimeUTC
from cookbook.enums import IngredientUnit, RecipeUnit
from cookbook.utils import utc_now


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(36), default=uuid4, primary_key=True)

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

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), index=True)
    user: Mapped["User"] = relationship("User")
    created_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTimeUTC)

    def __repr__(self) -> str:
        return f"RefreshToken(id={self.id}, expires_at={self.expires_at})"


class Picture(Base):
    __tablename__ = "picture"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), index=True)
    user: Mapped["User"] = relationship("User")

    filename: Mapped[str] = mapped_column(String(127))
    uploaded_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    path: Mapped[str] = mapped_column(String(255))
    alt: Mapped[str] = mapped_column(String(127))
    height: Mapped[int] = mapped_column(Integer)
    width: Mapped[int] = mapped_column(Integer)

    def save_file(self, file: BinaryIO) -> None:
        with open(self.path, "wb") as f:
            shutil.copyfileobj(file, f)

    def delete_file(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)

    @classmethod
    def find(cls, db: Session, picture_id: str, user_id: str) -> "Picture":
        picture: Picture | None = db.get(Picture, picture_id)

        if not picture:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Picture {picture_id} not found",
            )

        if picture.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Access to picture {picture_id} not allowed",
            )

        picture.used = True

        return picture

    def __repr__(self) -> str:
        return f"Picture(id={self.id}, path={self.path})"


class Tool(Base):
    __tablename__ = "tool"

    name: Mapped[str] = mapped_column(String(63), primary_key=True)

    @classmethod
    def find_or_create(cls, db: Session, name: str) -> "Tool":
        tool: Tool | None = db.get(Tool, name)

        if not tool:
            tool = Tool(name=name)
            db.add(tool)

        return tool

    def __repr__(self) -> str:
        return f"Tool(name={self.name})"


class RecipeTool(Base):
    __tablename__ = "recipe_tool"

    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True
    )
    tool_name: Mapped[str] = mapped_column(
        String(63), ForeignKey("tool.name"), primary_key=True
    )
    hint: Mapped[str] = mapped_column(String(127))

    def __repr__(self) -> str:
        return f"Tool(recipe_id={self.recipe_id}, tool_name={self.tool_name})"


class Ingredient(Base):
    __tablename__ = "ingredient"

    name: Mapped[str] = mapped_column(String(63), primary_key=True)
    default_unit: Mapped[IngredientUnit] = mapped_column(Enum(IngredientUnit))

    @classmethod
    def find_or_create(
        cls, db: Session, name: str, unit: IngredientUnit
    ) -> "Ingredient":
        ingredient: Ingredient | None = db.get(Ingredient, name)

        if not ingredient:
            ingredient = Ingredient(name=name, default_unit=unit)
            db.add(ingredient)

        return ingredient

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
            ondelete="CASCADE",
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
        Integer, ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True
    )
    index: Mapped[int] = mapped_column(Integer, primary_key=True)

    description: Mapped[str] = mapped_column(Text)

    picture_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("picture.id"), nullable=True
    )
    picture: Mapped[Optional["Picture"]] = relationship(
        "Picture",
    )

    ingredients: Mapped[List["StepIngredient"]] = relationship(
        "StepIngredient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="steps",
    )

    def __repr__(self) -> str:
        return f"RecipeStep(recipe_id={self.recipe_id}, index={self.index})"


class ComponentIngredient(Base):
    __tablename__ = "component_ingredient"

    recipe_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_component_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingredient_name: Mapped[str] = mapped_column(
        String(63), ForeignKey("ingredient.name"), primary_key=True
    )
    index: Mapped[int] = mapped_column(Integer, primary_key=True)

    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[IngredientUnit] = mapped_column(Enum(IngredientUnit))
    hint: Mapped[str] = mapped_column(String(127))

    __table_args__ = (
        ForeignKeyConstraint(
            ["recipe_id", "recipe_component_index"],
            ["recipe_component.recipe_id", "recipe_component.index"],
            ondelete="CASCADE",
        ),
    )

    def __repr__(self) -> str:
        return (
            "ComponentIngredient("
            f"recipe_id={self.recipe_id}, "
            f"recipe_component_index={self.recipe_component_index}, "
            f"ingredient_name={self.ingredient_name})"
            f"index={self.index}"
        )


class RecipeComponent(Base):
    __tablename__ = "recipe_component"

    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True
    )
    index: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(127))
    description: Mapped[str] = mapped_column(Text)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="components")

    ingredients: Mapped[List["ComponentIngredient"]] = relationship(
        "ComponentIngredient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"RecipeComponent(recipe_id={self.recipe_id} index={self.index})"


recipe_book_recipes = Table(
    "recipe_book_recipes",
    Base.metadata,
    Column(
        "recipe_book_id",
        Integer,
        ForeignKey("recipe_book.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "recipe_id",
        Integer,
        ForeignKey("recipe.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


recipe_pictures = Table(
    "recipe_pictures",
    Base.metadata,
    Column(
        "recipe_id",
        Integer,
        ForeignKey("recipe.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "picture_id",
        String(36),
        ForeignKey("picture.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class RecipeAssessment(Base):
    __tablename__ = "assessment"

    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipe.id"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer)


class Recipe(Base):
    __tablename__ = "recipe"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), index=True)
    created_by: Mapped["User"] = relationship("User")
    created_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC, nullable=True, default=None
    )

    rating: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)

    number: Mapped[int] = mapped_column(Integer)
    unit: Mapped["RecipeUnit"] = mapped_column(Enum(RecipeUnit))

    cover_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("picture.id"), nullable=True
    )
    cover: Mapped[Optional["Picture"]] = relationship("Picture")

    pictures: Mapped[List["Picture"]] = relationship(
        "Picture",
        secondary=recipe_pictures,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    components: Mapped[List["RecipeComponent"]] = relationship(
        "RecipeComponent",
        back_populates="recipe",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    steps: Mapped[List["RecipeStep"]] = relationship(
        "RecipeStep",
        back_populates="recipe",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    tools: Mapped[List["RecipeTool"]] = relationship(
        "RecipeTool",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    recipe_books: Mapped[List["RecipeBook"]] = relationship(
        "RecipeBook",
        secondary=recipe_book_recipes,
        back_populates="recipes",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def published(self) -> bool:
        return self.published_at is not None

    @property
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

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), index=True)
    created_by: Mapped["User"] = relationship("User")
    created_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTimeUTC, default=utc_now)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC, nullable=True, default=None
    )

    tags: Mapped[List[str]] = mapped_column(JSON, default=list)

    cover_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("picture.id"), nullable=True
    )
    cover: Mapped[Optional["Picture"]] = relationship("Picture")

    recipes: Mapped[List["Recipe"]] = relationship(
        "Recipe",
        secondary=recipe_book_recipes,
        back_populates="recipe_books",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def published(self) -> bool:
        return self.published_at is not None

    def __repr__(self) -> str:
        return f"RecipeBook(id={self.id}, name={self.name})"
