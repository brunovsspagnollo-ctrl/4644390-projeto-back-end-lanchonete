from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(20), default="CLIENTE")
    loyalty_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    loyalty_consent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    points_balance: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Unit(Base):
    __tablename__ = "units"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    address: Mapped[str] = mapped_column(String(240))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class UnitCatalog(Base):
    __tablename__ = "unit_catalog"
    __table_args__ = (UniqueConstraint("unit_id", "product_id", name="uq_catalog_unit_product"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    price_cents: Mapped[int] = mapped_column(Integer)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    product: Mapped[Product] = relationship()


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("unit_id", "product_id", name="uq_inventory_unit_product"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    movement_type: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Promotion(Base):
    __tablename__ = "promotions"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    percent_off: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(12), index=True)
    status: Mapped[str] = mapped_column(String(32), default="AGUARDANDO_PAGAMENTO", index=True)
    promotion_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    subtotal_cents: Mapped[int] = mapped_column(Integer)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_cents: Mapped[int] = mapped_column(Integer)
    points_redeemed: Mapped[int] = mapped_column(Integer, default=0)
    idempotency_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_cents: Mapped[int] = mapped_column(Integer)
    order: Mapped[Order] = relationship(back_populates="items")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16))
    provider: Mapped[str] = mapped_column(String(40), default="GATEWAY_MOCK")
    request_payload: Mapped[str] = mapped_column(Text)
    response_payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LoyaltyLedger(Base):
    __tablename__ = "loyalty_ledger"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    points_delta: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    resource: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(80))
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
