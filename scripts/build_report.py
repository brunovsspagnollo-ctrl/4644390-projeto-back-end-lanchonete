"""Build the editable academic report after the API source is finalized."""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
OUT = DOCS / "Trabalho Final Bruno Spagnollo.docx"


def set_run(run, size=12, bold=False, italic=False, color="000000"):
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run.font.size = Pt(12)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)
    run.font.underline = False


def shade(cell, fill="FFFFFF"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(cell, top=80, start=90, bottom=80, end=90):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def add_page_field(paragraph):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText"); instruction.set(qn("xml:space"), "preserve"); instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar"); separate.set(qn("w:fldCharType"), "separate")
    value = OxmlElement("w:t"); value.text = "1"
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for node in (begin, instruction, separate, value, end):
        run._r.append(node)
    set_run(run, 10)


def add_toc_field(paragraph):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText"); instruction.set(qn("xml:space"), "preserve")
    instruction.text = ' TOC \\o "1-3" \\h \\z \\u '
    separate = OxmlElement("w:fldChar"); separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t"); placeholder.text = "Atualize este sumário no Word (Ctrl+A e F9)."
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for node in (begin, instruction, separate, placeholder, end):
        run._r.append(node)
    set_run(run, 11)


def body(doc, text, first=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, after=0):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(after)
    if first:
        p.paragraph_format.first_line_indent = Cm(1.25)
    r = p.add_run(text)
    set_run(r, size)
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(14 if level == 1 else 9)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    set_run(r, 12, True)
    return p


def small_label(doc, label, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.4)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(label + " ")
    set_run(r, 10.5, True)
    r = p.add_run(text)
    set_run(r, 10.5)
    return p


def add_table(doc, headers, rows, widths=None, font_size=9):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = False
    header = table.rows[0]
    tr_pr = header._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader"); repeat.set(qn("w:val"), "true"); tr_pr.append(repeat)
    for i, text in enumerate(headers):
        cell = header.cells[i]
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shade(cell, "FFFFFF")
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(text); set_run(r, font_size, True)
        if widths:
            cell.width = Cm(widths[i])
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            set_cell_margins(cells[i])
            p = cells[i].paragraphs[0]
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(value)); set_run(r, font_size)
            if widths:
                cells[i].width = Cm(widths[i])
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def figure(doc, name, caption, width=6.25):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(ASSETS / name), width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.first_line_indent = Cm(0)
    cap.paragraph_format.line_spacing = 1.0
    r = cap.add_run(caption); set_run(r, 10)


def code_block(doc, text):
    for line in text.strip("\n").splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(line if line else " ")
        r.font.name = "Times New Roman"
        r._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Times New Roman")
        r._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Times New Roman")
        r.font.size = Pt(12)


def endpoint(doc, method, route, purpose, auth, params="Sem parâmetros", request="Sem corpo", response="200", errors="401, 403, 404, 422 conforme a regra"):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run(f"{method} {route}"); set_run(r, 12, True, color="000000")
    small_label(doc, "Finalidade:", purpose)
    small_label(doc, "Autenticação/perfil:", auth)
    small_label(doc, "Parâmetros:", params)
    small_label(doc, "Request:", request)
    small_label(doc, "Response/códigos:", f"{response}; erros: {errors}.")


doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21); sec.page_height = Cm(29.7)
sec.top_margin = Cm(3); sec.left_margin = Cm(3); sec.bottom_margin = Cm(2); sec.right_margin = Cm(2)
sec.footer_distance = Cm(1.25)
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"; normal.font.size = Pt(12)
normal.font.color.rgb = RGBColor(0, 0, 0); normal.font.underline = False
normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
for style in doc.styles:
    if style.type in (1, 2):
        style.font.name = "Times New Roman"
        style.font.size = Pt(12)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.underline = False
        if style.name.startswith("Heading "):
            style.font.bold = True
    p_pr = style._element.find(qn("w:pPr"))
    if p_pr is not None:
        border = p_pr.find(qn("w:pBdr"))
        if border is not None:
            p_pr.remove(border)
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
sec.different_first_page_header_footer = True

# Capa com os dados acadêmicos fornecidos pelo aluno.
for text in (
    "CENTRO UNIVERSITÁRIO INTERNACIONAL",
    "CST ANÁLISE E DESENVOLVIMENTO DE SISTEMAS",
    "BRUNO VINICIUS SCARIOT SPAGNOLLO",
    "RU: 4644390",
):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.space_after = Pt(4)
    set_run(p.add_run(text), 12, text != "RU: ____________________")
for _ in range(5): doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Cm(0)
set_run(p.add_run("SISTEMA DE PEDIDOS MULTICANAL PARA A REDE RAÍZES DO NORDESTE"), 12, True)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent = Cm(0)
set_run(p.add_run("API Back-End com Python, FastAPI e SQLite"), 12)
for _ in range(8): doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent = Cm(0)
set_run(p.add_run("PATO BRANCO - PR\n2026"), 12)
doc.add_page_break()

# Folha de rosto.
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent = Cm(0)
set_run(p.add_run("BRUNO VINICIUS SCARIOT SPAGNOLLO\nRU: 4644390"), 12, True)
for _ in range(5): doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent = Cm(0)
p.style = doc.styles["Title"]
set_run(p.add_run("SISTEMA DE PEDIDOS MULTICANAL PARA A REDE RAÍZES DO NORDESTE"), 12, True)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent = Cm(0)
set_run(p.add_run("API Back-End com Python, FastAPI e SQLite"), 12)
for _ in range(4): doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p.paragraph_format.left_indent = Cm(8); p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.line_spacing = 1.0
set_run(p.add_run("Trabalho apresentado ao curso de CST Análise e Desenvolvimento de Sistemas do Centro Universitário Internacional, como requisito parcial da atividade de Projeto Multidisciplinar - Trilha Back-End."), 12)
for _ in range(4): doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent = Cm(0)
set_run(p.add_run("PATO BRANCO - PR\n2026"), 12)
doc.add_page_break()

