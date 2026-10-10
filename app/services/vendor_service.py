
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate


async def get_vendor_by_user_id(
    db: AsyncSession,
    user_id: int,
) -> Vendor | None:
    result = await db.execute(
        select(Vendor).where(
            Vendor.user_id == user_id
        )
    )

    return result.scalar_one_or_none()


async def create_vendor(
    db: AsyncSession,
    user_id: int,
    vendor_data: VendorCreate,
) -> Vendor:
    vendor = Vendor(
        user_id=user_id,
        business_name=vendor_data.business_name,
        business_description=vendor_data.business_description,
    )

    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)

    return vendor