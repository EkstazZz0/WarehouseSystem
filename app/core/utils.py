from app.schemas.orders import OrderStatus, OrderItemStatus, OrderItemPublic

def get_order_status(order_items: list[OrderItemPublic]):
    if [OrderItemStatus.receivable] * len(order_items) == [order_item.status for order_item in order_items]:
        return OrderStatus.receive_pending
    
    if OrderItemStatus.receivable in [order_item.status for order_item in order_items]:
        return OrderStatus.partially_delivered
    
    return OrderStatus.on_delivery
