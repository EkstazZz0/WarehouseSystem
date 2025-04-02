from sqlmodel import SQLModel, Field
from uuid import UUID
from datetime import datetime


class ItemBase(SQLModel):
    name: str = Field(unique=True, index=True, min_length=3, max_length=256)
    desciption: str = Field()


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    name: str | None = Field(default=None, min_length=3, max_length=256)
    desciption: str | None = Field(default=None)


class ItemPublic(ItemBase):
    item_id: UUID = Field()
    quantity: int = Field()
    reserved: int = Field()
    created_at: datetime = Field()
    updated_at: datetime = Field()


class ItemSupply(SQLModel):
    item_id: UUID = Field()
    quantity: int = Field(gt=0)
