from sqlmodel import SQLModel, Field


class ItemBase(SQLModel):
    name: str = Field()
    desciption: str = Field()
    


class ItemCreate(ItemBase):
    name: str = Field()
