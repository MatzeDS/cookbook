import click
from sqlalchemy import select

from cookbook.auth import Permission, create_permission_bitmask, get_password_hash
from cookbook.db.models import User
from cookbook.db.session import get_db_session


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--username", "-u", required=True, type=str)
@click.option("--password", "-p", required=True, type=str)
@click.option("--email", "-m", required=True, type=str)
@click.option("--fullname", "-n", required=True, type=str)
@click.option("--admin", "-a", is_flag=True, default=False)
def add_user(
    username: str, password: str, email: str, fullname: str, admin: bool
) -> None:
    with get_db_session() as db:
        user = db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()

        if user:
            raise ValueError("Username already exists")

        pw_hash = get_password_hash(password)
        permissions = create_permission_bitmask(admin and [Permission.ADMIN] or [])

        user = User(
            username=username,
            hashed_password=pw_hash,
            email=email,
            full_name=fullname,
            permissions=permissions,
        )

        db.add(user)
        db.commit()


if __name__ == "__main__":
    cli()
