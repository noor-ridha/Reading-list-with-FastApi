import strawberry
from strawberry.types import Info

from app.graphql.types import ExportJobType, ItemType, ListType
from app.schemas.item import ItemCreate
from app.schemas.list import ListCreate
from app.services import export_service, item_service, list_service


def _require_user(info: Info):
    user = info.context["current_user"]
    if user is None:
        raise Exception("Not authenticated")
    return user


@strawberry.type
class Query:
    @strawberry.field
    def my_lists(self, info: Info, limit: int = 20, offset: int = 0) -> list[ListType]:
        user = _require_user(info)
        db = info.context["db"]
        items, _ = list_service.get_lists(db, user.id, limit, offset)
        return [
            ListType(
                id=l.id,
                name=l.name,
                description=l.description,
                created_at=l.created_at,
                items=[],
            )
            for l in items
        ]

    @strawberry.field
    def list(self, info: Info, id: strawberry.ID) -> ListType | None:
        user = _require_user(info)
        db = info.context["db"]
        try:
            list_obj = list_service.get_list(db, user.id, id)
        except list_service.ListNotFoundError:
            return None

        list_items, _ = item_service.get_items(db, user.id, list_obj.id, limit=100, offset=0)
        return ListType(
            id=list_obj.id,
            name=list_obj.name,
            description=list_obj.description,
            created_at=list_obj.created_at,
            items=[
                ItemType(id=i.id, title=i.title, status=i.status, created_at=i.created_at)
                for i in list_items
            ],
        )

    @strawberry.field
    def export_job(self, info: Info, id: strawberry.ID) -> ExportJobType | None:
        user = _require_user(info)
        db = info.context["db"]
        try:
            job = export_service.get_export_job(db, user.id, id)
        except export_service.ExportJobNotFoundError:
            return None
        return ExportJobType(id=job.id, status=job.status, format=job.format, error=job.error)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_list(self, info: Info, name: str, description: str | None = None) -> ListType:
        user = _require_user(info)
        db = info.context["db"]
        list_obj = list_service.create_list(db, user.id, ListCreate(name=name, description=description))
        return ListType(
            id=list_obj.id,
            name=list_obj.name,
            description=list_obj.description,
            created_at=list_obj.created_at,
            items=[],
        )

    @strawberry.mutation
    def add_item(
        self, info: Info, list_id: strawberry.ID, title: str, status: str = "want_to_read"
    ) -> ItemType:
        user = _require_user(info)
        db = info.context["db"]
        item = item_service.create_item(db, user.id, list_id, ItemCreate(title=title, status=status))
        return ItemType(id=item.id, title=item.title, status=item.status, created_at=item.created_at)


schema = strawberry.Schema(query=Query, mutation=Mutation)