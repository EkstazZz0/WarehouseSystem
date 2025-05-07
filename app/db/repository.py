from sqlmodel import SQLModel, select
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import traceback
from datetime import datetime
from sqlalchemy import func, or_

from app.db.session import engine, SessionDep
from app.db.models import Item, Order, OrderItem
from app.schemas.items import ItemCreate, ItemUpdate, ItemSupply
from app.schemas.orders import CreateOrder, OrderItemStatus, OrderPublic, OrderItemPublic, OrderStatus, ConfirmReceiveOrderItem
from app.core.utils import get_next_order_number, get_order_status


def init_db():
    SQLModel.metadata.create_all(engine)


def drop_db():
    SQLModel.metadata.drop_all(engine)


def create_item(session: SessionDep, item: Item) -> Item:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def update_item(item:Item, item_to_update: ItemUpdate, session: SessionDep) -> Item:
    
    item_data = item_to_update.model_dump(exclude_unset=True)
    item_data['updated_at'] = datetime.now()
    item.sqlmodel_update(item_data)

    session.add(item)

    session.commit()
    
    session.refresh(item)

    return item


def take_delivery(items: list[ItemSupply], session: SessionDep):
    for item in items:
        db_item = session.get(Item, item.item_id)

        if not db_item:
            raise HTTPException(status_code=404, detail=f'Item with id: {item.item_id} was not found in database.')

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


def update_orders_status_by_delivery(items: list[ItemSupply], session: SessionDep) -> None:
    for item in items:
        db_item = session.get(Item, item.item_id)
        order_ids = session.exec(select(OrderItem.order_id).where((OrderItem.item_id == item.item_id) & (OrderItem.status == OrderItemStatus.on_delivery))).all()

        if not order_ids:
            continue

        orders = session.exec(select(Order).where(Order.order_id.in_(order_ids)).order_by(Order.created_at)).all()

        for order in orders:

            receivable_quantity = session.exec(select(func.sum(OrderItem.quantity))
                                            .where((OrderItem.item_id == item.item_id) & (OrderItem.status == OrderItemStatus.receivable))
                                            .group_by(OrderItem.item_id)).first()
            if not receivable_quantity:
                receivable_quantity = 0
                
            order_order_item = session.exec(select(OrderItem).where((OrderItem.order_id == order.order_id) & (OrderItem.item_id == item.item_id) & (OrderItem.status == OrderItemStatus.on_delivery))).first()

            if not order_order_item:
                continue

            if order_order_item.quantity + receivable_quantity <= db_item.quantity:
                order_order_item.status = OrderItemStatus.receivable
                session.add(order_order_item)
                session.commit()
                session.refresh(order_order_item)
        
        order_ids = session.exec(select(OrderItem.order_id).where(OrderItem.item_id == item.item_id)).all()

        orders = session.exec(select(Order).where(Order.order_id.in_(order_ids))).all()
        for order in orders:
            order_items = session.exec(select(OrderItem).where((OrderItem.order_id == order.order_id) & or_(OrderItem.status == OrderItemStatus.on_delivery, OrderItem.status == OrderItemStatus.receivable))).all()
            new_order_status = get_order_status(order_items=[OrderItemPublic.model_validate(order_item) for order_item in order_items])
            if order.status != new_order_status:
                order.status = new_order_status
                order.updated_at = datetime.now()
                session.add(order)
                session.commit()
                session.refresh(order)


def make_order(order_items: list[CreateOrder], session: SessionDep) -> OrderPublic:
    order_items_id = [order_item.item_id for order_item in order_items]

    if len(list(set(order_items_id))) != len(order_items_id):
        raise HTTPException(status_code=422, detail=f'Items id in list should not be repeatable')
    
    db_items = []
    for order_item in order_items:
        db_item = session.get(Item, order_item.item_id)

        if not db_item:
            session.rollback()
            raise HTTPException(status_code=404, detail=f'Item with id: {order_item.item_id} was not found in database.')
        
        db_items.append(db_item)
    
    public_order_items = []
    order = create_order(session=session)

    for order_item, db_item in zip(order_items, db_items):

        if db_item.quantity - db_item.reserved >= order_item.quantity:
            order_item_status = OrderItemStatus.receivable
        else:
            order_item_status = OrderItemStatus.on_delivery
        
        db_item.reserved += order_item.quantity
        db_item.updated_at = datetime.now()
        
        session.add(db_item)
        session.commit()
        session.refresh(db_item)

        db_order_item = OrderItem(**order_item.model_dump(), order_id=order.order_id, status=order_item_status)

        session.add(db_order_item)
        session.commit()
        session.refresh(db_order_item)

        public_order_item = OrderItemPublic.model_validate(db_order_item)
        public_order_items.append(public_order_item)

    order.status = get_order_status(order_items=public_order_items)
    order.updated_at = datetime.now()
    session.add(order)
    session.commit()
    session.refresh(order)

    return OrderPublic(**order.model_dump(), items=public_order_items)


def get_order(order_id: UUID, session: SessionDep) -> OrderPublic:
    order = session.get(Order, order_id)
    order_items = session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()

    return OrderPublic(**order.model_dump(), items=[OrderItemPublic.model_validate(order_item) for order_item in order_items])


def generate_order_number(order_id: UUID, session: SessionDep) -> int:
    order = session.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail=f'Order with id: {order_id} was not found in database.')
    elif order.status in [OrderStatus.accepted, OrderStatus.canceled, OrderStatus.finished, OrderStatus.partially_finished]:
        raise HTTPException(status_code=422, detail=f'Order with id: {order_id} does not exist')
    elif order.queue_number is not None:
        return order.queue_number
    
    max_order_queue_number = session.exec(select(func.max(Order.queue_number)).where(Order.queue_number != None)).first()
    print(session.exec(select(Order.queue_number).where(Order.queue_number != None).order_by(Order.queue_number)).all(), "\n\n\n\n")

    if max_order_queue_number is None:
        order_queue_number = 0
    elif max_order_queue_number == 999:
        order_queue_number = get_next_order_number(order_numbers=session.exec(select(Order.queue_number).where(Order.queue_number != None).order_by(Order.queue_number)).all())
    else:
        order_queue_number = max_order_queue_number + 1
    
    order.queue_number = order_queue_number
    order.updated_at = datetime.now()

    session.add(order)
    session.commit()
    session.refresh(order)

    return order.queue_number


def confirm_order_receiving(order_id: UUID, order_items: list[ConfirmReceiveOrderItem], session: SessionDep) -> OrderPublic:
    order_items_ids = [order_item.order_item_id for order_item in order_items]
    db_order_items = session.exec(select(OrderItem).where(OrderItem.order_item_id.in_(order_items_ids))).all()

    order = session.get(Order, order_id)

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

        item = session.get(Item, db_order_item.item_id)

        if db_order_item.status == OrderItemStatus.received:
            item.quantity -= db_order_item.quantity
            item.reserved -= db_order_item.quantity
        else:
            item.reserved -= db_order_item.quantity
        
        item.updated_at = datetime.now()
        
        session.add(item)
        session.commit()
        session.refresh(item)

        session.add(db_order_item)
        session.commit()
        session.refresh(db_order_item)
    
    public_order_items = [OrderItemPublic.model_validate(db_item_for_order) for db_item_for_order in session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()]

    order.status = get_order_status(order_items=public_order_items)
    order.queue_number = None
    order.updated_at = datetime.now()

    session.add(order)
    session.commit()
    session.refresh(order)

    return OrderPublic(**order.model_dump(), items=public_order_items)
    


