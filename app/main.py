import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.config import SEED_ADMIN_EMAIL, SEED_ADMIN_NAME, SEED_ADMIN_PASSWORD
from app.domain import OrderChannel, OrderStatus, PaymentStatus, Role
from app.models import (AuditLog, Inventory, LoyaltyLedger, Order, Payment, Product,
                       Promotion, StockMovement, Unit, UnitCatalog, User)
from app.schemas import (CatalogEntryCreate, CatalogEntryOut, LoginInput,
                         LoyaltyConsentUpdate, OrderCreate, OrderOut, PaymentOut,
                         PaymentRequest, ProductCreate, ProductOut,
                         PromotionCreate, StatusUpdate, StockMovementCreate,
                         StaffCreate, StockOut, TokenOut, UnitCreate, UnitOut, UserOut,
                         UserRegister)
from app.security import TOKEN_TTL, create_access_token, get_current_user, hash_password, require_roles, verify_password
from app.services import audit, create_order, get_order, mock_payment, update_order_status


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        admin_email = SEED_ADMIN_EMAIL
        if db.scalar(select(User.id).where(User.email == admin_email)) is None:
            db.add(User(name=SEED_ADMIN_NAME,
                        email=admin_email,
                        password_hash=hash_password(SEED_ADMIN_PASSWORD),
                        role=Role.ADMIN.value))
        if db.scalar(select(Unit.id).limit(1)) is None:
            unit = Unit(name="Unidade Centro", address="Av. Principal, 100")
            db.add(unit)
            db.flush()
            for name, desc, cents, qty in [
                ("X-Burger", "Hambúrguer, queijo e salada", 2290, 30),
                ("Suco de laranja", "Copo 300 ml", 850, 25),
            ]:
                product = Product(name=name, description=desc)
                db.add(product)
                db.flush()
                db.add(UnitCatalog(unit_id=unit.id, product_id=product.id, price_cents=cents))
                db.add(Inventory(unit_id=unit.id, product_id=product.id, quantity=qty))
        db.commit()
    yield


app = FastAPI(
    title="API da Rede de Lanchonetes Raízes do Nordeste",
    description="Pedidos multicanal com estoque por unidade e pagamento simulado.",
    version="2.0.0",
    lifespan=lifespan,
)
logger = logging.getLogger("lanchonete.api")


def error_body(request: Request, error: str, message: str, details=None):
    return {"error": error, "message": message, "details": details or [],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "path": request.url.path,
            "requestId": request.headers.get("X-Request-ID", str(uuid.uuid4()))}


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    labels = {400: "REQUISICAO_INVALIDA", 401: "NAO_AUTENTICADO", 403: "SEM_PERMISSAO",
              404: "NAO_ENCONTRADO", 409: "CONFLITO_REGRA_NEGOCIO", 422: "VALIDACAO"}
    return JSONResponse(status_code=exc.status_code,
                        content=error_body(request, labels.get(exc.status_code, "ERRO_HTTP"), str(exc.detail)),
                        headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    details = [{"field": ".".join(str(part) for part in e["loc"] if part != "body"),
                "issue": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content=error_body(request, "VALIDACAO", "Dados enviados são inválidos.", details))


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content=error_body(request, "CONFLITO", "Registro duplicado ou relacionamento inválido."))


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logger.exception("Falha nao tratada na API", extra={"path": request.url.path})
    return JSONResponse(status_code=500,
                         content=error_body(request, "ERRO_INTERNO", "Não foi possível concluir a solicitação."))


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "service": "lanchonete-api"}


