from sqlmodel import SQLModel, Field
from pydantic import conlist
from uuid import UUID
from enum import Enum
from datetime import datetime
from pydantic import conlist

from app.core.enums import OrderItemStatus, ReceiveOrderItemStatus, OrderStatus


class OrderItemPublic(SQLModel):
    order_item_id: UUID = Field()
    item_id: UUID = Field()
    quantity: int = Field(gt=0)
    status: OrderItemStatus = Field()


class ConfirmReceiveOrderItem(SQLModel):
    order_item_id: UUID = Field()
    status: ReceiveOrderItemStatus = Field()


class CreateOrder(SQLModel):
    item_id: UUID = Field()
    quantity: int = Field(gt=0, le=10)


ItemsOfNewOrder = conlist(CreateOrder, min_length=1, max_length=10)


class OrderPublic(SQLModel):
    order_id: UUID = Field()
    queue_number: int | None = Field(default=None)
    status: OrderStatus = Field()
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemPublic] = Field()
