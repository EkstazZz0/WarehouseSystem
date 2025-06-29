import pytest
from app.db.models import Order, Item, OrderItem
from datatest import create_items, update_items
from httpx import AsyncClient


async def test_create_items(async_client: AsyncClient):
    created_items = []
    for create_item in create_items:
        response = await async_client.post("/api/v1/items/create", json=create_item)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == create_item["name"]
        assert data["description"] == create_item["description"]
        assert "item_id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["quantity"] == 0
        assert data["reserved"] == 0
        created_items.append(data["item_id"])
    
    return created_items


async def test_1_get_items(async_client: AsyncClient, test_create_items):
    response = await async_client.get("api/v1/items/")
    assert response.status_code == 200
    assert response.json() == test_create_items


# async def test_2_update_items(async_client: AsyncClient, test_create_items):
#     for update_item, created_item in zip(update_items, test_create_items):
#         response = await async_client.patch(f'api/v1/items/update/{created_item["id"]}', json=update_item)
#         assert response.status_code == 200
        
#         data = response.json()

#         if update_item.get("name"):
#             assert update_item["name"] == data["name"]
        
#         if update_item.get("description"):
#             assert update_item["description"] == data["description"]

    