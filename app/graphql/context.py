from fastapi import Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User


async def get_graphql_context(request: Request) -> dict:
    db: Session = next(get_db())

    auth_header = request.headers.get("Authorization", "")
    current_user: User | None = None
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        user_id = decode_access_token(token)
        if user_id:
            current_user = db.query(User).filter(User.id == user_id).first()

    return {"db": db, "current_user": current_user}