heading(doc, "RESUMO", 1)
body(doc, "Este trabalho apresenta a modelagem e a implementação de uma API Back-End para a Rede Raízes do Nordeste, cenário de uma rede de lanchonetes com unidades e canais de atendimento integrados. A solução foi construída em Python com FastAPI, SQLAlchemy e SQLite e organiza o domínio em usuários, unidades, produtos, cardápio por unidade, estoque, pedidos, itens, pagamentos simulados, promoções e fidelidade. O fluxo principal registra um pedido com canal de origem obrigatório, valida preços e saldo da unidade, reserva o estoque e solicita um pagamento a um gateway mock. Uma aprovação atualiza o pedido para pago e pode creditar pontos quando existe consentimento; uma recusa cancela o pedido e devolve o estoque reservado. A API aplica autenticação Bearer com JWT, perfis de acesso, hash de senha, erros JSON padronizados e trilha de auditoria. A modelagem é apresentada em diagramas de casos de uso, classes, entidade-relacionamento e sequência. O projeto inclui migração inicial, instruções de execução e coleção Postman com vinte e uma chamadas e assertions para cenários positivos e negativos. A proposta prioriza um MVP local, descreve limites do SQLite e identifica medidas para uma evolução segura a um ambiente de produção.")
small_label(doc, "Palavras-chave:", "API REST. FastAPI. SQLite. Pedidos multicanal. Pagamento simulado.")
doc.add_page_break()
heading(doc, "ABSTRACT", 1)
body(doc, "This report presents the modeling and implementation of a back-end API for a multi-unit snack restaurant chain. The solution uses Python, FastAPI, SQLAlchemy, and SQLite and covers users, stores, products, store-specific menus, inventory, orders, order items, mocked payments, promotions, and loyalty points. The main flow requires an order channel, validates the store menu and stock, reserves inventory, and submits a payment request to a mock gateway. An approved payment changes the order state to paid and may award points when the customer has consented; a declined payment cancels the order and restores reserved stock. The API applies Bearer authentication with JWT, role-based access, salted password hashing, standardized JSON errors, and audit records. The report includes use-case, class, entity-relationship, and sequence diagrams, plus a Postman collection with twenty-one calls and assertions for positive and negative scenarios.")
small_label(doc, "Keywords:", "REST API. FastAPI. SQLite. Multichannel orders. Mock payment.")
doc.add_page_break()
heading(doc, "SUMÁRIO", 1)
add_toc_field(doc.add_paragraph())
main_section = doc.add_section(WD_SECTION.NEW_PAGE)
main_section.page_width = Cm(21); main_section.page_height = Cm(29.7)
main_section.top_margin = Cm(3); main_section.left_margin = Cm(3); main_section.bottom_margin = Cm(2); main_section.right_margin = Cm(2)
main_section.footer.is_linked_to_previous = False
main_section.footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
add_page_field(main_section.footer.paragraphs[0])
pg = OxmlElement("w:pgNumType"); pg.set(qn("w:start"), "6")
main_section._sectPr.append(pg)

heading(doc, "1 INTRODUÇÃO", 1)
body(doc, "A Rede Raízes do Nordeste precisa consolidar informações de unidades, cardápio, disponibilidade, pedidos e atendimento mesmo quando a compra começa em canais diferentes. Aplicativos, totens, balcão, retirada e web devem registrar a origem do pedido e compartilhar regras operacionais, evitando divergências de preço e venda de itens sem saldo.")
body(doc, "O objetivo deste projeto é demonstrar uma solução de Back-End para esse cenário, expondo uma API REST em Python com FastAPI e persistindo os dados em SQLite. O sistema registra pedidos de forma rastreável, valida estoque da unidade, simula a integração de pagamento e oferece regras básicas de fidelidade e promoção. A aplicação e seus contratos são apresentados em relação direta com o roteiro da atividade prática.")
heading(doc, "1.1 Objetivos", 2)
body(doc, "O objetivo geral é modelar e implementar um MVP de pedidos multicanal com persistência relacional. Como objetivos específicos, busca-se definir requisitos de domínio; separar interface, aplicação, domínio e infraestrutura; documentar contratos REST; aplicar autenticação, autorização e controles básicos de privacidade; e preparar uma coleção reproduzível para validação manual no Postman.")

