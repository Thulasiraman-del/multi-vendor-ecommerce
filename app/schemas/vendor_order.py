from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
class VendorOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    order_id: int
    order_item_id: int
    order_date: datetime
    order_status: str
    item_status: str
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    customer_id: int
