from sqlmodel import SQLModel, Field
from enum import Enum
from uuid import UUID
from typing import Annotated

from app.schemas.orders import ItemsOfNewOrder, OrderPublic
from app.schemas.items import ItemSupply

class DBWorkerTaskTypes(Enum):
    items_delivered = "items_delivered"
    new_order = "new_order"


class SupplyList(SQLModel):
    items: list[ItemSupply]


class KafkaMessageNewSupply(SQLModel):
    task: DBWorkerTaskTypes | None = DBWorkerTaskTypes.items_delivered
    payload: SupplyList


class KafkaMessageNewOrder(SQLModel):
    task: DBWorkerTaskTypes | None = DBWorkerTaskTypes.new_order
    payload: OrderPublic