heading(doc, "2 CONTEXTO E REQUISITOS", 1)
body(doc, "A proposta considera uma empresa com matriz e unidades operacionais. O catálogo e o estoque são associados à unidade; os pedidos mantêm preço histórico, estado, horário, canal e identificador de idempotência. O cliente é opcional para compras realizadas por atendente e obrigatório de forma implícita para os fluxos autenticados como cliente. A integração de pagamento é simulada e não recebe dados bancários reais.")
heading(doc, "2.1 Requisitos funcionais", 2)
rf = [
    ("RF01", "Cadastrar clientes com e-mail e senha, armazenando somente hash com salt; autenticar e emitir token Bearer."),
    ("RF02", "Aplicar perfis ADMIN, GERENTE, ATENDENTE, COZINHA e CLIENTE em rotas protegidas."),
    ("RF03", "Cadastrar unidades e produtos e associar produtos a um cardápio com preço e disponibilidade por unidade."),
    ("RF04", "Consultar cardápio e saldo de estoque por unidade, com paginação nas listagens."),
    ("RF05", "Registrar entrada e saída de estoque e impedir saída ou pedido acima do saldo disponível."),
    ("RF06", "Criar pedido com um ou mais itens, total calculado no servidor e snapshot do preço unitário."),
    ("RF07", "Exigir canalPedido em APP, TOTEM, BALCAO, PICKUP ou WEB e permitir filtrar pedidos por esse campo."),
    ("RF08", "Acompanhar o fluxo AGUARDANDO_PAGAMENTO, PAGO, EM_PREPARO, PRONTO, ENTREGUE e CANCELADO."),
    ("RF09", "Enviar solicitação a um gateway de pagamento mock, registrar request/response e tratar aprovação e recusa."),
    ("RF10", "Cadastrar campanhas por código promocional com percentual e período de validade."),
    ("RF11", "Registrar consentimento de fidelidade, creditar pontos por compra aprovada, permitir resgate e revogação."),
    ("RF12", "Registrar auditoria de pedidos, mudanças de estado, pagamentos, estoque, usuários internos e privacidade."),
    ("RF13", "Permitir solicitação de anonimização da conta, desvinculando pedidos históricos do titular."),
]
add_table(doc, ["ID", "Requisito funcional"], rf, [2.0, 14.0], 9.5)
heading(doc, "2.2 Requisitos não funcionais", 2)
rnf = [
    ("RNF01 - Segurança", "JWT assinado, validade configurável, perfis por rota, senha PBKDF2-HMAC-SHA256 com salt aleatório e segredo fora do código em .env."),
    ("RNF02 - Privacidade", "Minimização de dados, consentimento específico para fidelidade, registro de data/hora, revogação e anonimização solicitável."),
    ("RNF03 - Integridade", "Chaves estrangeiras, restrições únicas, transação de pedido/estoque e chave Idempotency-Key."),
    ("RNF04 - Observabilidade", "Formato de erro comum, requestId e registros de auditoria para ações sensíveis."),
    ("RNF05 - Desempenho e disponibilidade", "MVP local com SQLite e paginação limitada; operação distribuída e alta concorrência exigem PostgreSQL, monitoramento e escalabilidade."),
    ("RNF06 - Integração resiliente", "O gateway mock demonstra retorno aprovado/recusado; timeout, repetição segura e circuit breaker ficam definidos como evolução do adaptador real."),
    ("RNF07 - Documentação", "OpenAPI/Swagger gerado pelo FastAPI, README de configuração e coleção Postman com cenários e assertions."),
]
add_table(doc, ["ID", "Requisito não funcional"], rnf, [3.3, 12.7], 9.5)

heading(doc, "3 ARQUITETURA DA SOLUÇÃO", 1)
body(doc, "A aplicação adota uma separação por responsabilidade equivalente às camadas Domain, Application, Infrastructure e API. O domínio concentra enums e estados; os casos de uso ficam em services.py; models.py e database.py encapsulam persistência; main.py expõe controllers e configura a aplicação; schemas.py define contratos e security.py autenticação e autorização.")
layers = [
    ("Domain", "app/domain.py", "Perfis, canais, estados de pedido e resultados de pagamento."),
    ("Application", "app/services.py", "Orquestra criação do pedido, reserva de estoque, pagamento, pontuação e transições."),
    ("Infrastructure", "app/database.py, app/models.py, alembic/", "Engine e sessões SQLAlchemy, entidades relacionais e migração do schema."),
    ("API", "app/main.py, app/schemas.py, app/security.py", "Rotas REST, validação Pydantic, erros, JWT, Bearer e permissões."),
]
add_table(doc, ["Camada", "Arquivos", "Responsabilidade"], layers, [2.4, 5.8, 7.8], 9)
body(doc, "A documentação interativa do contrato é gerada pelo FastAPI em /docs. FastAPI também gera o esquema OpenAPI, que descreve caminhos, parâmetros e modelos da API [1].");
figure(doc, "sequencia_pedido_pagamento.png", "Figura 1 - Sequência do fluxo crítico de pedido e pagamento mock. Fonte: elaborado pelo autor.")

heading(doc, "4 MODELAGEM DO DOMÍNIO", 1)
heading(doc, "4.1 Diagrama de casos de uso", 2)
body(doc, "Os atores do sistema são Cliente (App/Web/Totem), Atendente (Balcão), Cozinha, Gerente/Administrador e Gateway de Pagamento. O cliente consulta cardápio, registra e acompanha pedidos e participa da fidelidade; o atendente apoia a venda; a cozinha avança o preparo; o gerente administra unidades, catálogo, campanhas e estoque; o gateway mock responde à solicitação de pagamento.")
figure(doc, "casos_de_uso.png", "Figura 2 - Atores e casos de uso da API. Fonte: elaborado pelo autor.")
heading(doc, "4.2 Descrição da feature crítica", 2)
small_label(doc, "UC01 - Nome:", "Realizar pedido e solicitar pagamento mock.")
small_label(doc, "Atores principais:", "Cliente ou Atendente; sistema externo participante: Gateway de Pagamento mock.")
small_label(doc, "Pré-condições:", "API disponível; unidade ativa; produtos no cardápio da unidade; saldo de estoque suficiente; usuário autenticado quando o perfil exigir; chave Idempotency-Key fornecida. Para resgatar pontos, o usuário deve ser CLIENTE, ter consentido com fidelidade e possuir saldo.")
small_label(doc, "Fluxo principal:", "(1) Cliente consulta /catalog/{unit_id}. (2) Envia POST /orders com canalPedido e itens. (3) API valida unidade, cardápio, preço, estoque, cupom e fidelidade. (4) API calcula o total em centavos, reserva saldo e persiste o pedido. (5) API responde 201 com status AGUARDANDO_PAGAMENTO. (6) Cliente solicita POST /payments/{id}/mock. (7) Gateway retorna status e payload; a API grava a transação e atualiza o pedido. (8) Em aprovação, cozinha percorre EM_PREPARO, PRONTO e ENTREGUE.")
small_label(doc, "Pós-condições:", "O pedido, itens e pagamento ficam persistidos; canalPedido permite rastrear origem; a reserva altera o saldo; pontos são creditados somente após aprovação e consentimento.")
small_label(doc, "Exceções:", "Unidade ou item ausente: 404. Estoque insuficiente, cupom inválido, falta de saldo ou pedido já pago: 409. Corpo inválido ou total zero: 422. Token ausente: 401. Perfil sem acesso: 403. Pagamento recusado: resposta registrada como RECUSADO, pedido CANCELADO, estoque devolvido e pontos resgatados estornados.")
small_label(doc, "Idempotência:", "Idempotency-Key é única no pedido. Uma repetição com a mesma chave e o mesmo cliente retorna o pedido já persistido; uma chave reutilizada por outro cliente gera conflito. Pagamento é único por pedido e uma segunda solicitação é rejeitada com 409.")
small_label(doc, "Limite do cancelamento:", "O cancelamento de pedido pelo MVP ocorre antes da confirmação do pagamento. O reembolso mock para pedido pago fica como evolução, pois não há cobrança financeira real.")

