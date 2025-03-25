from fastapi import APIRouter

from app.schemas.items import ItemUpdate, ItemSupply, ItemPublic, ItemCreate

from uuid import UUID

router = APIRouter(
    prefix="/api/v1/items"
)


@router.patch("/update/{item_id}")
async def update_item(item_id: UUID, item: ItemUpdate):
    pass


@router.put("/deliver")
async def item_supply(items: list[ItemSupply]):
    pass

@router.post("/create", response_model=ItemPublic)
async def create_item(item: ItemCreate):
    pass