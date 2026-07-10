import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.list import List
from app.schemas.list import ListCreate, ListUpdate

MAX_PAGE_SIZE = 100


class ListNotFoundError(Exception):
    pass


def create_list(db: Session, owner_id: uuid.UUID, data: ListCreate) -> List:
    list_obj = List(owner_id=owner_id, name=data.name, description=data.description)
    db.add(list_obj)
    db.commit()
    db.refresh(list_obj)
    return list_obj


def get_list(db: Session, owner_id: uuid.UUID, list_id: uuid.UUID) -> List:
        # owner_id in the filter, not a separate check — non-owned looks like non-existent
    list_obj = (
        db.query(List)
        .filter(List.id == list_id, List.owner_id == owner_id)
        .first()
    )
    if list_obj is None:
        raise ListNotFoundError()
    return list_obj


def get_lists(
    db: Session, owner_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[List], int]:
    limit = min(limit, MAX_PAGE_SIZE)

    base_query = db.query(List).filter(List.owner_id == owner_id)

    total = base_query.with_entities(func.count(List.id)).scalar()

    items = (
        base_query.order_by(List.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def update_list(
    db: Session, owner_id: uuid.UUID, list_id: uuid.UUID, data: ListUpdate
) -> List:
    list_obj = get_list(db, owner_id, list_id)

    if data.name is not None:
        list_obj.name = data.name
    if data.description is not None:
        list_obj.description = data.description

    db.commit()
    db.refresh(list_obj)
    return list_obj


def delete_list(db: Session, owner_id: uuid.UUID, list_id: uuid.UUID) -> None:
    list_obj = get_list(db, owner_id, list_id)
    db.delete(list_obj)
    db.commit()