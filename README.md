# API de pedidos da Rede Raízes do Nordeste

Back-end acadêmico em Python, FastAPI e SQLite. A API demonstra autenticação com perfis, cardápio e estoque por unidade, pedidos multicanal, fidelidade, promoções, pagamento externo simulado e auditoria.

## Requisitos

- Python 3.11 ou superior
- pip
- Postman para reproduzir a coleção de chamadas

## Configuração local

No PowerShell, abra esta pasta e rode:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Edite `.env` antes de iniciar. Troque `TOKEN_SECRET` por uma chave aleatória com pelo menos 32 caracteres e altere a senha do usuário administrador de demonstração. O `.env` é ignorado pelo Git.

## Banco e migrações

O banco padrão é o arquivo SQLite `lanchonete.db`. A migração inicial cria as tabelas:

```powershell
alembic upgrade head
```

Ao iniciar, a aplicação completa a criação idempotente do esquema e insere dados demonstrativos se a base estiver vazia: uma unidade, dois produtos, saldos de estoque e o usuário administrador indicado no `.env`.

## Iniciar a API

```powershell
uvicorn app.main:app --reload
```

- API local: `http://127.0.0.1:8000`
- Swagger/OpenAPI: `http://127.0.0.1:8000/docs`
- Esquema OpenAPI: `http://127.0.0.1:8000/openapi.json`
- Verificação: `GET /health`

## Arquitetura

| Camada | Arquivos | Responsabilidade |
|---|---|---|
| Domain | `app/domain.py` | Perfis e estados válidos do domínio |
| Application | `app/services.py` | Criação de pedido, estoque, fidelidade, pagamento e transições |
| Infrastructure | `app/models.py`, `app/database.py`, `alembic/` | Persistência SQLAlchemy, SQLite e migração |
| API | `app/main.py`, `app/schemas.py`, `app/security.py` | Rotas, contratos, autenticação e autorização |

## Endpoints por recurso

| Recurso | Endpoints principais |
|---|---|
| Autenticação | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Usuários | `POST /users/staff` (ADMIN) |
| Unidades | `GET /units`, `POST /units` |
| Produtos e cardápio | `POST /products`, `GET /products`, `POST /units/{unit_id}/catalog`, `GET /catalog/{unit_id}` |
| Estoque | `GET /stock?unit_id=1`, `POST /stock/movements` |
| Promoções | `POST /promotions` |
| Pedidos | `POST /orders`, `GET /orders`, `GET /orders/{order_id}`, `POST /orders/{order_id}/cancel`, `PATCH /orders/{order_id}/status` |
| Pagamento | `POST /payments/{order_id}/mock` |
| Fidelidade | `GET /loyalty/me`, `GET /loyalty/history`, `PATCH /loyalty/consent` |
| Privacidade e auditoria | `DELETE /privacy/me`, `GET /audit` |

`POST /orders` exige o campo `canalPedido` (`APP`, `TOTEM`, `BALCAO`, `PICKUP` ou `WEB`) e o cabeçalho `Idempotency-Key`. A consulta filtra por canal com `GET /orders?canalPedido=TOTEM`. Valores monetários são armazenados em centavos inteiros.

## Fluxo principal

1. Um cliente se cadastra e faz login para obter token Bearer.
2. Consulta `GET /catalog/{unit_id}`.
3. Cria pedido informando canal, unidade e itens. A API valida estoque, preço de cada unidade, cupom e resgate de pontos; reserva o estoque e inicia o pedido como `AGUARDANDO_PAGAMENTO`.
4. Envia o pagamento de demonstração em `POST /payments/{order_id}/mock`, com `outcome` `APROVADO` ou `RECUSADO`.
5. Aprovação move o pedido a `PAGO`; a cozinha avança `EM_PREPARO` → `PRONTO` → `ENTREGUE`. Recusa cancela o pedido e devolve o estoque reservado.

O gateway é deliberadamente simulado: nenhum dado de cartão é coletado ou enviado. O pedido exige chave de idempotência; o pagamento de um pedido só pode ser processado uma vez.

## Perfis

