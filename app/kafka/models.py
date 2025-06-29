from sqlmodel import SQLModel

from app.schemas.orders import OrderPublic
from app.schemas.items import ItemSupply
from app.core.enums import DBWorkerTaskTypes


class SupplyList(SQLModel):
    items: list[ItemSupply]


class KafkaMessageNewSupply(SQLModel):
    task: DBWorkerTaskTypes | None = DBWorkerTaskTypes.items_delivered
    payload: SupplyList


class KafkaMessageNewOrder(SQLModel):
    task: DBWorkerTaskTypes | None = DBWorkerTaskTypes.new_order
    payload: OrderPublic