heading(doc, "4.3 Diagrama de classes", 2)
body(doc, "As classes representam contas de usuários e perfis, unidades, produtos, associação do cardápio por unidade, estoque, pedidos, itens, pagamentos, promoções, lançamentos de fidelidade e movimentos de estoque. O pedido é composto por um ou mais itens; cada item guarda preço unitário praticado para preservar o histórico do preço.")
figure(doc, "diagrama_classes.png", "Figura 3 - Classes de domínio e cardinalidades principais. Fonte: elaborado pelo autor.")
heading(doc, "4.4 Diagrama entidade-relacionamento", 2)
body(doc, "O DER corresponde às tabelas SQLAlchemy e destaca PK, FK, chaves únicas e cardinalidades. O estoque é próprio de cada unidade, implementado por Inventory com restrição única para unit_id + product_id. O cardápio também usa associação unitária UnitCatalog. OrderItem liga pedido e produto e mantém unit_price_cents como snapshot. Payment possui relação 1:0..1 com Order por order_id único. A promoção é registrada no pedido pelo código aplicado; o código não é uma chave estrangeira porque a campanha pode ser desativada sem alterar o histórico do pedido.")
figure(doc, "der.png", "Figura 4 - DER compatível com o schema do SQLite. Fonte: elaborado pelo autor.")

heading(doc, "5 PERSISTÊNCIA E MODELO DE DADOS", 1)
body(doc, "SQLite foi escolhido por ser relacional, embutido e armazenado em arquivo local, sem servidor dedicado. O formato facilita a execução e correção de um MVP individual; a documentação do próprio SQLite o posiciona para armazenamento local e explica quando um banco cliente-servidor pode ser preferível [5]. SQLAlchemy mapeia entidades e relacionamentos e compõe as operações relacionais [4]. Alembic mantém a revisão inicial do schema [6].")
data = [
    ("users", "Conta, hash, role, consentimento, saldo de pontos; e-mail único."),
    ("units", "Unidade/filial e endereço."),
    ("products", "Catálogo geral de produtos."),
    ("unit_catalog", "Produto por unidade, preço em centavos e disponibilidade; par unit/product único."),
    ("inventory", "Saldo por unidade e produto; par único."),
    ("stock_movements", "Entradas/saídas, quantidade, motivo e usuário responsável."),
    ("orders", "Unidade, cliente opcional, canal, status, valores, pontos e chave idempotente."),
    ("order_items", "Itens do pedido, quantidade e preço histórico em centavos."),
    ("payments", "Status e payloads JSON de solicitação e retorno do gateway mock."),
    ("promotions", "Código, percentual, validade e disponibilidade."),
    ("loyalty_ledger", "Créditos e débitos de pontos ligados ao usuário e, se aplicável, ao pedido."),
    ("audit_logs", "Ação, ator, recurso, identificador, detalhes sem senha ou cartão."),
]
add_table(doc, ["Tabela", "Conteúdo e restrições"], data, [3.5, 12.5], 9)
body(doc, "Valores monetários são inteiros em centavos, evitando aritmética binária de ponto flutuante. O arquivo de banco padrão é lanchonete.db; a configuração pode ser alterada por DATABASE_URL. A aplicação ativa chaves estrangeiras no SQLite.")

