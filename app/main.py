from fastapi import FastAPI
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from app.db.repository import init_db, drop_db
from app.api.v1.endpoints.items import router as item_router
from app.api.v1.endpoints.orders import router as order_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    pass

app = FastAPI(lifespan=lifespan)
app.include_router(item_router)
app.include_router(order_router)

if __name__ == '__main__':
    drop_db()
    init_db()