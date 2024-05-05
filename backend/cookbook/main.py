from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi_pagination import add_pagination

from cookbook.api import pictures, recipe_books, recipes, token, users
from cookbook.db.session import get_db_session

app = FastAPI(
    root_path="/api",
    openapi_url="/",
    docs_url="/docs",
    redoc_url=None,
    title="Cookbook",
    separate_input_output_schemas=False,
)
add_pagination(app)


@app.middleware("http")
async def database_session_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    with get_db_session() as db:
        request.state.db = db
        response = await call_next(request)

        return response


app.include_router(token.router)
app.include_router(users.router)
app.include_router(recipes.router)
app.include_router(recipe_books.router)
app.include_router(pictures.router)