heading(doc, "6 CONTRATO DA API E ENDPOINTS", 1)
body(doc, "Todos os contratos são JSON. As rotas protegidas usam Authorization: Bearer <access_token>. O token é obtido em POST /auth/login. Listagens pagináveis usam page (inicia em 1) e limit (máximo 100). O canal do pedido é obrigatório na propriedade canalPedido e usa os valores APP, TOTEM, BALCAO, PICKUP e WEB. O filtro é GET /orders?canalPedido=TOTEM.")
heading(doc, "6.1 Autenticação e usuários", 2)
endpoint(doc, "POST", "/auth/register", "Criar uma conta de cliente; o perfil público é sempre CLIENTE.", "Público", "Body: nome, e-mail, senha (mínimo 10 caracteres), loyalty_consent opcional.", '{"name":"Ana Silva","email":"ana@example.com","password":"SenhaSegura123!","loyalty_consent":true}', "201 com id, nome, e-mail, role e consentimento", "409 e-mail já usado; 422 entrada inválida")
endpoint(doc, "POST", "/auth/login", "Validar credenciais e retornar JWT assinado com validade configurada.", "Público", "Body: email e password.", '{"email":"admin@example.com","password":"<senha-do-env>"}', "200 access_token, token_type, expires_in e user", "401 credenciais inválidas; 422 entrada inválida")
endpoint(doc, "GET", "/auth/me", "Consultar perfil da conta autenticada.", "JWT; todos os perfis ativos", "Authorization Bearer.", "Sem corpo", "200 com perfil público", "401 token inválido/ausente")
endpoint(doc, "POST", "/users/staff", "Criar conta interna com role definida.", "JWT; ADMIN", "Body: name, email, password e role.", '{"name":"Cozinha Centro","email":"cozinha@example.com","password":"SenhaInterna123!","role":"COZINHA"}', "201 usuário criado; auditoria gerada", "401, 403, 409 e 422")
heading(doc, "6.2 Unidades, produtos, cardápio e estoque", 2)
endpoint(doc, "GET", "/units", "Listar unidades com paginação.", "JWT; ADMIN, GERENTE, ATENDENTE ou COZINHA", "Query page, limit.", "Sem corpo", "200 lista de unidades", "401, 403 e 422")
endpoint(doc, "POST", "/units", "Cadastrar uma unidade.", "JWT; ADMIN ou GERENTE", "Body: name e address.", '{"name":"Unidade Centro","address":"Av. Principal, 100"}', "201 unidade criada", "401, 403, 409 e 422")
endpoint(doc, "GET", "/products", "Listar produtos com paginação.", "JWT; ADMIN, GERENTE ou ATENDENTE", "Query page, limit.", "Sem corpo", "200 lista de produtos", "401, 403 e 422")
endpoint(doc, "POST", "/products", "Cadastrar um produto geral.", "JWT; ADMIN ou GERENTE", "Body: name e description opcional.", '{"name":"X-Burger","description":"Hamburguer, queijo e salada"}', "201 produto criado", "401, 403, 409 e 422")
endpoint(doc, "POST", "/units/{unit_id}/catalog", "Associar produto ao cardápio e definir preço/disponibilidade.", "JWT; ADMIN ou GERENTE", "Path unit_id; body product_id, price_cents e available.", '{"product_id":1,"price_cents":2290,"available":true}', "201 item associado", "401, 403, 404, 409 e 422")
endpoint(doc, "GET", "/catalog/{unit_id}", "Consultar cardápio e disponibilidade por filial.", "Público", "Path unit_id; query page, limit.", "Sem corpo", "200 lista com product_id, nome, preço, disponibilidade e stock", "404 unidade inexistente; 422 query inválida")
endpoint(doc, "GET", "/stock", "Consultar saldo de estoque da unidade.", "JWT; ADMIN, GERENTE, ATENDENTE ou COZINHA", "Query obrigatória unit_id; page, limit.", "Sem corpo", "200 lista de saldos", "401, 403 e 422")
endpoint(doc, "POST", "/stock/movements", "Registrar entrada ou saída manual de estoque.", "JWT; ADMIN ou GERENTE", "Body unit_id, product_id, movement_type, quantity e reason.", '{"unit_id":1,"product_id":1,"movement_type":"ENTRADA","quantity":10,"reason":"Reposicao"}', "201 com movimento e saldo atualizado", "401, 403, 404, 409 e 422")
heading(doc, "6.3 Promoções, pedidos, pagamento e fidelidade", 2)
endpoint(doc, "POST", "/promotions", "Cadastrar campanha de desconto percentual por período.", "JWT; ADMIN ou GERENTE", "Body code, percent_off, starts_at e ends_at.", '{"code":"LANCHE10","percent_off":10,"starts_at":"2026-11-01T00:00:00","ends_at":"2026-12-31T23:59:59"}', "201 campanha cadastrada", "401, 403, 409 e 422")
endpoint(doc, "POST", "/orders", "Criar pedido, calcular valores, reservar estoque e iniciar pagamento.", "JWT; ADMIN, GERENTE, ATENDENTE ou CLIENTE", "Header Idempotency-Key; body unit_id, canalPedido obrigatório, items, promotion_code e redeem_points.", '{"unit_id":1,"canalPedido":"APP","items":[{"product_id":1,"quantity":2}]}', "201 pedido AGUARDANDO_PAGAMENTO com total_cents e itens", "401, 403, 404, 409 e 422")
endpoint(doc, "GET", "/orders", "Consultar pedidos com filtros e paginação.", "JWT; todos os perfis; CLIENTE vê somente os próprios", "Query unit_id, canalPedido, status, page, limit.", "Sem corpo", "200 lista de pedidos", "401, 403 e 422")
endpoint(doc, "GET", "/orders/{order_id}", "Consultar pedido individual; a leitura é auditada.", "JWT; equipe; CLIENTE somente o próprio", "Path order_id.", "Sem corpo", "200 pedido com itens e canalPedido", "401, 403 e 404")
endpoint(doc, "POST", "/orders/{order_id}/cancel", "Cancelar pedido antes do pagamento e liberar estoque/pontos reservados.", "JWT; CLIENTE dono do pedido, ADMIN, GERENTE ou ATENDENTE", "Path order_id.", "Sem corpo", "200 pedido CANCELADO", "401, 403, 404 e 409")
endpoint(doc, "PATCH", "/orders/{order_id}/status", "Avançar o preparo e a entrega na ordem permitida.", "JWT; ADMIN, GERENTE ou COZINHA", "Path order_id; body status.", '{"status":"EM_PREPARO"}', "200 pedido atualizado", "401, 403, 404, 409 e 422")
endpoint(doc, "POST", "/payments/{order_id}/mock", "Simular a solicitação e o retorno do gateway; não movimenta dinheiro real.", "JWT; ADMIN, GERENTE, ATENDENTE ou CLIENTE dono", "Path order_id; body outcome e payment_method.", '{"outcome":"APROVADO","payment_method":"PIX_MOCK"}', "201 pagamento com status, provider e payloads; pedido vai a PAGO ou CANCELADO", "401, 403, 404, 409 e 422")
endpoint(doc, "GET", "/loyalty/me", "Consultar participação e saldo de pontos do cliente.", "JWT; CLIENTE", "Sem parâmetros.", "Sem corpo", "200 enrolled e points ou aviso de não adesão", "401 e 403")
endpoint(doc, "GET", "/loyalty/history", "Consultar o histórico paginado de créditos e resgates.", "JWT; CLIENTE com consentimento", "Query page, limit.", "Sem corpo", "200 lista do ledger", "401, 403 e 422")
endpoint(doc, "PATCH", "/loyalty/consent", "Registrar ou revogar o aceite para fidelidade.", "JWT; CLIENTE", "Body consent boolean.", '{"consent":false}', "200 consentimento e saldo; revogar encerra saldo", "401, 403 e 422")
heading(doc, "6.4 Privacidade, auditoria e sistema", 2)
endpoint(doc, "DELETE", "/privacy/me", "Anonymizar dados da conta e retirar a associação a pedidos anteriores.", "JWT; CLIENTE", "Sem parâmetros.", "Sem corpo", "204 sem conteúdo", "401 e 403")
endpoint(doc, "GET", "/audit", "Consultar trilha de auditoria paginada.", "JWT; ADMIN", "Query page, limit.", "Sem corpo", "200 lista de eventos", "401, 403 e 422")
endpoint(doc, "GET", "/health", "Confirmar disponibilidade da aplicação.", "Público", "Sem parâmetros.", "Sem corpo", '200 {"status":"ok","service":"lanchonete-api"}', "500 falha interna padronizada")

