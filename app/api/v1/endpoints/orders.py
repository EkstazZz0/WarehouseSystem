from fastapi import APIRouter
from uuid import UUID

from app.schemas.orders import OrderItem, OrderPublic

router = APIRouter(
    prefix="/api/v1/orders",
    tags=['orders']
)


@router.post("/create")
async def create_order(order_items: list[OrderItem]):
    pass


@router.get("/get/{order_id}", response_model=OrderPublic)
async def get_order(order_id: UUID):
    pass


@router.patch("/receive/{order_id}", response_model=OrderPublic)
async def receive_items_from_order():
    pass
