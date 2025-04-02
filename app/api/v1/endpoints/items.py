from fastapi import APIRouter

from app.schemas.items import ItemUpdate, ItemSupply, ItemPublic, ItemCreate
from app.db.repository import create_item as db_create_item, update_item as db_update_item, take_delivery
from app.db.session import SessionDep

from uuid import UUID

router = APIRouter(
    prefix="/api/v1/items",
    tags=['items']
)


@router.post("/create", response_model=ItemPublic)
async def create_item(item: ItemCreate, session: SessionDep):
    return db_create_item(item=item, session=session)


@router.patch("/update/{item_id}", response_model=ItemPublic)
async def update_item(item_id: UUID, item: ItemUpdate, session: SessionDep):
    return db_update_item(item_id=item_id, item=item, session=session)


@router.put("/deliver")
async def supply_item(items: list[ItemSupply], session: SessionDep):
    take_delivery(items=items, session=session)
    return {"success": True}
