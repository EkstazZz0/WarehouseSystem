from fastapi import APIRouter, HTTPException, Body
from uuid import UUID
from typing import Annotated
import json

from app.schemas.orders import CreateOrder, OrderPublic, ConfirmReceiveOrderItem, ItemsOfNewOrder
from app.db.repository import get_order as db_get_order, generate_order_number, confirm_order_receiving, create_order as db_create_order
from app.db.session import SessionDep
from app.db.models import Item
from app.kafka.producer import producer, producer_delivery_report
from app.kafka.models import KafkaMessageNewOrder

router = APIRouter(
    prefix="/api/v1/orders",
    tags=['orders']
)


@router.post("/create", response_model=OrderPublic)
async def create_order(order_items: Annotated[ItemsOfNewOrder, ...], session: SessionDep): # type: ignore
    order_items_id = [order_item.item_id for order_item in order_items]

    if len(set(order_items_id)) != len(order_items_id):
        raise HTTPException(status_code=422, detail=f'Items id in list should not be repeatable')
    
    order = await db_create_order(order_items=order_items, session=session)
    kafka_message_key = str(order.order_id).encode("utf-8")

    producer.produce(
        topic='db_work',
        key=kafka_message_key,
        value=KafkaMessageNewOrder(payload=order).model_dump_json().encode("utf-8"),
        callback=producer_delivery_report
    )
    
    return order


@router.get("/get/{order_id}", response_model=OrderPublic)
async def get_order(order_id: UUID, session: SessionDep):
    return await db_get_order(order_id=order_id, session=session)


@router.get("/receive/{order_id}")
async def receive_items_from_order(order_id: UUID, session: SessionDep) -> int:
    return await generate_order_number(order_id=order_id, session=session)


@router.patch("/confirm/{order_id}", response_model=OrderPublic)
async def confirm_order_receive(order_id: UUID, order_items: list[ConfirmReceiveOrderItem], session: SessionDep):
    return await confirm_order_receiving(order_id=order_id, order_items=order_items, session=session)
