"""Generate clear PNG diagrams for the editable academic report."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
FONT_PATH = Path("C:/Windows/Fonts/times.ttf")
FONT_BOLD_PATH = Path("C:/Windows/Fonts/timesbd.ttf")

INK = "#000000"
ACCENT = "#000000"
SOFT = "#FFFFFF"
MUTED = "#000000"
WHITE = "#FFFFFF"
LINE = "#000000"


def font(size: int, bold=False):
    path = FONT_BOLD_PATH if bold else FONT_PATH
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def center(draw, box, text, fnt, fill=INK, spacing=5):
    x1, y1, x2, y2 = box
    bb = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.multiline_text((x1 + (x2-x1-w)/2, y1 + (y2-y1-h)/2), text, font=fnt,
                        fill=fill, spacing=spacing, align="center")


def actor(draw, x, y, label):
    r = 25
    draw.ellipse((x-r, y-r, x+r, y+r), outline=INK, width=5)
    draw.line((x, y+r, x, y+105), fill=INK, width=5)
    draw.line((x-48, y+55, x+48, y+55), fill=INK, width=5)
    draw.line((x, y+105, x-42, y+165), fill=INK, width=5)
    draw.line((x, y+105, x+42, y+165), fill=INK, width=5)
    draw.text((x-125, y+180), label, font=font(19, True), fill=INK)


def use_cases():
    im = Image.new("RGB", (1900, 1220), WHITE)
    d = ImageDraw.Draw(im)
    d.text((80, 35), "Casos de uso — API da Rede Raízes do Nordeste", font=font(38, True), fill=INK)
    d.rounded_rectangle((330, 100, 1510, 1150), radius=20, outline=ACCENT, width=5)
    d.text((365, 115), "SISTEMA", font=font(20, True), fill=ACCENT)
    cases = [
        (500, 180, "Cadastrar e autenticar"), (920, 180, "Consultar cardápio"),
        (500, 360, "Criar/cancelar pedido\n(validar canal e estoque)"), (920, 360, "Solicitar pagamento\n(mock externo)"),
        (500, 550, "Consultar pedido"), (920, 550, "Atualizar status\n(cozinha)"),
        (500, 740, "Consultar saldo e\nresgatar pontos"), (920, 740, "Movimentar estoque"),
        (500, 930, "Gerir unidades,\nprodutos e cardápio"), (920, 930, "Criar promoções"),
    ]
    for x, y, label in cases:
        box = (x, y, x+310, y+105)
        d.ellipse(box, fill=SOFT, outline=ACCENT, width=4)
        center(d, box, label, font(22, True))
    actor(d, 130, 190, "Cliente (App/Web/Totem)")
    actor(d, 130, 540, "Atendente (Balcão)")
    actor(d, 1690, 220, "Gateway de pagamento")
    actor(d, 1690, 600, "Cozinha")
    actor(d, 1690, 900, "Gerente / Administrador")
    # Associations are routed outside the use-case ovals so labels stay clear.
    d.line((178, 245, 285, 150, 1075, 150, 1075, 180), fill=LINE, width=3)
    for yy in (230, 410, 600, 790):
        d.line((178, 245, 285, yy, 500, yy), fill=LINE, width=3)
    for yy in (410, 600):
        d.line((178, 595, 315, yy, 500, yy), fill=LINE, width=3)
    d.line((1740, 275, 1550, 275, 1550, 410, 1230, 410), fill=LINE, width=3)
    d.line((1740, 655, 1550, 655, 1550, 600, 1230, 600), fill=LINE, width=3)
    d.line((1740, 955, 1580, 955, 1580, 790, 1230, 790), fill=LINE, width=3)
    d.line((1740, 955, 1600, 955, 1600, 980, 1230, 980), fill=LINE, width=3)
    d.line((1740, 955, 1560, 955, 1560, 1110, 810, 1110, 810, 980), fill=LINE, width=3)
    im.save(OUT / "casos_de_uso.png")


def entity_box(draw, xy, title, attrs, width=450, font_size=21):
    x, y = xy
    line_h = 32
    height = 54 + line_h * len(attrs) + 18
    draw.rounded_rectangle((x, y, x+width, y+height), radius=10, fill=WHITE, outline=ACCENT, width=4)
    draw.rounded_rectangle((x, y, x+width, y+53), radius=10, fill=SOFT, outline=ACCENT, width=4)
    draw.rectangle((x, y+35, x+width, y+54), fill=SOFT)
    draw.text((x+18, y+12), title, font=font(25, True), fill=INK)
    for i, attr in enumerate(attrs):
        draw.text((x+18, y+62+i*line_h), attr, font=font(font_size), fill=INK)
    return (x, y, x+width, y+height)


def relation(draw, a, b, label, cardinality="1 : N", color=LINE):
    # Relationships are listed in a separate panel to keep the entity map readable.
    return None


def classes():
    im = Image.new("RGB", (1900, 1900), WHITE)
    global d
    d = ImageDraw.Draw(im)
    d.text((65, 30), "Diagrama de classes — domínio e relacionamentos", font=font(36, True), fill=INK)
    boxes = {}
    boxes["Usuario"] = entity_box(d, (50, 115), "Usuario", ["id: int", "nome, email", "senha_hash", "perfil", "consentimentoFidelidade", "saldoPontos"])
    boxes["Unidade"] = entity_box(d, (720, 115), "Unidade", ["id: int", "nome", "endereco", "ativa"])
    boxes["Produto"] = entity_box(d, (1390, 115), "Produto", ["id: int", "nome", "descricao", "ativo"])
    boxes["Cardapio"] = entity_box(d, (720, 480), "ItemCardapio", ["id: int", "unidadeId", "produtoId", "precoCentavos", "disponivel"])
    boxes["Estoque"] = entity_box(d, (1390, 480), "Estoque", ["id: int", "unidadeId", "produtoId", "quantidade"])
    boxes["Pedido"] = entity_box(d, (50, 865), "Pedido", ["id: int", "unidadeId", "clienteId?", "canalPedido", "status", "subtotal/desconto/total", "chaveIdempotencia"])
    boxes["Item"] = entity_box(d, (720, 865), "ItemPedido", ["id: int", "pedidoId", "produtoId", "quantidade", "precoUnitarioCentavos"])
    boxes["Pagamento"] = entity_box(d, (1390, 865), "Pagamento", ["id: int", "pedidoId", "status", "gateway", "payloadSolicitacao", "payloadResposta"])
    boxes["Fidelidade"] = entity_box(d, (50, 1260), "LancamentoFidelidade", ["id: int", "usuarioId", "pedidoId?", "variacaoPontos", "motivo"])
    boxes["Movimento"] = entity_box(d, (720, 1260), "MovimentoEstoque", ["id: int", "estoqueId", "usuarioId", "tipo", "quantidade", "motivo"])
    boxes["Promocao"] = entity_box(d, (1390, 1260), "Promocao", ["id: int", "codigo", "percentual", "inicio/fim", "ativa"])
    relation(d, boxes["Unidade"], boxes["Cardapio"], "define")
    relation(d, boxes["Produto"], boxes["Cardapio"], "ofertado")
    relation(d, boxes["Unidade"], boxes["Estoque"], "possui")
    relation(d, boxes["Produto"], boxes["Estoque"], "saldo")
    relation(d, boxes["Usuario"], boxes["Pedido"], "realiza", "0..1 : N")
    relation(d, boxes["Unidade"], boxes["Pedido"], "recebe")
    relation(d, boxes["Pedido"], boxes["Item"], "composicao")
    relation(d, boxes["Produto"], boxes["Item"], "referencia")
    relation(d, boxes["Pedido"], boxes["Pagamento"], "liquidacao", "1 : 0..1")
    relation(d, boxes["Usuario"], boxes["Fidelidade"], "gera")
    relation(d, boxes["Estoque"], boxes["Movimento"], "registra")
    relation(d, boxes["Usuario"], boxes["Movimento"], "autoriza")
    d.rounded_rectangle((50, 1570, 1850, 1860), radius=16, fill=SOFT, outline=ACCENT, width=3)
    d.text((80, 1590), "Relacionamentos e cardinalidades", font=font(25, True), fill=INK)
    rels = [
        "Unidade 1:N Pedidos  |  Cliente 0..1:N Pedidos",
        "Pedido 1:N ItensPedido  |  Produto 1:N ItensPedido",
        "Pedido 1:0..1 Pagamento  |  Unidade 1:N ItemCardapio",
        "Produto 1:N ItemCardapio  |  Unidade/Produto 1:N Estoque",
        "Estoque 1:N Movimentos  |  Usuario 1:N Fidelidade/Auditoria",
    ]
    for i, line in enumerate(rels):
        d.text((85, 1635 + i*42), line, font=font(21), fill=INK)
    im.save(OUT / "diagrama_classes.png")


def erd():
    im = Image.new("RGB", (1900, 1900), WHITE)
    d = ImageDraw.Draw(im)
    d.text((65, 30), "DER — entidades, chaves e cardinalidades", font=font(36, True), fill=INK)
    boxes = {}
    boxes["USERS"] = entity_box(d, (50, 110), "USERS", ["PK id", "UK email", "password_hash", "role", "loyalty_consent", "points_balance"])
    boxes["UNITS"] = entity_box(d, (720, 110), "UNITS", ["PK id", "UK name", "address", "active"])
    boxes["PRODUCTS"] = entity_box(d, (1390, 110), "PRODUCTS", ["PK id", "UK name", "description", "active"])
    boxes["CATALOG"] = entity_box(d, (720, 465), "UNIT_CATALOG", ["PK id", "FK unit_id", "FK product_id", "price_cents", "available", "UK(unit_id, product_id)"])
    boxes["INVENTORY"] = entity_box(d, (1390, 465), "INVENTORY", ["PK id", "FK unit_id", "FK product_id", "quantity", "UK(unit_id, product_id)"])
    boxes["ORDERS"] = entity_box(d, (50, 850), "ORDERS", ["PK id", "FK unit_id", "FK customer_id?", "channel", "status", "total_cents", "UK idempotency_key"])
    boxes["ITEMS"] = entity_box(d, (720, 850), "ORDER_ITEMS", ["PK id", "FK order_id", "FK product_id", "quantity", "unit_price_cents"])
    boxes["PAYMENTS"] = entity_box(d, (1390, 850), "PAYMENTS", ["PK id", "FK/UK order_id", "status", "provider", "request_payload", "response_payload"])
    boxes["LOYALTY"] = entity_box(d, (50, 1240), "LOYALTY_LEDGER", ["PK id", "FK user_id", "FK order_id?", "points_delta", "reason"])
    boxes["STOCK"] = entity_box(d, (720, 1240), "STOCK_MOVEMENTS", ["PK id", "FK inventory_id", "FK user_id", "movement_type", "quantity", "reason"])
    boxes["PROMO"] = entity_box(d, (1390, 1240), "PROMOTIONS", ["PK id", "UK code", "percent_off", "starts_at/ends_at", "active"])
    relation(d, boxes["UNITS"], boxes["CATALOG"], "1:N")
    relation(d, boxes["PRODUCTS"], boxes["CATALOG"], "1:N")
    relation(d, boxes["UNITS"], boxes["INVENTORY"], "1:N")
    relation(d, boxes["PRODUCTS"], boxes["INVENTORY"], "1:N")
    relation(d, boxes["USERS"], boxes["ORDERS"], "0..1:N")
    relation(d, boxes["UNITS"], boxes["ORDERS"], "1:N")
    relation(d, boxes["ORDERS"], boxes["ITEMS"], "1:N")
    relation(d, boxes["PRODUCTS"], boxes["ITEMS"], "1:N")
    relation(d, boxes["ORDERS"], boxes["PAYMENTS"], "1:0..1")
    relation(d, boxes["USERS"], boxes["LOYALTY"], "1:N")
    relation(d, boxes["INVENTORY"], boxes["STOCK"], "1:N")
    d.rounded_rectangle((50, 1570, 1850, 1860), radius=16, fill=SOFT, outline=ACCENT, width=3)
    d.text((80, 1590), "Relacionamentos e cardinalidades", font=font(25, True), fill=INK)
    rels = [
        "UNITS 1:N ORDERS  |  USERS 0..1:N ORDERS",
        "ORDERS 1:N ORDER_ITEMS  |  PRODUCTS 1:N ORDER_ITEMS",
        "ORDERS 1:0..1 PAYMENTS  |  UNITS 1:N UNIT_CATALOG",
        "PRODUCTS 1:N UNIT_CATALOG  |  UNITS/PRODUCTS 1:N INVENTORY",
        "INVENTORY 1:N STOCK_MOVEMENTS  |  USERS 1:N LOYALTY_LEDGER",
    ]
    for i, line in enumerate(rels):
        d.text((85, 1635 + i*42), line, font=font(21), fill=INK)
    im.save(OUT / "der.png")


def sequence():
    im = Image.new("RGB", (1900, 1050), WHITE)
    d = ImageDraw.Draw(im)
    d.text((65, 35), "Sequência — pedido e pagamento mock", font=font(36, True), fill=INK)
    names = ["Cliente /\nAtendente", "API", "SQLite", "Gateway\nmock", "Cozinha"]
    xs = [190, 560, 920, 1280, 1660]
    top, bottom = 130, 990
    for x, name in zip(xs, names):
        box = (x-120, top, x+120, top+95)
        d.rounded_rectangle(box, radius=12, fill=SOFT, outline=ACCENT, width=4)
        center(d, box, name, font(22, True))
        d.line((x, top+95, x, bottom), fill=LINE, width=3)

    def msg(a, b, y, label, dashed=False):
        style = (8, 6) if dashed else None
        d.line((xs[a], y, xs[b], y), fill=ACCENT if not dashed else MUTED, width=3)
        if a < b:
            d.polygon([(xs[b],y),(xs[b]-14,y-8),(xs[b]-14,y+8)], fill=ACCENT if not dashed else MUTED)
        else:
            d.polygon([(xs[b],y),(xs[b]+14,y-8),(xs[b]+14,y+8)], fill=ACCENT if not dashed else MUTED)
        bb=d.textbbox((0,0),label,font=font(19,True)); w=bb[2]-bb[0]
        d.rectangle(((xs[a]+xs[b]-w)//2-8,y-31,(xs[a]+xs[b]+w)//2+8,y-4),fill=WHITE)
        d.text(((xs[a]+xs[b]-w)//2,y-29),label,font=font(19,True),fill=INK)

    msg(0,1,285,"POST /orders + canalPedido + Idempotency-Key")
    msg(1,2,385,"Validar unidade, cardápio e estoque")
    msg(2,1,455,"Preço e saldo válidos",True)
    msg(1,2,535,"Reservar estoque e persistir pedido")
    msg(1,0,605,"201 AGUARDANDO_PAGAMENTO",True)
    msg(0,1,695,"POST /payments/{id}/mock")
    msg(1,3,785,"Solicitar pagamento de demonstração")
    msg(3,1,855,"Payload APROVADO ou RECUSADO",True)
    msg(1,2,925,"Persistir pagamento, status, pontos e auditoria")
    d.text((75, 1000), "Aprovado: PAGO → EM_PREPARO → PRONTO → ENTREGUE. Recusado: CANCELADO e estoque devolvido.", font=font(21, True), fill=INK)
    im.save(OUT / "sequencia_pedido_pagamento.png")


if __name__ == "__main__":
    use_cases()
    classes()
    erd()
    sequence()
    print(f"Diagramas salvos em {OUT}")
