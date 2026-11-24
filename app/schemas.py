from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain import OrderChannel, OrderStatus, PaymentStatus, Role


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class UserRegister(InputModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    loyalty_consent: bool = False


class StaffCreate(InputModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: Role


class LoginInput(InputModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Role
    loyalty_consent: bool

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserOut


class UnitCreate(InputModel):
    name: str = Field(min_length=2, max_length=120)
    address: str = Field(min_length=5, max_length=240)


class UnitOut(BaseModel):
    id: int
    name: str
    address: str
    active: bool
    model_config = ConfigDict(from_attributes=True)


class ProductCreate(InputModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class CatalogEntryCreate(InputModel):
    product_id: int = Field(gt=0)
    price_cents: int = Field(gt=0)
    available: bool = True


class CatalogEntryOut(BaseModel):
    unit_id: int
    product_id: int
    name: str
    description: str | None
    price_cents: int
    available: bool
    stock: int


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    active: bool
    model_config = ConfigDict(from_attributes=True)


class StockMovementCreate(InputModel):
    unit_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    movement_type: str = Field(pattern="^(ENTRADA|SAIDA)$")
    quantity: int = Field(gt=0, le=10000)
    reason: str = Field(min_length=3, max_length=200)


class StockOut(BaseModel):
    unit_id: int
    product_id: int
    quantity: int


class OrderItemInput(InputModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=99)


class OrderCreate(InputModel):
    unit_id: int = Field(gt=0)
    channel: OrderChannel = Field(alias="canalPedido")
    items: list[OrderItemInput] = Field(min_length=1, max_length=30)
    promotion_code: str | None = Field(default=None, max_length=40)
    redeem_points: int = Field(default=0, ge=0)


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price_cents: int


class OrderOut(BaseModel):
    id: int
    unit_id: int
    customer_id: int | None
    channel: OrderChannel = Field(serialization_alias="canalPedido")
    status: OrderStatus
    promotion_code: str | None
    subtotal_cents: int
    discount_cents: int
    total_cents: int
    idempotency_key: str
    created_at: datetime
    items: list[OrderItemOut]
    model_config = ConfigDict(from_attributes=True)


class PaymentRequest(InputModel):
    outcome: PaymentStatus
    payment_method: str = Field(min_length=2, max_length=30)


class PaymentOut(BaseModel):
    id: int
    order_id: int
    status: PaymentStatus
    provider: str
    request_payload: str
    response_payload: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StatusUpdate(InputModel):
    status: OrderStatus


class PromotionCreate(InputModel):
    code: str = Field(min_length=3, max_length=40, pattern="^[A-Z0-9_-]+$")
    percent_off: int = Field(gt=0, le=80)
    starts_at: datetime
    ends_at: datetime


class LoyaltyRedeem(InputModel):
    points: int = Field(gt=0)


class LoyaltyConsentUpdate(InputModel):
    consent: bool