heading(doc, "6.5 Exemplo do pedido e resposta", 2)
body(doc, "O canal é propriedade obrigatória do contrato. A chave de idempotência é um cabeçalho para que uma repetição de rede não gere um segundo pedido.", first=False)
code_block(doc, '''POST /orders\nAuthorization: Bearer <access_token>\nIdempotency-Key: pedido-cliente-01\nContent-Type: application/json\n\n{\n  "unit_id": 1,\n  "canalPedido": "TOTEM",\n  "items": [\n    {"product_id": 1, "quantity": 2},\n    {"product_id": 2, "quantity": 1}\n  ]\n}''')
code_block(doc, '''{\n  "id": 101,\n  "unit_id": 1,\n  "customer_id": 5,\n  "canalPedido": "TOTEM",\n  "status": "AGUARDANDO_PAGAMENTO",\n  "subtotal_cents": 5430,\n  "discount_cents": 0,\n  "total_cents": 5430,\n  "items": [\n    {"product_id": 1, "quantity": 2, "unit_price_cents": 2290},\n    {"product_id": 2, "quantity": 1, "unit_price_cents": 850}\n  ]\n}''')
heading(doc, "6.6 Padrão comum de erro", 2)
body(doc, "Erros HTTP e de validação usam error, message, details, timestamp, path e requestId. Os códigos seguem a semântica HTTP: 200, 201 e 204 para sucesso; 400 para requisição inválida; 401 para autenticação; 403 para autorização; 404 para recurso ausente; 409 para conflito de negócio; 422 para corpo ou parâmetros inválidos; e 500 para falha interna sem expor detalhes técnicos ao consumidor.")
code_block(doc, '''{\n  "error": "CONFLITO_REGRA_NEGOCIO",\n  "message": "Estoque insuficiente para o produto 1.",\n  "details": [],\n  "timestamp": "2026-11-23T12:00:00Z",\n  "path": "/orders",\n  "requestId": "uuid-da-requisicao"\n}''')

heading(doc, "7 SEGURANÇA, LGPD E AUDITORIA", 1)
body(doc, "O sistema coleta nome, e-mail e hash de senha para cadastro e autenticação; mantém unidade, itens e valores para executar pedidos; e registra consentimento e saldo quando o cliente opta pela fidelidade. O cadastro não coleta cartão, documento nacional, endereço residencial ou dados sensíveis. A senha é derivada com PBKDF2-HMAC-SHA256, salt aleatório de 16 bytes e 310.000 iterações, usando hashlib; a documentação do Python recomenda função lenta, salt e iterações ajustadas para derivação de senha [3]. O token JWT é assinado com HS256, expira em tempo configurável e não guarda senha.")
body(doc, "Para o cadastro e a execução do pedido, a proposta considera como base legal de referência a execução de contrato ou de procedimentos preliminares solicitados pelo titular (LGPD, art. 7º, V). A participação em fidelidade é opcional e registrada com consentimento afirmativo e data/hora, tendo como referência o art. 7º, I. A LGPD define consentimento e exige finalidade determinada; também prevê revogação [7]. A base legal aplicável deve ser confirmada pelo controlador em contexto real e não é substituída por este exemplo acadêmico.")
body(doc, "A rota PATCH /loyalty/consent permite adesão ou revogação; a revogação retira o saldo de pontos ativo e preserva os lançamentos sem os expor a outros clientes. DELETE /privacy/me anonimiza nome e e-mail, desativa a conta e desvincula pedidos antigos do usuário. Registros operacionais permanecem vinculados a um identificador anonimizado para preservar consistência e trilha técnica. Prazo de retenção legal deve ser definido pela empresa fora do escopo deste MVP.")
body(doc, "A API não registra credenciais em resposta nem dados de cartão. Auditoria guarda ator, ação, recurso, identificador e detalhes operacionais para pedidos, pagamentos, movimentos de estoque, gestão de usuários, consulta individual e anonimização. Rotas administrativas verificam perfil; cliente só lê seus próprios pedidos. Para produção, ainda são necessários HTTPS, rotação/armazenamento de segredos, limite de tentativas de login, política formal de retenção e monitoramento.")

