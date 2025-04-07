from app.schemas.orders import OrderStatus, OrderItemStatus, OrderItemPublic
from fastapi import HTTPException

def get_order_status(order_items: list[OrderItemPublic]):
    received_order_items = [order_item for order_item in order_items if order_item.status == OrderItemStatus.received]
    canceled_order_items = [order_item for order_item in order_items if order_item.status == OrderItemStatus.canceled]

    if len(received_order_items) == len(order_items):
        return OrderStatus.finished
    
    if len(canceled_order_items) == len(order_items):
        return OrderStatus.canceled
    
    if len(received_order_items) + len(canceled_order_items) == len(order_items):
        return OrderStatus.partially_finished

    if [OrderItemStatus.receivable] * (len(order_items) - len(received_order_items) - len(canceled_order_items)) == [order_item.status for order_item in order_items]:
        return OrderStatus.receive_pending
    
    if OrderItemStatus.receivable in [order_item.status for order_item in order_items]:
        return OrderStatus.partially_delivered
    
    return OrderStatus.on_delivery

def get_next_order_number(order_numbers: list[int]) -> int:
    order_numbers.sort()
    for i in range(0, 1000):
        if i != order_numbers[i]:
            return i
    
    raise HTTPException(status_code=400, detail='No queue_number for order, try again later')

