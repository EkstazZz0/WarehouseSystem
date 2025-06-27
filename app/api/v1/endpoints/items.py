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
    print(session)
    try:
       return await db_create_item(item=db_item, session=session)
    except IntegrityError:
        await session.rollback()

        raise HTTPException(status_code=422, detail=f'Item with name: {item.name} is already exists in database. It should be unique')


@router.patch("/update/{item_id}", response_model=ItemPublic)
async def update_item(item_id: UUID, item: ItemUpdate, session: SessionDep):
    db_item = await session.get(Item, item_id)

    if not db_item:
        raise HTTPException(status_code=404, detail=f'Item with id: {item_id} does not exists in database.')
    
    try:
        return await db_update_item(item=db_item, item_to_update=item, session=session)
    except IntegrityError:
        await session.rollback()

        raise HTTPException(status_code=422, detail=f'Item with name: {item.name} is already exists in database. It should be unique')


@router.put("/deliver")
async def supply_item(items: list[ItemSupply], session: SessionDep):
    await take_delivery(items=items, session=session)
    await update_orders_status_by_delivery(items=items, session=session)
    return {"success": True}
