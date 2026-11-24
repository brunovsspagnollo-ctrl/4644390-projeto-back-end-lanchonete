import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.domain import OrderStatus, PaymentStatus
from app.models import (
    AuditLog, Inventory, LoyaltyLedger, Order, OrderItem, Payment, Promotion,
    StockMovement, Unit, UnitCatalog, User,
)
from app.schemas import OrderCreate


def audit(db: Session, user_id: int | None, action: str, resource: str, resource_id: str, details=None):
    db.add(AuditLog(user_id=user_id, action=action, resource=resource,
                    resource_id=resource_id, details=json.dumps(details or {}, ensure_ascii=False)))


def get_order(db: Session, order_id: int) -> Order:
    order = db.scalar(select(Order).options(selectinload(Order.items)).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return order


def create_order(db: Session, actor: User, payload: OrderCreate, idempotency_key: str) -> Order:
    old = db.scalar(select(Order).options(selectinload(Order.items)).where(Order.idempotency_key == idempotency_key))
    if old:
        if old.customer_id not in (None, actor.id) and actor.role not in {"ADMIN", "GERENTE"}:
            raise HTTPException(status_code=409, detail="Chave de idempotência já utilizada.")
        return old

    unit = db.get(Unit, payload.unit_id)
    if unit is None or not unit.active:
        raise HTTPException(status_code=404, detail="Unidade não encontrada ou inativa.")
    if actor.role == "CLIENTE" and not actor.active:
        raise HTTPException(status_code=403, detail="Cliente inativo.")

    quantities: dict[int, int] = {}
    for item in payload.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity

    order_items: list[OrderItem] = []
    inventories: list[tuple[Inventory, int]] = []
    subtotal = 0
    for product_id, quantity in quantities.items():
        catalog = db.scalar(select(UnitCatalog).where(
            UnitCatalog.unit_id == unit.id,
            UnitCatalog.product_id == product_id,
            UnitCatalog.available.is_(True),
        ))
        inventory = db.scalar(select(Inventory).where(
            Inventory.unit_id == unit.id, Inventory.product_id == product_id,
        ))
        if catalog is None:
            raise HTTPException(status_code=404, detail=f"Produto {product_id} não consta no cardápio da unidade.")
        if inventory is None or inventory.quantity < quantity:
            raise HTTPException(status_code=409, detail=f"Estoque insuficiente para o produto {product_id}.")
        inventories.append((inventory, quantity))
        subtotal += catalog.price_cents * quantity
        order_items.append(OrderItem(product_id=product_id, quantity=quantity, unit_price_cents=catalog.price_cents))

    discount = 0
    promotion = None
    if payload.promotion_code:
        promotion = db.scalar(select(Promotion).where(Promotion.code == payload.promotion_code.upper()))
        now = datetime.now()
        if promotion is None or not promotion.active or not (promotion.starts_at <= now <= promotion.ends_at):
            raise HTTPException(status_code=409, detail="Cupom inexistente, inativo ou fora da validade.")
        discount = subtotal * promotion.percent_off // 100

    points = payload.redeem_points
    if points:
        if actor.role != "CLIENTE" or not actor.loyalty_consent:
            raise HTTPException(status_code=409, detail="Resgate exige cliente com consentimento de fidelidade.")
        if actor.points_balance < points:
            raise HTTPException(status_code=409, detail="Saldo de pontos insuficiente.")
        if points > subtotal - discount:
            raise HTTPException(status_code=409, detail="Resgate excede o valor restante do pedido.")
        discount += points

    discount = min(discount, subtotal)
    total = subtotal - discount
    if total <= 0:
        raise HTTPException(status_code=422, detail="O pedido precisa ter valor maior que zero após descontos.")

    order = Order(
        unit_id=unit.id,
        customer_id=actor.id if actor.role == "CLIENTE" else None,
        channel=payload.channel.value,
        status=OrderStatus.AGUARDANDO_PAGAMENTO.value,
        promotion_code=promotion.code if promotion else None,
        subtotal_cents=subtotal,
        discount_cents=discount,
        total_cents=total,
        points_redeemed=points,
        idempotency_key=idempotency_key,
        items=order_items,
    )
    db.add(order)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Chave de idempotência já utilizada.")

    for inventory, quantity in inventories:
        changed = db.execute(
            update(Inventory)
            .where(Inventory.id == inventory.id, Inventory.quantity >= quantity)
            .values(quantity=Inventory.quantity - quantity)
            .execution_options(synchronize_session=False)
        )
        if changed.rowcount != 1:
            db.rollback()
            raise HTTPException(status_code=409, detail="Estoque insuficiente para concluir a reserva.")
        db.add(StockMovement(inventory_id=inventory.id, user_id=actor.id,
                             movement_type="SAIDA", quantity=quantity,
                             reason=f"Reserva do pedido {order.id}"))
    if points:
        actor.points_balance -= points
        db.add(LoyaltyLedger(user_id=actor.id, order_id=order.id,
                             points_delta=-points, reason="Resgate no pedido"))
    audit(db, actor.id, "PEDIDO_CRIADO", "pedido", str(order.id), {"canal": order.channel, "total_centavos": total})
    db.commit()
    return get_order(db, order.id)


def mock_payment(db: Session, actor: User, order_id: int, outcome: PaymentStatus, method: str) -> Payment:
    order = get_order(db, order_id)
    if actor.role == "CLIENTE" and order.customer_id != actor.id:
        raise HTTPException(status_code=403, detail="Pedido pertence a outro cliente.")
    if order.status != OrderStatus.AGUARDANDO_PAGAMENTO.value:
        raise HTTPException(status_code=409, detail="Pedido não aguarda pagamento.")
    if db.scalar(select(Payment.id).where(Payment.order_id == order.id)):
        raise HTTPException(status_code=409, detail="Pagamento deste pedido já foi processado.")

    approved = outcome == PaymentStatus.APROVADO
    response = {"gateway": "GATEWAY_MOCK", "status": outcome.value,
                "transaction_id": f"MOCK-{order.id}-{datetime.now():%Y%m%d%H%M%S}",
                "amount_cents": order.total_cents,
                "message": "Pagamento aprovado." if approved else "Pagamento recusado pelo simulador."}
    payment = Payment(order_id=order.id, status=outcome.value,
                      request_payload=json.dumps({"payment_method": method, "amount_cents": order.total_cents}),
                      response_payload=json.dumps(response, ensure_ascii=False))
    db.add(payment)
    if approved:
        order.status = OrderStatus.PAGO.value
        if order.customer_id:
            customer = db.get(User, order.customer_id)
            if customer and customer.loyalty_consent:
                earned = order.total_cents // 1000  # 1 ponto por R$ 10,00 pagos
                if earned:
                    customer.points_balance += earned
                    db.add(LoyaltyLedger(user_id=customer.id, order_id=order.id,
                                         points_delta=earned, reason="Pontos por compra aprovada"))
    else:
        order.status = OrderStatus.CANCELADO.value
        _restore_order_stock(db, order, actor.id, "Pagamento recusado")
        if order.customer_id and order.points_redeemed:
            customer = db.get(User, order.customer_id)
            customer.points_balance += order.points_redeemed
            db.add(LoyaltyLedger(user_id=customer.id, order_id=order.id,
                                 points_delta=order.points_redeemed, reason="Estorno por pagamento recusado"))
    audit(db, actor.id, "PAGAMENTO_MOCK", "pedido", str(order.id), response)
    db.commit()
    db.refresh(payment)
    return payment


def _restore_order_stock(db: Session, order: Order, user_id: int, reason: str):
    for item in order.items:
        inventory = db.scalar(select(Inventory).where(
            Inventory.unit_id == order.unit_id, Inventory.product_id == item.product_id,
        ))
        if inventory:
            inventory.quantity += item.quantity
            db.add(StockMovement(inventory_id=inventory.id, user_id=user_id,
                                 movement_type="ENTRADA", quantity=item.quantity,
                                 reason=f"{reason}; pedido {order.id}"))


def update_order_status(db: Session, actor: User, order_id: int, new_status: OrderStatus) -> Order:
    order = get_order(db, order_id)
    allowed = {
        OrderStatus.AGUARDANDO_PAGAMENTO.value: {OrderStatus.CANCELADO.value},
        OrderStatus.PAGO.value: {OrderStatus.EM_PREPARO.value},
        OrderStatus.EM_PREPARO.value: {OrderStatus.PRONTO.value},
        OrderStatus.PRONTO.value: {OrderStatus.ENTREGUE.value},
    }
    if new_status.value not in allowed.get(order.status, set()):
        raise HTTPException(status_code=409, detail=f"Transição inválida: {order.status} -> {new_status.value}.")
    previous = order.status
    order.status = new_status.value
    if new_status == OrderStatus.CANCELADO:
        _restore_order_stock(db, order, actor.id, "Cancelamento do pedido")
        if order.customer_id and order.points_redeemed:
            customer = db.get(User, order.customer_id)
            if customer:
                customer.points_balance += order.points_redeemed
                db.add(LoyaltyLedger(user_id=customer.id, order_id=order.id,
                                     points_delta=order.points_redeemed,
                                     reason="Estorno de pontos por cancelamento"))
    audit(db, actor.id, "STATUS_PEDIDO_ALTERADO", "pedido", str(order.id),
          {"de": previous, "para": new_status.value})
    db.commit()
    return get_order(db, order.id)
