# API de Cartões e Controle de Limite

MVP educacional de uma API para cadastro de clientes fictícios, emissão de cartões
fictícios, controle de limite e autorização de transações. A aplicação usa FastAPI,
PostgreSQL, SQLAlchemy e Alembic em containers Docker.

> Este projeto usa somente dados fictícios. Não processa pagamentos reais e não
> armazena PAN completo, CVV, CPF, senhas, dados bancários ou dados pessoais reais.
> Ele não deve ser considerado adequado para uma operação financeira real.

## Pré-requisitos

- Docker Engine com Docker Compose v2.
- Git, para clonar o repositório.

Python, PostgreSQL, Alembic, Pytest, Ruff e MkDocs **não precisam ser instalados
nem executados diretamente no host**. Todos os comandos dessas ferramentas são
executados nos containers.

## Configuração

Crie o arquivo local de ambiente a partir do exemplo:

```bash
cp .env.example .env
```

O `.env` não é versionado. Para desenvolvimento, os valores fictícios do exemplo
são suficientes. Em um servidor, gere uma senha forte para `POSTGRES_PASSWORD` e
atualize `DATABASE_URL` com a mesma credencial, sem incluí-las no Git ou na imagem.

Variáveis usadas:

- `APP_NAME`: nome exposto pela API.
- `APP_ENV`: `development` no ambiente local e `production` no servidor.
- `DATABASE_URL`: URL SQLAlchemy apontando para o serviço `db`.
- `LOG_LEVEL`: nível dos logs estruturados.
- `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD`: inicialização do PostgreSQL.

## Desenvolvimento local com Docker Compose

O Compose padrão é o ambiente de desenvolvimento: monta o código local e habilita
reload do Uvicorn somente quando `APP_ENV=development`.

Em hosts cujo usuário local não seja `1000:1000`, exporte `LOCAL_UID` e `LOCAL_GID`
com `id -u` e `id -g` antes de usar o Compose para preservar as permissões dos
artefatos gerados pelos testes.

```bash
docker compose up --build -d
docker compose run --rm --no-deps api alembic upgrade head
```

A API fica disponível em:

- Swagger: <http://127.0.0.1:8001/docs>
- ReDoc: <http://127.0.0.1:8001/redoc>
- Saúde: <http://127.0.0.1:8001/health>

Para acompanhar logs e encerrar o ambiente:

```bash
docker compose logs -f api
docker compose down
```

`docker compose down` preserva o volume `postgres_data`. Use
`docker compose down --volumes` somente quando desejar remover intencionalmente os
dados locais.

## Migrações

As migrações são executadas exclusivamente pelo container da API, após o `db`
ficar saudável:

```bash
docker compose run --rm --no-deps api alembic upgrade head
docker compose run --rm --no-deps api alembic current
```

Em produção, execute a migração uma única vez para cada versão publicada. Não use
`Base.metadata.create_all()`.

## Qualidade

Ruff e Pytest também rodam dentro da imagem de desenvolvimento:

```bash
docker compose run --rm --no-deps api ruff check .
docker compose run --rm --no-deps api ruff format --check app tests
docker compose run --rm --no-deps api pytest
```

## Documentação técnica

O MkDocs usa a imagem oficial do Material for MkDocs, sem instalar MkDocs na imagem
da API ou no host:

```bash
docker compose --profile docs up docs
```

O site fica disponível em <http://127.0.0.1:8000>. Encerre com `Ctrl+C` ou execute
`docker compose --profile docs down` em outro terminal.

Consulte a [documentação completa](docs/index.md) para arquitetura, modelo de dados,
fluxos, regras de negócio e decisões arquiteturais.

## Deploy demonstrável: AWS EC2 e CloudWatch

> Status: publicado para fins de demonstração em uma instância AWS EC2.

- Swagger/OpenAPI: <http://18.228.213.100/docs>
- Health check: <http://18.228.213.100/health>

O IP público pode mudar se a instância for parada e iniciada novamente. Os links
acima representam o ambiente de demonstração enquanto a instância estiver ligada.

### Arquitetura implantada

```text
Internet
  |
  | HTTP :80
  v
Nginx (EC2)
  |
  | 127.0.0.1:8000
  v
FastAPI + Uvicorn (container Docker)
  |
  | rede Docker
  v
PostgreSQL (container Docker, sem porta pública)

Logs dos containers + métricas de memória/disco
  |
  v
Amazon CloudWatch
```

O Security Group da instância permite HTTP (`80`) para acesso à demonstração e
SSH (`22`) somente para o IP administrativo e o EC2 Instance Connect. As portas
`8000`, `8001` e `5432` não são abertas publicamente.

O CloudWatch Agent coleta logs JSON dos containers no grupo
`/credit-card/docker`, com retenção de sete dias, além de métricas de memória e
disco no namespace `CWAgent`. Não há credenciais AWS no repositório: a EC2 usa
uma IAM Role com a política `CloudWatchAgentServerPolicy`.

### Evidências de observabilidade

<!-- observability-screenshot: cloudwatch-logs.png -->
<!-- observability-screenshot: cloudwatch-metrics.png -->

## Imagem de produção e EC2

O `Dockerfile` possui dois targets:

- `development`: dependências de desenvolvimento, bind mount e reload.
- `production`: somente dependências de execução, sem bind mount e com usuário não
  privilegiado `app`.

Para reproduzir a configuração de produção localmente ou em uma EC2, use a
sobreposição:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml build api
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d db
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm --no-deps api alembic upgrade head
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d api
```

Nesse modo, a API é publicada apenas em `127.0.0.1:8000`; o PostgreSQL continua sem
porta pública. Na EC2, o Nginx recebe tráfego externo na porta `80` e o encaminha para
essa porta local. O Uvicorn recebe `SIGTERM`, tem até 25 segundos para encerrar
graciosamente e o Compose reserva 30 segundos antes de interrompê-lo à força.

### Atualização manual da EC2

`git pull` baixa o código, mas não reinicia a imagem que está em execução. Após
enviar uma versão revisada ao GitHub, atualize a instância manualmente:

```bash
cd ~/credit-card
git pull --ff-only
docker compose -f docker-compose.yml -f docker-compose.prod.yml build api
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --force-recreate api
curl http://127.0.0.1/health
```

Quando houver uma nova migração Alembic, execute antes de recriar a API:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm --no-deps api alembic upgrade head
```

Alterações exclusivamente em `README.md` ou `docs/` não exigem novo deploy.

### Limites do ambiente demonstrável

O ambiente compartilha aplicação e banco na mesma EC2 e utiliza HTTP sem domínio ou
TLS. Essa escolha é intencional para um MVP educacional demonstrável. Em um cenário
real, a evolução incluiria HTTPS, domínio, banco gerenciado, backup, alertas e
segregação adicional de rede.
