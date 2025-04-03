from fastapi import APIRouter
from uuid import UUID

from app.schemas.orders import CreateOrder, OrderPublic
from app.db.repository import make_order, get_order as db_get_order, generate_order_number
from app.db.session import SessionDep

router = APIRouter(
    prefix="/api/v1/orders",
    tags=['orders']
)


@router.post("/create", response_model=OrderPublic)
async def create_order(order_items: list[CreateOrder], session: SessionDep):
    return make_order(order_items=order_items, session=session)


@router.get("/get/{order_id}", response_model=OrderPublic)
async def get_order(order_id: UUID, session: SessionDep):
    return db_get_order(order_id=order_id, session=session)


@router.patch("/receive/{order_id}")
async def receive_items_from_order(order_id: UUID) -> int:
    return generate_order_number(order_id=order_id, session=SessionDep)


@router.post("/confirm/{order_id}", response_model=OrderPublic)
async def confirm_order_receive(order_id: UUID):
    pass