
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.services.order_service import create_order_from_cart


@pytest.mark.asyncio
async def test_checkout_rejects_insufficient_stock():
    db = AsyncMock()
    db.add = MagicMock()

    cart = MagicMock()
    cart.id = 10

    cart_item = MagicMock()
    cart_item.id = 1
    cart_item.product_id = 5
    cart_item.quantity = 5

    cart_result = MagicMock()
    cart_result.scalar_one_or_none.return_value = cart

    cart_items_result = MagicMock()
    cart_items_result.scalars.return_value.all.return_value = [
        cart_item
    ]

    product = MagicMock()
    product.id = 5
    product.name = "Keyboard"
    product.price = Decimal("799.00")
    product.stock_quantity = 2
    product.is_active = True

    products_result = MagicMock()
    products_result.scalars.return_value.all.return_value = [
        product
    ]

    db.execute.side_effect = [
        cart_result,
        cart_items_result,
        products_result,
    ]

    with pytest.raises(HTTPException) as exc_info:
        await create_order_from_cart(db, user_id=3)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Insufficient stock for Keyboard"

    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()
    db.add.assert_not_called()

    # Stock must remain unchanged when checkout fails.
    assert product.stock_quantity == 2


@pytest.mark.asyncio
async def test_checkout_creates_order_and_reduces_stock():
    db = AsyncMock()
    db.add = MagicMock()

    cart = MagicMock()
    cart.id = 10

    cart_item = MagicMock()
    cart_item.id = 1
    cart_item.product_id = 5
    cart_item.quantity = 2

    cart_result = MagicMock()
    cart_result.scalar_one_or_none.return_value = cart

    cart_items_result = MagicMock()
    cart_items_result.scalars.return_value.all.return_value = [
        cart_item
    ]

    product = MagicMock()
    product.id = 5
    product.name = "Keyboard"
    product.price = Decimal("799.00")
    product.stock_quantity = 10
    product.is_active = True

    products_result = MagicMock()
    products_result.scalars.return_value.all.return_value = [
        product
    ]

    saved_order = MagicMock()
    saved_order.id = 100
    saved_order.user_id = 3
    saved_order.status = "pending"
    saved_order.total_amount = Decimal("1598.00")

    saved_order_result = MagicMock()
    saved_order_result.scalar_one.return_value = saved_order

    db.execute.side_effect = [
        cart_result,
        cart_items_result,
        products_result,
        saved_order_result,
    ]

    result = await create_order_from_cart(db, user_id=3)

    # Verify the created order.
    assert result.id == 100
    assert result.user_id == 3
    assert result.status == "pending"
    assert result.total_amount == Decimal("1598.00")

    # Two units purchased: stock decreases from 10 to 8.
    assert product.stock_quantity == 8

    # Verify that the order and order item were added.
    assert db.add.call_count == 2
    added_objects = [
        call.args[0] for call in db.add.call_args_list
    ]
    assert len(added_objects) == 2

    # Verify that the purchased cart item was removed.
    db.delete.assert_awaited_once_with(cart_item)

    # Verify successful transaction.
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()