- `ADMIN`: gestão total, criação de usuários internos e leitura da auditoria.
- `GERENTE`: unidades, catálogo, produtos, promoções e estoque.
- `ATENDENTE`: consulta e criação de pedidos; processamento de pagamento mock.
- `COZINHA`: consulta e avanço do status do pedido.
- `CLIENTE`: seus pedidos, saldo de fidelidade e consentimento.

O cadastro público sempre cria perfil `CLIENTE`. A conta ADMIN inicial é criada a partir de `.env`; perfis internos adicionais são cadastrados por ADMIN em `/users/staff`.

## Erros

Todas as falhas usam o mesmo formato. Exemplo de produto ausente:

```json
{
  "error": "NAO_ENCONTRADO",
  "message": "Produto 99999 não consta no cardápio da unidade.",
  "details": [],
  "timestamp": "2026-11-23T12:00:00Z",
  "path": "/orders",
  "requestId": "uuid"
}
```

Códigos centrais: `200` sucesso, `201` criação, `204` anonimização, `401` sem token/credenciais inválidas, `403` perfil sem acesso, `404` recurso ausente, `409` conflito/regra de negócio e `422` campo inválido.

## Coleção Postman e plano de cenários

Importe `postman/Trabalho_Lanchonete.postman_collection.json`, confira as variáveis de administrador e execute as chamadas em ordem. A coleção inclui 21 chamadas com 13 cenários positivos e 8 negativos: login, cadastro, consulta, movimentação de estoque, pedido, pagamento aprovado/recusado, filtro por canal, saldo de fidelidade, auditoria, revogação de consentimento, ausência de token, perfil sem permissão, dois casos de validação, produto ausente e estoque insuficiente. As verificações estão organizadas nas pastas Autenticacao, Cardapio e autorizacao, e Pedidos e pagamentos.

Os cenários foram executados localmente pelo Newman: 21 requisições, 44 assertions aprovadas e 0 falhas. O relatório completo está em [evidências/newman-run.json](evid%C3%AAncias/newman-run.json) e o resumo em [evidências/newman-resumo.txt](evid%C3%AAncias/newman-resumo.txt). Para repetir pelo Postman, inicie a API e use o Collection Runner em ordem. Para repetir pelo Newman, instale Node.js e Newman e execute `newman run postman/Trabalho_Lanchonete.postman_collection.json --reporters cli,json --reporter-json-export evidências/newman-run.json`. O cliente recebe e-mail aleatório em domínio reservado `example.com` a cada execução.

Os prints complementares da execução estão na [pasta de evidências](evid%C3%AAncias/Prints/), incluindo respostas do Swagger, pagamentos, estoque, fidelidade e auditoria.

## Segurança, LGPD e limites

Senhas são armazenadas com PBKDF2-HMAC-SHA256 e salt aleatório. O token JWT assinado tem validade configurável. O cadastro minimiza os dados a nome, e-mail e senha; participação na fidelidade é opt-in e o aceite tem data/hora. A rota `PATCH /loyalty/consent` registra/revoga o aceite e encerra o saldo de pontos quando há revogação. A rota `DELETE /privacy/me` anonimiza a conta e desvincula os pedidos antigos, preservando registros operacionais anonimizados. Ações administrativas, consulta individual de pedido e mudanças sensíveis geram auditoria sem guardar senha ou dados de cartão.

É um MVP acadêmico local. Não oferece gateway financeiro real, deploy, alta disponibilidade, limites de tentativa de login, TLS, gestão de segredos de produção ou trilha de migração incremental entre múltiplas versões do esquema. Para produção, mover para PostgreSQL, usar serviço de identidade/segredos, TLS, monitoramento e revisão jurídica das bases legais e retenção.

## Árvore resumida

```text
app/                 API, schemas, domínio, aplicação e persistência
alembic/             migração inicial
postman/             coleção importável com cenários e assertions
evidências/          prints da API e relatórios de execução Newman
requirements.txt     dependências
.env.example         variáveis de configuração
```

## Publicação e evidências finais

Repositório público do projeto: https://github.com/brunovsspagnollo-ctrl/4644390-projeto-back-end-lanchonete

O repositório contém o código-fonte, a coleção Postman e as evidências de teste. Não há deploy incluído. O Swagger local funciona em `http://127.0.0.1:8000/docs` enquanto a API estiver rodando.
