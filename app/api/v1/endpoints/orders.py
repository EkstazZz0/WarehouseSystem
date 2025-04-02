from fastapi import APIRouter
from uuid import UUID

from app.schemas.orders import CreateOrderItem, OrderPublic
from app.db.repository import create_order as db_create_order, create_order_items
from app.db.session import SessionDep

router = APIRouter(
    prefix="/api/v1/orders",
    tags=['orders']
)


@router.post("/create", response_model=OrderPublic)
async def create_order(order_items: list[CreateOrderItem], session: SessionDep):
    order = db_create_order(session=session)
    created_order_items = create_order_items(order_id=order.order_id, order_items=order_items, session=session)
    order_public = OrderPublic
    return order


@router.get("/get/{order_id}", response_model=OrderPublic)
async def get_order(order_id: UUID):
    pass


@router.patch("/receive/{order_id}", response_model=OrderPublic)
async def receive_items_from_order():
    pass
