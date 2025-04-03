from fastapi import APIRouter
from uuid import UUID

from app.schemas.orders import CreateOrder, OrderPublic
from app.db.repository import make_order
from app.db.session import SessionDep

router = APIRouter(
    prefix="/api/v1/orders",
    tags=['orders']
)


@router.post("/create", response_model=OrderPublic)
async def create_order(order_items: list[CreateOrder], session: SessionDep):
    return make_order(order_items=order_items, session=session)


@router.get("/get/{order_id}", response_model=OrderPublic)
async def get_order(order_id: UUID):
    pass


@router.patch("/receive/{order_id}", response_model=OrderPublic)
async def receive_items_from_order():
    pass
