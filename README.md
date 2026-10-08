# API de Cartões e Controle de Limite

MVP educacional de uma API para emissão de cartões fictícios, controle de limite e autorização de transações.

O projeto foi desenhado para demonstrar práticas de desenvolvimento back-end com Python, incluindo regras de negócio, persistência relacional, consistência transacional, controle de concorrência, idempotência, testes e documentação.

> Este é um projeto exclusivamente educacional. Ele não processa pagamentos reais e não deve armazenar dados pessoais ou financeiros verdadeiros.

## Stack planejada

- Python 3.12
- FastAPI e Uvicorn
- Pydantic
- SQLAlchemy e Alembic
- PostgreSQL
- Pytest
- Docker e Docker Compose
- AWS EC2 e CloudWatch
- MkDocs Material

## Arquitetura

A solução utiliza um monólito modular. A API FastAPI e o PostgreSQL serão executados em containers Docker. No primeiro deploy, os containers poderão ser hospedados em uma instância AWS EC2, com logs enviados ao CloudWatch.

## Executando a aplicação

Quando a implementação da API estiver disponível:

```bash
docker compose up --build
```

## Visualizando a documentação

Instale o Material for MkDocs e inicie o servidor local:

```bash
pip install mkdocs-material
mkdocs serve
```

A documentação ficará disponível em:

```text
http://127.0.0.1:8000
```

Consulte a [documentação completa](docs/index.md) para conhecer a arquitetura, o modelo de dados, os fluxos, as regras de negócio e as decisões arquiteturais.
