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

## Imagem de produção e EC2

O `Dockerfile` possui dois targets:

- `development`: dependências de desenvolvimento, bind mount e reload.
- `production`: somente dependências de execução, sem bind mount e com usuário não
  privilegiado `app`.

Para simular a configuração de produção localmente, use a sobreposição:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d db
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm --no-deps api alembic upgrade head
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d api
```

Nesse modo, a API é publicada apenas em `127.0.0.1:8001`; o PostgreSQL continua sem
porta pública. Em uma EC2, um Nginx futuro deve receber tráfego externo e encaminhá-lo
para essa porta local. O Uvicorn recebe `SIGTERM`, tem até 25 segundos para encerrar
graciosamente e o Compose reserva 30 segundos antes de interrompê-lo à força.

### Roteiro manual para futura EC2

Este roteiro é manual e não cria recursos AWS, não registra domínio e não gera custo
automaticamente.

1. Crie uma instância EC2 Linux com tamanho compatível com o MVP e armazenamento
   persistente suficiente para o volume PostgreSQL.
2. Crie um Security Group permitindo SSH (`22`) apenas do seu IP administrativo.
   Enquanto não houver Nginx/HTTPS, não exponha a API ao público. Quando Nginx estiver
   configurado, permita somente `80` e `443` conforme a necessidade. Nunca abra `5432`.
3. Instale Docker Engine e o plugin Docker Compose seguindo a documentação da
   distribuição escolhida. Adicione o usuário operacional ao grupo Docker com cuidado
   e valide `docker compose version`.
4. Clone o repositório e crie `.env` com permissões restritas, por exemplo
   `chmod 600 .env`. Use senha forte e exclusiva para `POSTGRES_PASSWORD`; mantenha
   `DATABASE_URL` coerente com ela.
5. Construa e suba os containers com a sobreposição de produção mostrada acima.
   Execute `alembic upgrade head` dentro do container `api` antes de liberar tráfego.
6. Em etapa futura, configure Nginx como proxy reverso para `127.0.0.1:8001`, defina
   timeouts apropriados e habilite HTTPS com certificados válidos. Não exponha Uvicorn
   nem PostgreSQL diretamente.
7. Envie os logs JSON do container `api` para o CloudWatch usando um agente ou driver
   de logs configurado fora do repositório. Não envie `.env` nem dados sensíveis.
8. Configure AWS Budgets, alertas de custo e alarmes de utilização antes de manter a
   instância ligada. Revise volumes, snapshots, logs e regras do Security Group.

A implantação EC2 inicial compartilha aplicação e banco na mesma máquina, conforme o
ADR 0001. É adequada somente ao propósito educacional e deve evoluir para controles
adicionais e banco gerenciado caso os requisitos aumentem.