heading(doc, "8 PLANO DE TESTES E EVIDÊNCIAS", 1)
body(doc, "A coleção postman/Trabalho_Lanchonete.postman_collection.json contém 21 requisições ordenadas: 13 positivas e 8 negativas. Cada item possui assertions automatizadas. A execução local foi concluída com 21 requisições e 44 assertions aprovadas, sem falhas; o relatório JSON está em docs/evidencias/newman-run.json. A matriz identifica pré-condição, entrada, resposta esperada e evidência reproduzível.")
tests = [
    ("T01", "POST /auth/login", "Seed ADMIN disponível", "Credenciais válidas", "200; token e ADMIN", "Postman T01 / JSON Newman"),
    ("T02", "POST /auth/register", "E-mail não cadastrado", "Cliente com consentimento true", "201; CLIENTE, sem hash", "Postman T02 / JSON Newman"),
    ("T03", "POST /auth/login", "Cliente criado em T02", "E-mail e senha do cliente", "200; token CLIENTE", "Postman T03 / JSON Newman"),
    ("T04", "POST /auth/login", "Conta ADMIN existe", "Senha incorreta", "401; NAO_AUTENTICADO", "Postman T04 / JSON Newman"),
    ("T05", "GET /catalog/1", "Unidade e catálogo semeados", "Unidade 1; page=1, limit=20", "200; preço e saldo", "Postman T05 / JSON Newman"),
    ("T06", "GET /stock", "Token CLIENTE válido", "unit_id=1", "403; SEM_PERMISSAO", "Postman T06 / JSON Newman"),
    ("T07", "GET /units", "API disponível", "Sem Authorization", "401; NAO_AUTENTICADO", "Postman T07 / JSON Newman"),
    ("T08", "POST /stock/movements", "Token ADMIN e produto 1", "Entrada de 10 unidades", "201; saldo acrescido", "Postman T08 / JSON Newman"),
    ("T09", "POST /orders", "Token CLIENTE; saldo suficiente", "APP; produto 1; qty=2; Idempotency-Key", "201; pedido criado e estoque reservado", "Postman T09 / JSON Newman"),
    ("T10", "POST /orders", "Token CLIENTE", "Corpo sem canalPedido", "422; VALIDACAO", "Postman T10 / JSON Newman"),
    ("T11", "POST /orders", "Token CLIENTE", "product_id=999999", "404; NAO_ENCONTRADO", "Postman T11 / JSON Newman"),
    ("T12", "POST /orders", "Token CLIENTE; produto 2 com saldo 25", "product_id=2; quantity=99", "409; conflito de negócio", "Postman T12 / JSON Newman"),
    ("T13", "POST /payments/{id}/mock", "Pedido T09 pendente", "outcome=APROVADO; PIX_MOCK", "201; GATEWAY_MOCK aprovado", "Postman T13 / JSON Newman"),
    ("T14", "GET /orders", "Pedido T09 aprovado", "canalPedido=APP; status=PAGO", "200; pedido no filtro", "Postman T14 / JSON Newman"),
    ("T15", "GET /loyalty/me", "Cliente consentiu em T02", "Token CLIENTE", "200; enrolled e pontos", "Postman T15 / JSON Newman"),
    ("T16", "POST /orders", "Token CLIENTE; saldo suficiente", "Pedido APP para simular recusa", "201; AGUARDANDO_PAGAMENTO", "Postman T16 / JSON Newman"),
    ("T17", "POST /payments/{id}/mock", "Pedido T16 pendente", "outcome=RECUSADO; PIX_MOCK", "201; recusa registrada; pedido cancelado", "Postman T17 / JSON Newman"),
    ("T18", "GET /orders/{id}", "Pedido T17 recusado", "ID salvo em T16", "200; status CANCELADO", "Postman T18 / JSON Newman"),
    ("T19", "GET /audit", "Ações anteriores concluídas", "page=1; limit=100", "200; ações de pedido e pagamento", "Postman T19 / JSON Newman"),
    ("T20", "PATCH /loyalty/consent", "Token CLIENTE consentido", "consent=false", "200; consentimento false; saldo encerrado", "Postman T20 / JSON Newman"),
    ("T21", "POST /orders", "Token CLIENTE válido", "APP; product_id=1; quantity=-1", "422; VALIDACAO padronizada", "Postman T21 / JSON Newman"),
]
add_table(doc, ["ID", "Método/endpoint", "Pré-condição", "Entrada", "Esperado", "Evidência"], tests, [0.8, 2.8, 3.1, 3.1, 3.2, 3.0], 8.3)
heading(doc, "8.1 Evidências a capturar", 2)
evid = [
    ("EV01", "Terminal com instalação de requirements.txt, alembic upgrade head e uvicorn em execução."),
    ("EV02", "Swagger /docs e GET /health com retorno 200."),
    ("EV03", "Login válido, token Bearer e tentativa sem token (401) e perfil sem acesso (403)."),
    ("EV04", "Cardápio por unidade e saldo antes/depois de uma movimentação de estoque."),
    ("EV05", "Pedido com canalPedido, valores em centavos, estoque reservado e filtro por canal."),
    ("EV06", "Pagamento mock aprovado e resposta recusada com pedido cancelado e estoque restituído."),
    ("EV07", "Cliente com consentimento, saldo de fidelidade, revogação e registro de auditoria."),
    ("EV08", "Relatório JSON gerado pelo Newman em docs/evidencias/newman-run.json: 21 requisições, 44 assertions, 0 falhas. Captura visual no Postman pode ser feita para entrega presencial."),
    ("EV09", "Visualizador SQLite com tabelas e relações coerentes com o DER."),
]
add_table(doc, ["ID", "Evidência"], evid, [2.0, 14.0], 9)

