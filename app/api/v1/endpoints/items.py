from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from app.schemas.items import ItemUpdate, ItemSupply, ItemPublic, ItemCreate
from app.db.repository import create_item as db_create_item, update_item as db_update_item, take_delivery, update_orders_status_by_delivery
from app.db.session import SessionDep
from app.db.models import Item

from uuid import UUID

router = APIRouter(
    prefix="/api/v1/items",
    tags=['items']
)


@router.post("/create", response_model=ItemPublic)
async def create_item(item: ItemCreate, session: SessionDep):
    db_item = Item.model_validate(item)
    try:
       return db_create_item(item=db_item, session=session)
    except IntegrityError:
        session.rollback()

        raise HTTPException(status_code=422, detail=f'Item with name: {item.name} is already exists in database. It should be unique')


@router.patch("/update/{item_id}", response_model=ItemPublic)
async def update_item(item_id: UUID, item: ItemUpdate, session: SessionDep):
    db_item = 
    return db_update_item(item_id=item_id, item=item, session=session)


@router.put("/deliver")
async def supply_item(items: list[ItemSupply], session: SessionDep):
    take_delivery(items=items, session=session)
    update_orders_status_by_delivery(items=items, session=session)
    return {"success": True}
