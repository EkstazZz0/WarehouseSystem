from sqlmodel import SQLModel, Field
from uuid import UUID


class ItemBase(SQLModel):
    name: str = Field(unique=True, index=True)
    desciption: str = Field()
    quantity: int | None = Field(default=0)
    


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    name: str | None = Field(default=None)
    desciption: str | None = Field(default=None)
    quantity: int | None = Field(default=0)


class ItemPublic(ItemBase):
    item_id: UUID = Field()


class ItemSupply(SQLModel):
    item_id: UUID = Field()
    quantity: int = Field(gt=0)