heading(doc, "9 EXECUÇÃO E ENTREGA TÉCNICA", 1)
body(doc, "A aplicação exige Python 3.11 ou superior. Na pasta do projeto, crie ambiente virtual, copie .env.example para .env, troque TOKEN_SECRET e senha de administrador, instale requirements.txt, execute alembic upgrade head e inicie uvicorn app.main:app --reload. Os passos completos e a estrutura ficam no README.md; o Swagger é servido em /docs e OpenAPI em /openapi.json.")
code_block(doc, '''py -3.11 -m venv .venv\n.venv\\Scripts\\Activate.ps1\nCopy-Item .env.example .env\npip install -r requirements.txt\nalembic upgrade head\nuvicorn app.main:app --reload''')
body(doc, "A árvore inclui app/ para API, schemas, domínio, casos de uso, segurança e persistência; alembic/ para schema; postman/ para o contrato de teste; docs/assets/ para diagramas; requirements.txt e .env.example. O README contém endereço local do Swagger e passo de importação da coleção.")
body(doc, "O repositório público do projeto está disponível em https://github.com/brunovsspagnollo-ctrl/4644390-projeto-back-end-lanchonete. Ele contém o código-fonte, a coleção Postman, os diagramas e as evidências registradas. As capturas EV01-EV09 dependem da execução local. A coleção e o código não substituem essas evidências de execução.")

heading(doc, "10 CONCLUSÃO", 1)
body(doc, "O MVP implementa persistência relacional e um fluxo completo de domínio para pedido, reserva de estoque, pagamento mock e atualização de status. O canalPedido torna cada compra rastreável entre APP, TOTEM, BALCAO, PICKUP e WEB. Os diagramas relacionam atores, classes e tabelas com os endpoints; a sequência explica a interação crítica com o gateway. A separação de responsabilidades, as restrições e o snapshot do preço sustentam a consistência do fluxo.")
body(doc, "A proposta inclui autenticação com perfis, hash de senha, consentimento e revogação de fidelidade, erros comuns, auditoria e anonimização. SQLite foi priorizado para execução acadêmica local; para operação distribuída, é necessário adotar banco cliente-servidor, revisar concorrência, segredos, disponibilidade e observabilidade. O pagamento permanece simulado e não captura cartão. Campanhas usam regra percentual com validade; os pontos podem ser resgatados em pedido e são creditados somente após pagamento aprovado.")
body(doc, "A coleção Postman contém vinte e um cenários e foi executada por Newman contra o servidor local: 21 requisições, 44 assertions aprovadas e 0 falhas. O arquivo docs/evidencias/newman-run.json registra os resultados detalhados e pode ser aberto como evidência técnica. A suíte cobre autenticação e autorização, validação, estoque insuficiente, pagamentos aprovados e recusados, multicanalidade, fidelidade e auditoria. O conjunto de modelagem, código e contratos permite reproduzir o ambiente e analisar a coerência da solução.")

heading(doc, "REFERÊNCIAS", 1)
refs = [
    "[1] FASTAPI. First Steps: Interactive API documentation and OpenAPI. Disponível em: https://fastapi.tiangolo.com/tutorial/first-steps/. Acesso em: 23 nov. 2026.",
    "[2] FASTAPI. OAuth2 with Password (and hashing), Bearer with JWT tokens. Disponível em: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/. Acesso em: 23 nov. 2026.",
    "[3] PYTHON SOFTWARE FOUNDATION. hashlib - Secure hashes and message digests. Disponível em: https://docs.python.org/3/library/hashlib.html. Acesso em: 23 nov. 2026.",
    "[4] SQLALCHEMY. SQLAlchemy ORM Documentation, version 2.0. Disponível em: https://docs.sqlalchemy.org/en/20/orm/. Acesso em: 23 nov. 2026.",
    "[5] SQLITE. Appropriate Uses For SQLite. Disponível em: https://www.sqlite.org/whentouse.html. Acesso em: 23 nov. 2026.",
    "[6] ALEMBIC. Alembic Tutorial. Disponível em: https://alembic.sqlalchemy.org/en/latest/tutorial.html. Acesso em: 23 nov. 2026.",
    "[7] BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais. Brasília, DF: Presidência da República. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm. Acesso em: 23 nov. 2026.",
    "[8] UNINTER. Roteiro de Atividade Prática de Projeto Multidisciplinar - Trilha Back-End. Material fornecido no ambiente acadêmico, 2026.",
]
for ref in refs:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.left_indent = Cm(0)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(8)
    set_run(p.add_run(ref), 10)

# Keep the whole document in the requested plain black 12 point style.
for run_element in doc.element.iter(qn("w:r")):
    rpr = run_element.get_or_add_rPr()
    fonts = rpr.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn(f"w:{attr}"), "Times New Roman")
    size = rpr.find(qn("w:sz"))
    if size is None:
        size = OxmlElement("w:sz")
        rpr.append(size)
    size.set(qn("w:val"), "24")
    color = rpr.find(qn("w:color"))
    if color is None:
        color = OxmlElement("w:color")
        rpr.append(color)
    color.set(qn("w:val"), "000000")
    underline = rpr.find(qn("w:u"))
    if underline is not None:
        rpr.remove(underline)
for section in doc.sections:
    for part in (section.header, section.footer):
        for paragraph in part.paragraphs:
            for run in paragraph.runs:
                set_run(run, 12)

# Request Word to refresh generated fields such as the table of contents on open.
settings = doc.settings._element
update = OxmlElement("w:updateFields"); update.set(qn("w:val"), "true"); settings.append(update)
doc.core_properties.title = "Sistema de pedidos multicanal para a Rede Raízes do Nordeste"
doc.core_properties.subject = "Projeto Multidisciplinar - Trilha Back-End"
doc.core_properties.author = ""
doc.save(OUT)
print(OUT)
