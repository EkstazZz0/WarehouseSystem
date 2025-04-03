from sqlmodel import SQLModel
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import traceback
from datetime import datetime

from app.db.session import engine, SessionDep
from app.db.models import Item, Order, OrderItem
from app.schemas.items import ItemCreate, ItemUpdate, ItemSupply
from app.schemas.orders import CreateOrder, OrderItemStatus, OrderPublic, OrderItemPublic


def init_db():
    SQLModel.metadata.create_all(engine)


def drop_db():
    SQLModel.metadata.drop_all(engine)


def create_item(session: SessionDep, item: ItemCreate) -> Item:
    db_item = Item.model_validate(item)
    session.add(db_item)

    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f'Item with name: {item.name} is already exists in database. It should be unique')
    
    session.refresh(db_item)
    return db_item


def update_item(item_id: UUID, item: ItemUpdate, session: SessionDep) -> Item:
    db_item = session.get(Item, item_id)

    if not db_item:
        raise HTTPException(status_code=400, detail=f'Item with id: {item_id} does not exists in database.')
    
    item_data = item.model_dump(exclude_unset=True)
    item_data['updated_at'] = datetime.now()
    db_item.sqlmodel_update(item_data)
    session.add(db_item)

    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f'Item with name: {item.name} is already exists in database. It should be unique')
    
    session.refresh(db_item)
    return db_item


def take_delivery(items: list[ItemSupply], session: SessionDep):
    for item in items:
        db_item = session.get(Item, item.item_id)

        if not db_item:
            raise HTTPException(status_code=400, detail=f'Item with id: {item.item_id} was not found in database')

        db_item.quantity += item.quantity
        db_item.updated_at = datetime.now()
        session.add(db_item)
        try:
            session.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail='something went wrong with database')
        session.refresh(db_item)


def create_order(session: SessionDep) -> Order:
    order = Order()
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def make_order(order_items: list[CreateOrder], session: SessionDep) -> OrderPublic:
    db_items = []
    for order_item in order_items:
        db_item = session.get(Item, order_item.item_id)

        if not db_item:
            session.rollback()
            raise HTTPException(status_code=400, detail=f'Item with id: {order_item.item_id} was not found in database')
        
        db_items.append[db_item]
    
    public_order_items = []
    order = create_order(session=session)

    for order_item, db_item in zip(order_items, db_items):

        if db_item.quantity - db_item.reserved >= order_item.quantity:
            order_item_status = OrderItemStatus.receivable
        else:
            order_item_status = OrderItemStatus.on_delivery
        
        db_item.reserved += order_item.quantity
        
        session.add(db_item)
        session.commit()
        session.refresh(db_item)

        db_order_item = OrderItem(**order_item.model_dump(), order_id=order.order_id, status=order_item_status)

        session.add(db_order_item)
        session.commit()
        session.refresh(db_order_item)

        public_order_item = OrderItemPublic.model_validate(db_order_item)
        public_order_items.append(public_order_item)
    
    from app.core.utils import get_order_status
    order.status = get_order_status(order_items=public_order_items)
    session.add(order)
    session.commit()
    session.refresh(order)

    return OrderPublic(**order.model_dump(), items=public_order_items)
