from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProductCreate(BaseModel):
    name: str
    price: float = Field(gt=0)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    user_email: EmailStr
    items: list[OrderItemCreate]


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int
    unit_price: float


class OrderItemReadWithProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product: ProductRead
    quantity: int
    unit_price: float


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_email: EmailStr
    total_amount: float
    created_at: datetime
    items: list[OrderItemRead]


class OrderDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_email: EmailStr
    total_amount: float
    created_at: datetime
    items: list[OrderItemReadWithProduct]


class PaginatedOrders(BaseModel):
    total: int
    data: list[OrderRead]
