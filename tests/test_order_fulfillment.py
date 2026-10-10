
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.services.order_service import update_order_item_status


def make_db_for_fulfillment(
    current_status,
    new_status,
    vendor_owns_item=True,
):
    db = AsyncMock()

    vendor = MagicMock()
    vendor.id = 20
    vendor_result = MagicMock()
    vendor_result.scalar_one_or_none.return_value = vendor

    order_item = MagicMock()
    order_item.id = 7
    order_item.order_id = 8
    order_item.status = current_status

    item_result = MagicMock()
    if vendor_owns_item:
        item_result.scalar_one_or_none.return_value = order_item
    else:
        item_result.scalar_one_or_none.return_value = None

    order = MagicMock()
    order.id = 8
    order.status = current_status

    order_result = MagicMock()
    order_result.scalar_one.return_value = order

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [
        order_item
    ]

    final_order_result = MagicMock()
    final_order_result.scalar_one.return_value = order

    db.execute.side_effect = [
        vendor_result,
        item_result,
        order_result,
        items_result,
        final_order_result,
    ]

    return db, order_item, order


@pytest.mark.asyncio
async def test_vendor_can_confirm_pending_order_item():
    db, order_item, order = make_db_for_fulfillment(
        "pending", "confirmed"
    )

    result = await update_order_item_status(
        db, user_id=4, order_id=8, item_id=7,
        new_status="confirmed",
    )

    assert order_item.status == "confirmed"
    assert order.status == "confirmed"
    assert result.id == 8
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_vendor_cannot_skip_fulfillment_status():
    db, order_item, order = make_db_for_fulfillment(
        "pending", "shipped"
    )

    with pytest.raises(HTTPException) as exc_info:
        await update_order_item_status(
            db, user_id=4, order_id=8, item_id=7,
            new_status="shipped",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "Cannot change item status from pending to shipped"
    )
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_vendor_can_ship_confirmed_order_item():
    db, order_item, order = make_db_for_fulfillment(
        "confirmed", "shipped"
    )

    result = await update_order_item_status(
        db, user_id=4, order_id=8, item_id=7,
        new_status="shipped",
    )

    assert order_item.status == "shipped"
    assert order.status == "shipped"
    assert result.id == 8
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_vendor_can_deliver_shipped_order_item():
    db, order_item, order = make_db_for_fulfillment(
        "shipped", "delivered"
    )

    result = await update_order_item_status(
        db, user_id=4, order_id=8, item_id=7,
        new_status="delivered",
    )

    assert order_item.status == "delivered"
    assert order.status == "delivered"
    assert result.id == 8
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_vendor_cannot_update_another_vendors_order_item():
    db, order_item, order = make_db_for_fulfillment(
        "pending", "confirmed", vendor_owns_item=False
    )

    with pytest.raises(HTTPException) as exc_info:
        await update_order_item_status(
            db, user_id=4, order_id=8, item_id=7,
            new_status="confirmed",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == (
        "Order item not found for this vendor"
    )
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()
