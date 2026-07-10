import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.cache.redis_client import list_cache_key, redis_client
from app.models.user import User
from app.schemas.list import ListCreate, ListOut, ListPage, ListUpdate
from app.services.list_service import (
    ListNotFoundError,
    create_list,
    delete_list,
    get_list,
    get_lists,
    update_list,
)

router = APIRouter(prefix="/lists", tags=["lists"])


@router.post("", response_model=ListOut, status_code=status.HTTP_201_CREATED)
def create_list_route(
    data: ListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListOut:
    return create_list(db, current_user.id, data)


@router.get("", response_model=ListPage)
def list_lists_route(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListPage:
    items, total = get_lists(db, current_user.id, limit, offset)
    return ListPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{list_id}", response_model=ListOut)
def get_list_route(
    list_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListOut:
    cache_key = list_cache_key(current_user.id, list_id)

    cached = redis_client.get(cache_key)
    if cached is not None:
        return ListOut(**json.loads(cached))

    try:
        list_obj = get_list(db, current_user.id, list_id)
    except ListNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found") from None

    result = ListOut.model_validate(list_obj)
    redis_client.setex(cache_key, 300, result.model_dump_json())
    return result


@router.patch("/{list_id}", response_model=ListOut)
def update_list_route(
    list_id: uuid.UUID,
    data: ListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListOut:
    try:
        result = update_list(db, current_user.id, list_id, data)
    except ListNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found") from None

    redis_client.delete(list_cache_key(current_user.id, list_id))
    return result


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list_route(
    list_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        delete_list(db, current_user.id, list_id)
    except ListNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found") from None

    redis_client.delete(list_cache_key(current_user.id, list_id))