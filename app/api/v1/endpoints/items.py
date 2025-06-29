from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from typing import Annotated

from app.schemas.items import ItemUpdate, ItemSupply, ItemPublic, ItemCreate
from app.db.repository import create_item as db_create_item, update_item as db_update_item, take_delivery, get_items as db_get_items
from app.db.session import SessionDep
from app.db.models import Item
from app.kafka.producer import producer, producer_delivery_report
from app.kafka.models import KafkaMessageNewSupply, SupplyList
from app.core.enums import AvailableOrderColumn

from uuid import UUID, uuid4

router = APIRouter(
    prefix="/api/v1/items",
    tags=['items']
)

@router.get("/", response_model=list[Item])
async def get_items(session: SessionDep, 
                    limit: Annotated[int | None, Query(gt=0, le=100)] = 10, 
                    offset: Annotated[int | None, Query(ge=0)] = 0, 
                    order_by: Annotated[AvailableOrderColumn | None, Query()] = AvailableOrderColumn.created_at):
    return await db_get_items(session=session, limit=limit, offset=offset, order_by=order_by.value)


@router.post("/create", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
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

    producer.produce(
        topic='db_work',
        key=str(uuid4()).encode("utf-8"),
        value=KafkaMessageNewSupply(payload=SupplyList(items=items)).model_dump_json().encode("utf-8"),
        callback=producer_delivery_report
    )
    return {"success": True}
