from sqlmodel import SQLModel, Field
from uuid import UUID

from app.schemas.items import ItemBase

class Item(ItemBase, table=True):
    item_id: UUID = Field(primary_key=True)
    name: str = Field(unique=True)
    description: str = Field()
    quantity: int = Field()