@app.post("/auth/register", response_model=UserOut, status_code=201, tags=["Autenticação"])
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(User.email == str(payload.email).lower())):
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
    user = User(name=payload.name, email=str(payload.email).lower(),
                password_hash=hash_password(payload.password), role=Role.CLIENTE.value,
                loyalty_consent=payload.loyalty_consent,
                loyalty_consent_at=datetime.utcnow() if payload.loyalty_consent else None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/users/staff", response_model=UserOut, status_code=201, tags=["Usuários"])
def create_staff(payload: StaffCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    email = str(payload.email).lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
    staff = User(name=payload.name, email=email, password_hash=hash_password(payload.password),
                 role=payload.role.value, loyalty_consent=False)
    db.add(staff)
    db.flush()
    audit(db, user.id, "USUARIO_INTERNO_CRIADO", "usuario", str(staff.id), {"perfil": staff.role})
    db.commit()
    db.refresh(staff)
    return staff


@app.post("/auth/login", response_model=TokenOut, tags=["Autenticação"])
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    return TokenOut(access_token=create_access_token(user), expires_in=TOKEN_TTL, user=user)


@app.get("/auth/me", response_model=UserOut, tags=["Autenticação"])
def me(user: User = Depends(get_current_user)):
    return user


@app.get("/units", response_model=list[UnitOut], tags=["Unidades"])
def list_units(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100),
               db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE", "ATENDENTE", "COZINHA"))):
    return db.scalars(select(Unit).order_by(Unit.id).offset((page - 1) * limit).limit(limit)).all()


@app.post("/units", response_model=UnitOut, status_code=201, tags=["Unidades"])
def create_unit(payload: UnitCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE"))):
    unit = Unit(**payload.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    audit(db, user.id, "UNIDADE_CRIADA", "unidade", str(unit.id))
    db.commit()
    return unit


@app.post("/products", response_model=ProductOut, status_code=201, tags=["Produtos"])
def create_product(payload: ProductCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE"))):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    audit(db, user.id, "PRODUTO_CRIADO", "produto", str(product.id))
    db.commit()
    return product


@app.get("/products", response_model=list[ProductOut], tags=["Produtos"])
def list_products(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100),
                  db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE", "ATENDENTE"))):
    return db.scalars(select(Product).order_by(Product.id).offset((page - 1) * limit).limit(limit)).all()


@app.post("/units/{unit_id}/catalog", response_model=CatalogEntryOut, status_code=201, tags=["Cardápio"])
def add_catalog_entry(unit_id: int, payload: CatalogEntryCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE"))):
    unit = db.get(Unit, unit_id)
    product = db.get(Product, payload.product_id)
    if unit is None or product is None:
        raise HTTPException(status_code=404, detail="Unidade ou produto não encontrado.")
    entry = UnitCatalog(unit_id=unit_id, product_id=payload.product_id,
                        price_cents=payload.price_cents, available=payload.available)
    db.add(entry)
    db.flush()
    if db.scalar(select(Inventory.id).where(Inventory.unit_id == unit_id, Inventory.product_id == product.id)) is None:
        db.add(Inventory(unit_id=unit_id, product_id=product.id, quantity=0))
    audit(db, user.id, "ITEM_CARDAPIO_CRIADO", "cardapio", str(entry.id))
    db.commit()
    return CatalogEntryOut(unit_id=unit_id, product_id=product.id, name=product.name,
                           description=product.description, price_cents=entry.price_cents,
                           available=entry.available, stock=0)


@app.get("/catalog/{unit_id}", response_model=list[CatalogEntryOut], tags=["Cardápio"])
def get_catalog(unit_id: int, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    if db.get(Unit, unit_id) is None:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
    entries = db.scalars(select(UnitCatalog).where(UnitCatalog.unit_id == unit_id, UnitCatalog.available.is_(True))
                         .order_by(UnitCatalog.id).offset((page - 1) * limit).limit(limit)).all()
    result = []
    for entry in entries:
        stock = db.scalar(select(Inventory.quantity).where(Inventory.unit_id == unit_id, Inventory.product_id == entry.product_id)) or 0
        result.append(CatalogEntryOut(unit_id=unit_id, product_id=entry.product_id, name=entry.product.name,
                                      description=entry.product.description, price_cents=entry.price_cents,
                                      available=entry.available and stock > 0, stock=stock))
    return result


@app.get("/stock", response_model=list[StockOut], tags=["Estoque"])
def list_stock(unit_id: int = Query(gt=0), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
               db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE", "ATENDENTE", "COZINHA"))):
    rows = db.scalars(select(Inventory).where(Inventory.unit_id == unit_id).order_by(Inventory.product_id)
                      .offset((page - 1) * limit).limit(limit)).all()
    return [StockOut(unit_id=row.unit_id, product_id=row.product_id, quantity=row.quantity) for row in rows]


@app.post("/stock/movements", status_code=201, tags=["Estoque"])
def move_stock(payload: StockMovementCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE"))):
    inventory = db.scalar(select(Inventory).where(Inventory.unit_id == payload.unit_id, Inventory.product_id == payload.product_id))
    if inventory is None:
        raise HTTPException(status_code=404, detail="Saldo de estoque não encontrado para a unidade e produto.")
    if payload.movement_type == "SAIDA" and inventory.quantity < payload.quantity:
        raise HTTPException(status_code=409, detail="Estoque insuficiente para esta saída.")
    inventory.quantity += payload.quantity if payload.movement_type == "ENTRADA" else -payload.quantity
    movement = StockMovement(inventory_id=inventory.id, user_id=user.id, movement_type=payload.movement_type,
                             quantity=payload.quantity, reason=payload.reason)
    db.add(movement)
    audit(db, user.id, "ESTOQUE_MOVIMENTADO", "estoque", str(inventory.id), payload.model_dump())
    db.commit()
    return {"movement_id": movement.id, "unit_id": payload.unit_id, "product_id": payload.product_id,
            "quantity": inventory.quantity}


@app.post("/promotions", status_code=201, tags=["Promoções"])
def create_promotion(payload: PromotionCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE"))):
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=422, detail="A promoção deve terminar depois de começar.")
    promotion = Promotion(**payload.model_dump())
    db.add(promotion)
    audit(db, user.id, "PROMOCAO_CRIADA", "promocao", promotion.code)
    db.commit()
    db.refresh(promotion)
    return {"id": promotion.id, "code": promotion.code, "percent_off": promotion.percent_off,
            "starts_at": promotion.starts_at, "ends_at": promotion.ends_at, "active": promotion.active}


@app.post("/orders", response_model=OrderOut, status_code=201, tags=["Pedidos"])
def create_order_route(payload: OrderCreate, idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=80),
                       db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE", "ATENDENTE", "CLIENTE"))):
    return create_order(db, user, payload, idempotency_key)


@app.get("/orders", response_model=list[OrderOut], tags=["Pedidos"])
def list_orders(unit_id: int | None = Query(default=None, gt=0), channel: OrderChannel | None = Query(default=None, alias="canalPedido"),
                order_status: OrderStatus | None = Query(default=None, alias="status"),
                page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE", "ATENDENTE", "COZINHA", "CLIENTE"))):
    query = select(Order).order_by(Order.created_at.desc()).offset((page - 1) * limit).limit(limit)
    if unit_id is not None:
        query = query.where(Order.unit_id == unit_id)
    if channel:
        query = query.where(Order.channel == channel.value)
    if order_status:
        query = query.where(Order.status == order_status.value)
    if user.role == "CLIENTE":
        query = query.where(Order.customer_id == user.id)
    return db.scalars(query).all()


@app.get("/orders/{order_id}", response_model=OrderOut, tags=["Pedidos"])
def read_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "GERENTE", "ATENDENTE", "COZINHA", "CLIENTE"))):
    order = get_order(db, order_id)
    if user.role == "CLIENTE" and order.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Pedido pertence a outro cliente.")
    audit(db, user.id, "PEDIDO_CONSULTADO", "pedido", str(order.id))
    db.commit()
    return order


@app.post("/orders/{order_id}/cancel", response_model=OrderOut, tags=["Pedidos"])
def cancel_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = get_order(db, order_id)
    if user.role == "CLIENTE" and order.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Pedido pertence a outro cliente.")
    if user.role not in {"CLIENTE", "ADMIN", "GERENTE", "ATENDENTE"}:
        raise HTTPException(status_code=403, detail="Perfil sem permissão para cancelar pedido.")
    return update_order_status(db, user, order_id, OrderStatus.CANCELADO)


@app.patch("/orders/{order_id}/status", response_model=OrderOut, tags=["Pedidos"])
def change_order_status(order_id: int, payload: StatusUpdate, db: Session = Depends(get_db),
                        user: User = Depends(require_roles("ADMIN", "GERENTE", "COZINHA"))):
    if payload.status == OrderStatus.CANCELADO:
        raise HTTPException(status_code=422, detail="Use POST /orders/{id}/cancel para cancelar.")
    return update_order_status(db, user, order_id, payload.status)


@app.post("/payments/{order_id}/mock", response_model=PaymentOut, status_code=201, tags=["Pagamentos"])
def pay_mock(order_id: int, payload: PaymentRequest, db: Session = Depends(get_db),
             user: User = Depends(require_roles("ADMIN", "GERENTE", "ATENDENTE", "CLIENTE"))):
    return mock_payment(db, user, order_id, payload.outcome, payload.payment_method)


@app.get("/loyalty/me", tags=["Fidelidade"])
def loyalty_balance(user: User = Depends(require_roles("CLIENTE")), db: Session = Depends(get_db)):
    if not user.loyalty_consent:
        return {"enrolled": False, "message": "Cliente não consentiu com o programa de fidelidade."}
    return {"enrolled": True, "points": user.points_balance, "conversion": "100 pontos equivalem a R$ 1,00 em desconto"}


@app.get("/loyalty/history", tags=["Fidelidade"])
def loyalty_history(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                    db: Session = Depends(get_db), user: User = Depends(require_roles("CLIENTE"))):
    if not user.loyalty_consent:
        raise HTTPException(status_code=403, detail="É necessário consentir com o programa de fidelidade.")
    entries = db.scalars(select(LoyaltyLedger).where(LoyaltyLedger.user_id == user.id)
                         .order_by(LoyaltyLedger.created_at.desc()).offset((page - 1) * limit).limit(limit)).all()
    return entries


@app.patch("/loyalty/consent", tags=["Fidelidade"])
def update_loyalty_consent(payload: LoyaltyConsentUpdate, db: Session = Depends(get_db),
                           user: User = Depends(require_roles("CLIENTE"))):
    user.loyalty_consent = payload.consent
    user.loyalty_consent_at = datetime.utcnow() if payload.consent else None
    if not payload.consent:
        user.points_balance = 0
    audit(db, user.id, "CONSENTIMENTO_FIDELIDADE_ATUALIZADO", "usuario", str(user.id),
          {"consentimento": payload.consent})
    db.commit()
    return {"loyalty_consent": user.loyalty_consent,
            "loyalty_consent_at": user.loyalty_consent_at,
            "points": user.points_balance}


@app.get("/audit", tags=["Auditoria"])
def list_audit(page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100),
               db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    return db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)).all()


@app.delete("/privacy/me", status_code=204, tags=["Privacidade"])
def anonymize_my_account(db: Session = Depends(get_db), user: User = Depends(require_roles("CLIENTE"))):
    user_id = user.id
    user.name = "Cliente anonimizado"
    user.email = f"anon-{user.id}-{uuid.uuid4().hex[:12]}@invalid.local"
    user.password_hash = hash_password(uuid.uuid4().hex)
    user.active = False
    user.loyalty_consent = False
    user.loyalty_consent_at = None
    user.points_balance = 0
    for order in db.scalars(select(Order).where(Order.customer_id == user_id)).all():
        order.customer_id = None
    audit(db, user_id, "DADOS_PESSOAIS_ANONIMIZADOS", "usuario", str(user_id))
    db.commit()
    return JSONResponse(status_code=204, content=None)
