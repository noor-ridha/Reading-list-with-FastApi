import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.list import List
from app.schemas.item import ItemCreate, ItemUpdate

MAX_PAGE_SIZE = 100


class ItemNotFoundError(Exception):
    pass


class ListNotOwnedError(Exception):
    pass


def _assert_list_owned(db: Session, owner_id: uuid.UUID, list_id: uuid.UUID) -> None:
    # One indexed lookup — confirms the list exists AND belongs to this user
    # before we let them touch anything inside it.
    exists = (
        db.query(List.id)
        .filter(List.id == list_id, List.owner_id == owner_id)
        .first()
    )
    if exists is None:
        raise ListNotOwnedError()


def create_item(
    db: Session, owner_id: uuid.UUID, list_id: uuid.UUID, data: ItemCreate
) -> Item:
    _assert_list_owned(db, owner_id, list_id)
    item = Item(list_id=list_id, title=data.title, status=data.status)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item(
    db: Session, owner_id: uuid.UUID, list_id: uuid.UUID, item_id: uuid.UUID
) -> Item:
    # Ownership enforced via JOIN in a single query — item must belong to
    # list_id, and list_id must belong to owner_id so item.list_id must match AND that list must belong to owner_id
    
    item = (
        db.query(Item)
        .join(List, Item.list_id == List.id)
        .filter(
            Item.id == item_id,
            Item.list_id == list_id,
            List.owner_id == owner_id,
        )
        .first()
    )
    if item is None:
        raise ItemNotFoundError()
    return item


def get_items(
    db: Session, owner_id: uuid.UUID, list_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[Item], int]:
    _assert_list_owned(db, owner_id, list_id)
    limit = min(limit, MAX_PAGE_SIZE)

    base_query = db.query(Item).filter(Item.list_id == list_id)

    total = base_query.with_entities(func.count(Item.id)).scalar()

    items = (
        base_query.order_by(Item.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def update_item(
    db: Session,
    owner_id: uuid.UUID,
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    data: ItemUpdate,
) -> Item:
    item = get_item(db, owner_id, list_id, item_id)

    if data.title is not None:
        item.title = data.title
    if data.status is not None:
        item.status = data.status

    db.commit()
    db.refresh(item)
    return item


def delete_item(
    db: Session, owner_id: uuid.UUID, list_id: uuid.UUID, item_id: uuid.UUID
) -> None:
    item = get_item(db, owner_id, list_id, item_id)
    db.delete(item)
    db.commit()