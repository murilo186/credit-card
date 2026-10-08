# API e Operações

## Contrato HTTP

Todos os endpoints da primeira versão serão publicados sob o prefixo `/api/v1`.

### Clientes

```http
POST /api/v1/customers
```

Cria um cliente fictício.

### Cartões

```http
POST /api/v1/customers/{customer_id}/cards
GET  /api/v1/cards/{card_id}
POST /api/v1/cards/{card_id}/block
POST /api/v1/cards/{card_id}/unblock
```

Permitem emitir, consultar, bloquear e desbloquear um cartão.

### Transações

```http
POST /api/v1/cards/{card_id}/transactions
GET  /api/v1/cards/{card_id}/transactions
POST /api/v1/transactions/{transaction_id}/cancel
```

A autorização exige o cabeçalho:

```http
Idempotency-Key: 54068104-e063-4b93-9ecc-f58fe840ca34
```

Exemplo de requisição:

```json
{
  "merchant": "Loja Exemplo",
  "amount_cents": 15990
}
```

### Saúde da aplicação

```http
GET /health
```

Indica se a aplicação está disponível.

## Documentação OpenAPI

O FastAPI deverá disponibilizar:

```text
/docs   → Swagger UI
/redoc  → ReDoc
```

Os formatos completos de entrada, saída e respostas devem ser definidos nos schemas e nas rotas da aplicação.

## Códigos HTTP

| Código | Uso |
|---|---|
| `200 OK` | Consulta, bloqueio, desbloqueio ou cancelamento concluído |
| `201 Created` | Cliente, cartão ou transação criado |
| `400 Bad Request` | Regra ou dado inválido |
| `404 Not Found` | Recurso inexistente |
| `409 Conflict` | Conflito de idempotência ou estado |
| `422 Unprocessable Entity` | Payload incompatível com o schema |
| `500 Internal Server Error` | Falha interna inesperada |

Uma compra recusada por regra de negócio pode ser registrada normalmente e retornar seu status `DECLINED` na representação da transação.

## Tratamento de erros

Todas as respostas de erro devem utilizar o mesmo formato:

```json
{
  "error": {
    "code": "INSUFFICIENT_LIMIT",
    "message": "O cartão não possui limite suficiente.",
    "details": {
      "available_limit_cents": 10000,
      "requested_amount_cents": 15000
    }
  }
}
```

Códigos iniciais:

- `CUSTOMER_NOT_FOUND`
- `CARD_NOT_FOUND`
- `CARD_BLOCKED`
- `INVALID_AMOUNT`
- `INSUFFICIENT_LIMIT`
- `IDEMPOTENCY_CONFLICT`
- `TRANSACTION_NOT_FOUND`
- `TRANSACTION_NOT_CANCELLABLE`
- `INTERNAL_ERROR`

Erros internos não devem revelar stack traces, queries, credenciais ou variáveis de ambiente.

## Observabilidade

A aplicação produzirá logs estruturados contendo:

- Identificador da requisição.
- Endpoint acessado.
- Método HTTP.
- Código HTTP.
- Duração da operação.
- Identificador do cartão, quando aplicável.
- Identificador da transação, quando aplicável.
- Código de erro, quando aplicável.

Os logs não devem conter:

- Senhas.
- Credenciais do banco.
- Dados pessoais reais.
- Número completo de cartão.
- Conteúdo de variáveis de ambiente.

Na AWS, os logs serão enviados ao CloudWatch.
