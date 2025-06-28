from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime

from app.schemas.items import ItemBase
from app.schemas.orders import OrderStatus, OrderItemStatus


class Item(ItemBase, table=True):
    __tablename__ = "items"

    item_id: UUID = Field(default_factory=uuid4, primary_key=True)
    quantity: int | None = Field(default=0, ge=0)
    reserved: int | None = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __setattr__(self, name, value):
        if name != 'updated_at' and hasattr(self, name):
            super().__setattr__('updated_at', datetime.now())
        
        return super().__setattr__(name, value)
    

    def sqlmodel_update(self, obj, *, update = None):
        self.updated_at = datetime.now()
        return super().sqlmodel_update(obj, update=update)


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    order_id: UUID = Field(default_factory=uuid4, primary_key=True)
    queue_number: int | None = Field(lt=1000, ge=0, unique=True, nullable=True, default=None)
    status: OrderStatus | None = Field(default=OrderStatus.pending)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __setattr__(self, name, value):
        if name != 'updated_at' and hasattr(self, name):
            super().__setattr__('updated_at', datetime.now())
        
        return super().__setattr__(name, value)
    
    
    def sqlmodel_update(self, obj, *, update = None):
        self.updated_at = datetime.now()
        return super().sqlmodel_update(obj, update=update)


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    order_item_id: UUID = Field(default_factory=uuid4, primary_key=True)
    order_id: UUID = Field(foreign_key="orders.order_id", ondelete='CASCADE')
    item_id: UUID = Field(foreign_key="items.item_id", ondelete='CASCADE')
    quantity: int = Field(gt=0)
    status: OrderItemStatus | None = Field(default=OrderItemStatus.pending)

