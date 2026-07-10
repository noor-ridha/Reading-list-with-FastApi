from fastapi import FastAPI

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


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}