from sqlmodel import SQLModel
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.db.session import engine, SessionDep
from app.db.models import Item
from app.schemas.items import ItemCreate, ItemUpdate


def init_db():
    SQLModel.metadata.create_all(engine)


def drop_db():
    SQLModel.metadata.drop_all(engine)


def create_item(session: SessionDep, item: ItemCreate) -> Item:
    db_item = Item.model_validate(item)
    session.add(db_item)

    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f'Item with name: {item.name} is already exists in database. It should be unique')
    
    session.refresh(db_item)
    return db_item


def update_item(item_id: UUID, item: ItemUpdate, session: SessionDep):
    db_item = session.get(Item, item_id)

    if not db_item:
        raise HTTPException(status_code=400, detail=f'Item with id: {item_id} does not exists in database.')
    
    item_data = item.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(item_data)
    session.add(db_item)

    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f'Item with name: {item.name} is already exists in database. It should be unique')
    
    session.refresh(db_item)
    return db_item


def take_delivery():
    pass


