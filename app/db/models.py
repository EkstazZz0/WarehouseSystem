from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from enum import Enum

from app.schemas.items import ItemBase


class OrderStatus(Enum):
    accepted = 'accepted'
    on_delivery = 'on_delivery'
    partially_delivered = 'partially_delivered'
    delivered_pending = 'delivered_pending'
    partially_finished = 'partially_finished'
    finished = 'finished'


class Item(ItemBase, table=True):
    item_id: UUID = Field(default_factory=uuid4, primary_key=True)


class Order(SQLModel, table=True):
    order_id: UUID = Field(default_factory=uuid4, primary_key=True)
    queue_number: str | None = Field(min_length=4, max_length=4)
    status: OrderStatus = Field()


class OrderItems(SQLModel, table=True):
    order_item_id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="order.order_id")
    item_id: UUID = Field(foreign_key="item.item_id")
    quantity: int = Field(gt=0)

