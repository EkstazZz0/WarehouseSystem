from sqlmodel import SQLModel, select
from uuid import UUID
from fastapi import HTTPException
from datetime import datetime
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.db.session import engine, SessionDep
from app.db.models import Item, Order, OrderItem
from app.schemas.items import ItemUpdate, ItemSupply
from app.schemas.orders import CreateOrder, OrderItemStatus, OrderPublic, OrderItemPublic, OrderStatus, ConfirmReceiveOrderItem
from app.core.utils import get_next_order_number, get_order_status


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def create_item(session: SessionDep, item: Item) -> Item:
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def update_item(item:Item, item_to_update: ItemUpdate, session: SessionDep) -> Item:
    item_data = item_to_update.model_dump(exclude_unset=True)
    item.sqlmodel_update(item_data)

    session.add(item)
    await session.commit()
    await session.refresh(item)

    return item


async def take_delivery(items: list[ItemSupply], session: SessionDep):
    for item in items:
        db_item = await session.get(Item, item.item_id)

        if not db_item:
            raise HTTPException(status_code=404, detail=f'Item with id: {item.item_id} was not found in database.')

        db_item.quantity += item.quantity
        session.add(db_item)
    
    try:
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail='something went wrong with database')
    
    await session.refresh(db_item)


async def create_order(order_items: list[CreateOrder], session: SessionDep) -> OrderPublic:
    public_order_items = []
    order = Order()
    session.add(order)

    for order_item in order_items:
        db_order_item = OrderItem(**order_item.model_dump(), order_id=order.order_id)

        session.add(db_order_item)

        public_order_item = OrderItemPublic.model_validate(db_order_item)
        public_order_items.append(public_order_item)
    
    try:
        await session.commit()
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail=e._sql_message())
    except:
        raise HTTPException(status_code=500, detail='Something went wrong, please try again or contact support')

    await session.refresh(order)

    return OrderPublic(**order.model_dump(), items=public_order_items)


async def get_order(order_id: UUID, session: SessionDep) -> OrderPublic:
    order = await session.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail=f'Order with id {order_id} does not exist in database')
    
    order_items = (await session.execute(select(OrderItem).where(OrderItem.order_id == order_id))).scalars().all()

    return OrderPublic(**order.model_dump(), items=[OrderItemPublic.model_validate(order_item) for order_item in order_items])


async def generate_order_number(order_id: UUID, session: SessionDep) -> int:
    order = session.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail=f'Order with id: {order_id} was not found in database.')
    elif order.status in [OrderStatus.accepted, OrderStatus.canceled, OrderStatus.finished, OrderStatus.partially_finished]:
        raise HTTPException(status_code=422, detail=f'Order with id: {order_id} does not exist')
    elif order.queue_number is not None:
        return order.queue_number
    
    max_order_queue_number = (await session.execute(select(func.max(Order.queue_number)).where(Order.queue_number != None))).scalars().first()

    if max_order_queue_number is None:
        order_queue_number = 0
    elif max_order_queue_number == 999:
        order_queue_number = get_next_order_number(order_numbers=(await session.execute(select(Order.queue_number).where(Order.queue_number != None).order_by(Order.queue_number))).scalars().all())
    else:
        order_queue_number = max_order_queue_number + 1
    
    order.queue_number = order_queue_number

    session.add(order)
    await session.commit()
    await session.refresh(order)

    return order.queue_number


async def confirm_order_receiving(order_id: UUID, order_items: list[ConfirmReceiveOrderItem], session: SessionDep) -> OrderPublic:
    order_items_ids = [order_item.order_item_id for order_item in order_items]
    db_order_items = (await session.execute(select(OrderItem).where(OrderItem.order_item_id.in_(order_items_ids)))).scalars().all()

    order = await session.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail=f'Order with id: {order_id} was not found in database.')
    
    if order.queue_number is None:
        raise HTTPException(status_code=422, detail=f'Order must have a queue number')

    if not db_order_items:
        raise HTTPException(status_code=404, detail='Order items was not found in database')

    if not all([db_order_item.order_id == order_id for db_order_item in db_order_items]):
        raise HTTPException(status_code=422, detail='Some items do not match the order')
    
    if not all([db_order_item.status == OrderItemStatus.receivable for db_order_item in db_order_items]):
        raise HTTPException(status_code=422, detail='All the items must have a receivable status')

    if len(list(set([order_item.order_item_id for order_item in order_items]))) != len(order_items):
        raise HTTPException(status_code=422, detail='Items shouldn\'t be repeatable')
    
    for db_order_item in db_order_items:
        try:
            db_order_item.status = OrderItemStatus([order_item.status for order_item in order_items if order_item.order_item_id == db_order_item.order_item_id][0].value)
        except:
            raise HTTPException(status_code=404, detail='Some of the items was not found in database.')

        item = await session.get(Item, db_order_item.item_id)

        if db_order_item.status == OrderItemStatus.received:
            item.quantity -= db_order_item.quantity
            item.reserved -= db_order_item.quantity
        else:
            item.reserved -= db_order_item.quantity
        
        session.add(item)
        await session.commit()
        await session.refresh(item)

        session.add(db_order_item)
        await session.commit()
        await session.refresh(db_order_item)
    
    public_order_items = [OrderItemPublic.model_validate(db_item_for_order) for db_item_for_order in (await session.execute(select(OrderItem).where(OrderItem.order_id == order_id))).scalars().all()]

    order.status = get_order_status(order_items=public_order_items)
    order.queue_number = None

    session.add(order)
    await session.commit()
    await session.refresh(order)

    return OrderPublic(**order.model_dump(), items=public_order_items)
    


