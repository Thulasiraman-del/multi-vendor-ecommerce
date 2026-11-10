
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------
# CREATE PRODUCT
# --------------------------------------------------

class ProductCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    sku: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0)
    stock_quantity: int = Field(ge=0)


# --------------------------------------------------
# PRODUCT RESPONSE
# --------------------------------------------------

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_id: int
    category_id: int
    name: str
    description: str | None
    sku: str
    price: Decimal
    stock_quantity: int
    is_active: bool


# --------------------------------------------------
# UPDATE PRODUCT
# --------------------------------------------------

class ProductUpdate(BaseModel):
    category_id: int | None = None

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    description: str | None = None

    price: Decimal | None = Field(
        default=None,
        gt=0,
    )

    stock_quantity: int | None = Field(
        default=None,
        ge=0,
    )

    is_active: bool | None = None


# --------------------------------------------------
# PRODUCT PAGINATION RESPONSE
# --------------------------------------------------

class ProductPagination(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    limit: int
    pages: int


# --------------------------------------------------
# PRODUCT PAGINATION PARAMETERS
# --------------------------------------------------

class ProductPaginationParams(BaseModel):
    page: int = Field(
        default=1,
        ge=1,
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )
