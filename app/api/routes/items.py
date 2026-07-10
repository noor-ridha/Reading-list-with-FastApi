import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.item import ItemCreate, ItemOut, ItemPage, ItemUpdate
from app.services.item_service import (
    ItemNotFoundError,
    ListNotOwnedError,
    create_item,
    delete_item,
    get_item,
    get_items,
    update_item,
)

router = APIRouter(prefix="/lists/{list_id}/items", tags=["items"])


def _not_found(detail: str = "Not found") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item_route(
    list_id: uuid.UUID,
    data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ItemOut:
    try:
        return create_item(db, current_user.id, list_id, data)
    except ListNotOwnedError:
        raise _not_found("List not found") from None


@router.get("", response_model=ItemPage)
def list_items_route(
    list_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ItemPage:
    try:
        items, total = get_items(db, current_user.id, list_id, limit, offset)
    except ListNotOwnedError:
        raise _not_found("List not found") from None
    return ItemPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{item_id}", response_model=ItemOut)
def get_item_route(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ItemOut:
    try:
        return get_item(db, current_user.id, list_id, item_id)
    except ItemNotFoundError:
        raise _not_found("Item not found") from None


@router.patch("/{item_id}", response_model=ItemOut)
def update_item_route(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ItemOut:
    try:
        return update_item(db, current_user.id, list_id, item_id, data)
    except ItemNotFoundError:
        raise _not_found("Item not found") from None


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item_route(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        delete_item(db, current_user.id, list_id, item_id)
    except ItemNotFoundError:
        raise _not_found("Item not found") from None