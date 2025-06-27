from fastapi import APIRouter, HTTPException, Body
from uuid import UUID
from typing import Annotated

from app.schemas.orders import CreateOrder, OrderPublic, ConfirmReceiveOrderItem, ItemsOfNewOrder
from app.db.repository import make_order, get_order as db_get_order, generate_order_number, confirm_order_receiving
from app.db.session import SessionDep

router = APIRouter(
    prefix="/api/v1/orders",
    tags=['orders']
)


@router.post("/create", response_model=OrderPublic)
async def create_order(order_items: Annotated[ItemsOfNewOrder, ...], session: SessionDep): # type: ignore
    order_items_id = [order_item.item_id for order_item in order_items]

    if len(list(set(order_items_id))) != len(order_items_id):
        raise HTTPException(status_code=422, detail=f'Items id in list should not be repeatable')
    
    return make_order(order_items=order_items, session=session)


@router.get("/get/{order_id}", response_model=OrderPublic)
async def get_order(order_id: UUID, session: SessionDep):
    return db_get_order(order_id=order_id, session=session)


@router.get("/receive/{order_id}")
async def receive_items_from_order(order_id: UUID, session: SessionDep) -> int:
    return generate_order_number(order_id=order_id, session=session)


@router.patch("/confirm/{order_id}", response_model=OrderPublic)
async def confirm_order_receive(order_id: UUID, order_items: list[ConfirmReceiveOrderItem], session: SessionDep):
    return confirm_order_receiving(order_id=order_id, order_items=order_items, session=session)
