# API de Cartões e Controle de Limite

## Visão geral

Este projeto implementa uma API de gerenciamento de cartões fictícios, limites e transações financeiras simuladas.

O objetivo é demonstrar práticas de desenvolvimento back-end, incluindo:

- Construção de API REST com Python e FastAPI.
- Persistência de dados com PostgreSQL.
- Separação de responsabilidades em camadas.
- Transações e controle de concorrência.
- Idempotência de operações.
- Testes unitários e de integração.
- Documentação OpenAPI.
- Containerização com Docker.
- Publicação na AWS.

O sistema é exclusivamente educacional e não processa pagamentos reais nem armazena dados financeiros sensíveis.

## Escopo funcional

O sistema deverá permitir:

- Cadastrar clientes fictícios.
- Emitir cartões fictícios.
- Consultar limite total e disponível.
- Bloquear e desbloquear cartões.
- Autorizar ou recusar compras.
- Cancelar compras aprovadas.
- Devolver o limite após um cancelamento.
- Impedir o processamento duplicado de uma requisição.
- Consultar o histórico de transações.

## Limitações conhecidas

A primeira versão não terá:

- Autenticação.
- Autorização por perfil.
- Faturas.
- Parcelamento.
- Juros.
- Integração bancária.
- Processamento real de pagamentos.
- Alta disponibilidade.
- Recuperação automática de desastre.
- Conformidade PCI-DSS.
- Separação entre conta de crédito e cartão físico.

Essas limitações são conscientes e mantêm o projeto adequado ao objetivo educacional e ao tempo disponível para o MVP.

## Evoluções possíveis

- Autenticação com JWT.
- Perfis `CUSTOMER` e `ADMIN`.
- Separação entre cartão e conta de crédito.
- PostgreSQL no Amazon RDS.
- Deploy automatizado.
- Métricas e alarmes.
- Faturas mensais.
- Ajuste de limite.
- Auditoria persistida.
- Paginação do histórico.

## Navegação

- [Contexto do sistema](architecture/system-context.md)
- [Modelo de dados](architecture/data-model.md)
- [Fluxos, concorrência e idempotência](architecture/flows.md)
- [Regras de negócio](business-logic/rules.md)
- [API e operações](api/endpoints.md)
- [Decisões arquiteturais](adrs/0001-decisoes-iniciais.md)
