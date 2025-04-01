from sqlmodel import create_engine, Session
import os
from fastapi import Depends
from typing import Annotated

from app.core.config import db_connect_url


connect_args = {"check_same_thread": False}

engine=create_engine(db_connect_url, connect_args=connect_args, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
