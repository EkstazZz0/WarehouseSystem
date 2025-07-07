import pytest
from app.db.models import Order, Item, OrderItem
from datatest import create_items, update_items, generate_supply_item_model
from httpx import AsyncClient


@pytest.fixture
async def test_1_create_items(async_client: AsyncClient):
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
        created_items.append(data)
    
    response = await async_client.post("/api/v1/items/create", json=create_items[0])
    assert response.status_code == 422
    
    return created_items


@pytest.fixture
async def test_2_get_items(async_client: AsyncClient, test_1_create_items):
    response = await async_client.get("api/v1/items/")

    assert response.status_code == 200
    assert response.json() == test_1_create_items

    for item in test_1_create_items:
        response = await async_client.get(f"api/v1/items/{item["item_id"]}")

        assert response.status_code == 200
        assert response.json() == item

    return test_1_create_items


@pytest.fixture
async def test_3_update_items(async_client: AsyncClient, test_2_get_items):
    items = []
    for update_item, created_item in zip(update_items, test_2_get_items):
        response = await async_client.patch(f'api/v1/items/update/{created_item["item_id"]}', json=update_item)
        assert response.status_code == 200
        
        data = response.json()

        if update_item.get("name"):
            assert update_item["name"] == data["name"]
        
        if update_item.get("description"):
            assert update_item["description"] == data["description"]
        
        items.append(data)
    
    return items


async def test_4_supply_items(async_client: AsyncClient, test_3_update_items):
    quantities = []
    for item in test_3_update_items:
        request_model = generate_supply_item_model(item_ids=[item["item_id"]])
        response = await async_client.put("api/v1/items/deliver", json=generate_supply_item_model(item_ids=[item["item_id"]]))
        assert response.status_code == 200
        assert response.json() == {"success": True}
        quantities.append(request_model[0]["quantity"])
    
    item_ids = []
    for i in range(2):
        item_ids.append(test_3_update_items[i]["item_id"])
    
    request_model = generate_supply_item_model(item_ids=item_ids)

    for i in range(len(request_model)):
        quantities[i] += request_model[i]["quantity"]
    
    response = await async_client.put("api/v1/items/deliver", json=request_model)
    assert response.status_code == 200
    assert response.json() == {"success": True}

    item_ids = []
    for i in range(1, 3):
        item_ids.append(test_3_update_items[i]["item_id"])
    
    request_model = generate_supply_item_model(item_ids=item_ids)

    for i in range(1, 3):
        quantities[i] += request_model[i-1]["quantity"]

    response = await async_client.put("api/v1/items/deliver", json=request_model)
    assert response.status_code == 200
    assert response.json() == {"success": True}

    db_items = (await async_client.get("api/v1/items")).json()

    for item, quantity in zip(test_3_update_items, quantities):
        assert next((db_item for db_item in db_items if db_item["item_id"] == item["item_id"]))["quantity"] == quantity
    
    return db_items

    