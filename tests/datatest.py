import random
from uuid import UUID

create_item1 = {
    "name": "Item1",
    "description": "Some description of Item 1"
}

create_items = [
    {
        "name": "Item1",
        "description": "Some description of Item 1"
    },
    {
        "name": "Item2",
        "description": "Some description of Item 2"
    },
    {
        "name": "Item3",
        "description": "Some description of Item 3"
    }
]

update_items = [
    {
        "name": "Extremely Item 1"
    },
    {
        "description": "Really some desc of item 2"
    },
    {
        "name": "Extremely Item 3",
        "description": "Really some desc of item 3",
    }
]

def generate_supply_item_model(item_ids):
    result = []
    for item_id in item_ids:
        quantity = random.randint(1, 13)
        result.append({
            "item_id": item_id,
            "quantity": quantity
        })

    return result
