from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Cookbook(Base):
    __tablename__ = "cookbook"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(127))

    def __repr__(self) -> str:
        return f"Cookbook(id={self.id}, name={self.name})"
