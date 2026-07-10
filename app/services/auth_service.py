from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserLogin, UserRegister


class AuthError(Exception):
    """Raised for expected auth failures (duplicate email, bad credentials)."""


def register_user(db: Session, data: UserRegister) -> User:
    user = User(email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AuthError("Email already registered") from None
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: UserLogin) -> str:
    # Single indexed lookup on email — no N+1 risk here since it's one query.
    user = db.query(User).filter(User.email == data.email).first()
    if user is None or not verify_password(data.password, user.hashed_password):
        raise AuthError("Invalid email or password")
    return create_access_token(subject=str(user.id))