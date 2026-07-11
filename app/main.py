from fastapi import FastAPI

from strawberry.fastapi import GraphQLRouter
from app.graphql.context import get_graphql_context
from app.graphql.schema import schema

from app.api.routes import auth, lists, items,exports

app = FastAPI(
    title="Reading List API",
    description="Personal Catalog API — Shelves (Lists) and Books (Items)",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(lists.router)
app.include_router(items.router)
app.include_router(exports.router)

# graphql setup
graphql_app = GraphQLRouter(schema, context_getter=get_graphql_context)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}