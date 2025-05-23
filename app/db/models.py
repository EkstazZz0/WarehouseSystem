from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime

from app.schemas.items import ItemBase
from app.schemas.orders import OrderStatus, OrderItemStatus


class Item(ItemBase, table=True):
    item_id: UUID = Field(default_factory=uuid4, primary_key=True)
    quantity: int | None = Field(default=0, ge=0)
    reserved: int | None = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Order(SQLModel, table=True):
    order_id: UUID = Field(default_factory=uuid4, primary_key=True)
    queue_number: int | None = Field(lt=1000, ge=0, unique=True, nullable=True, default=None)
    status: OrderStatus | None = Field(default=OrderStatus.accepted)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class OrderItem(SQLModel, table=True):
    order_item_id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="order.order_id", ondelete='CASCADE')
    item_id: UUID = Field(foreign_key="item.item_id", ondelete='CASCADE')
    quantity: int = Field(gt=0)
    status: OrderItemStatus = Field()

