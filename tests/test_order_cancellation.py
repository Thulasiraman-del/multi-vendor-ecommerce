
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.services.order_service import cancel_order


@pytest.mark.asyncio
async def test_cancel_pending_order_restores_stock():
    db = AsyncMock()

    order = MagicMock()
    order.id = 100
    order.user_id = 3
    order.status = "pending"

    order_item = MagicMock()
    order_item.product_id = 5
    order_item.quantity = 2
    order_item.status = "pending"

    product = MagicMock()
    product.id = 5
    product.stock_quantity = 8

    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = order

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [
        order_item
    ]

    products_result = MagicMock()
    products_result.scalars.return_value.all.return_value = [
        product
    ]

    final_order_result = MagicMock()
    final_order_result.scalar_one.return_value = order

    db.execute.side_effect = [
        order_result,
        items_result,
        products_result,
        final_order_result,
    ]

    result = await cancel_order(
        db,
        user_id=3,
        order_id=100,
    )

    assert result.id == 100
    assert order.status == "cancelled"
    assert order_item.status == "cancelled"

    # Two cancelled units are returned to stock.
    assert product.stock_quantity == 10

    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_order_rejects_non_pending_order():
    db = AsyncMock()

    order = MagicMock()
    order.id = 100
    order.user_id = 3
    order.status = "shipped"

    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = order

    db.execute.return_value = order_result

    with pytest.raises(HTTPException) as exc_info:
        await cancel_order(
            db,
            user_id=3,
            order_id=100,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "Only pending orders can be cancelled"
    )

    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()
