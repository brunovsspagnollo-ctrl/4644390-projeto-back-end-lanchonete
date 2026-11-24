from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    GERENTE = "GERENTE"
    ATENDENTE = "ATENDENTE"
    COZINHA = "COZINHA"
    CLIENTE = "CLIENTE"


class OrderChannel(str, Enum):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"


class OrderStatus(str, Enum):
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    PAGO = "PAGO"
    EM_PREPARO = "EM_PREPARO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"


class PaymentStatus(str, Enum):
    APROVADO = "APROVADO"
    RECUSADO = "RECUSADO"
