# ADR 0001 — Decisões Arquiteturais Iniciais

- **Status:** Aceito
- **Data:** A definir
- **Responsáveis:** Equipe do projeto

## 1. Contexto

O projeto precisa demonstrar conhecimentos relevantes para uma vaga de estágio em desenvolvimento back-end com Python.

Os principais objetivos são:

- Construir uma API REST.
- Utilizar Python e FastAPI.
- Trabalhar com banco relacional.
- Demonstrar testes e documentação.
- Proteger operações de limite contra concorrência.
- Publicar a aplicação na AWS.
- Manter um escopo possível de concluir em pouco tempo.

As decisões devem equilibrar qualidade técnica, facilidade de aprendizado, custo e tempo de implementação.

## 2. Decisão: monólito modular

### Decisão

A aplicação será construída como um monólito modular.

### Motivos

- O domínio é pequeno.
- Existe apenas uma equipe e um único processo de deploy.
- Transações de cartão e limite precisam de consistência.
- Microsserviços aumentariam a complexidade operacional.
- A separação em módulos já oferece organização suficiente.

### Consequências positivas

- Deploy simples.
- Debug mais fácil.
- Transações locais no PostgreSQL.
- Menos infraestrutura.
- Menor tempo de desenvolvimento.

### Consequências negativas

- Todos os módulos são implantados juntos.
- Uma falha grave pode afetar toda a aplicação.
- Escalabilidade independente não está disponível.

### Alternativas rejeitadas

- Microsserviços.
- Arquitetura orientada a eventos.
- Funções Lambda separadas por endpoint.

Essas opções seriam excessivas para o escopo atual.

## 3. Decisão: FastAPI

### Decisão

FastAPI será utilizado como framework HTTP.

### Motivos

- Está alinhado aos diferenciais da vaga.
- Utiliza type hints do Python.
- Integra-se diretamente ao Pydantic.
- Gera OpenAPI e Swagger automaticamente.
- Possui boa experiência para desenvolvimento de APIs.
- Permite implementação rápida.

### Consequências positivas

- Menos código para validação.
- Documentação automática.
- Contratos de entrada e saída claros.
- Facilidade de testes com TestClient e HTTPX.

### Consequências negativas

- A equipe precisa compreender dependências e execução assíncrona.
- Uso incorreto de funções assíncronas pode bloquear a aplicação.
- Não oferece tantos recursos integrados quanto Django.

### Alternativa rejeitada

Django REST Framework foi considerado, mas oferece mais componentes do que o MVP necessita.

## 4. Decisão: PostgreSQL

### Decisão

PostgreSQL será o banco principal.

### Motivos

- O domínio possui relacionamentos claros.
- Operações de limite precisam de transações.
- Restrições e índices ajudam a proteger o domínio.
- O banco oferece bloqueio de linha com `FOR UPDATE`.
- PostgreSQL é mencionado na vaga.
- É amplamente utilizado em aplicações back-end.

### Consequências positivas

- Consistência transacional.
- Relacionamentos explícitos.
- Migrações controladas.
- Facilidade para consultas e auditoria.
- Proteção por constraints.

### Consequências negativas

- Requer administração e conexão persistente.
- O deploy é mais trabalhoso que uma solução serverless.
- Escalabilidade horizontal exige planejamento adicional.

### Alternativa rejeitada

DynamoDB foi considerado por sua integração com AWS e baixo custo operacional, mas PostgreSQL representa melhor o domínio e os requisitos da vaga.

## 5. Decisão: valores monetários em centavos

### Decisão

Valores monetários serão armazenados como inteiros em centavos.

Exemplo:

```text
R$ 159,90 → 15990
```

### Motivos

- Evita erros de precisão com ponto flutuante.
- Simplifica comparações.
- Facilita cálculos de limite.
- Torna o comportamento determinístico.

### Consequências

A aplicação será responsável por converter valores para apresentação quando necessário.

## 6. Decisão: bloqueio pessimista

### Decisão

A autorização e o cancelamento utilizarão bloqueio pessimista com `SELECT FOR UPDATE`.

### Motivos

Duas compras podem chegar simultaneamente e tentar consumir o mesmo limite. Sem coordenação, ambas poderiam ler o mesmo valor e serem aprovadas incorretamente.

### Operação

```sql
SELECT *
FROM cards
WHERE id = :card_id
FOR UPDATE;
```

A linha permanece bloqueada até o `COMMIT` ou `ROLLBACK`.

### Consequências positivas

- Implementação explícita.
- Protege o limite contra corridas.
- Adequado ao pequeno volume do projeto.
- Fácil de explicar e testar.

### Consequências negativas

- Transações longas podem gerar espera.
- Ordem inconsistente de bloqueios pode causar deadlocks.
- Pode reduzir o paralelismo em cartões muito acessados.

### Alternativa rejeitada

O bloqueio otimista com coluna de versão foi considerado, mas exigiria tratamento adicional de conflitos e novas tentativas.

## 7. Decisão: idempotência obrigatória

### Decisão

A criação de transações exigirá uma `Idempotency-Key`. A combinação `card_id + idempotency_key` será única.

### Motivos

Clientes HTTP podem repetir requisições quando:

- A conexão é interrompida.
- A resposta demora.
- O cliente possui política automática de retry.
- O usuário envia a mesma ação novamente.

### Consequências positivas

- Evita cobrança duplicada.
- Evita redução duplicada do limite.
- Permite retornar o resultado anterior.
- Demonstra uma prática relevante para APIs financeiras.

### Consequências negativas

- É necessário armazenar e consultar a chave.
- Deve existir uma política para reutilização com payload diferente.
- As chaves aumentam o volume de dados persistidos.

## 8. Decisão: SQLAlchemy e Alembic

### Decisão

SQLAlchemy será utilizado para acesso ao banco e Alembic para migrações.

### Motivos

- Separação entre domínio e detalhes de persistência.
- Controle explícito de transações.
- Compatibilidade com PostgreSQL.
- Histórico reproduzível das mudanças do esquema.
- Aderência ao ecossistema Python.

### Consequências

Mudanças de models que afetem o banco deverão ser acompanhadas por uma migração Alembic revisada. A geração automática não substitui a revisão manual da migração.

## 9. Decisão: Docker Compose no desenvolvimento

### Decisão

FastAPI e PostgreSQL serão executados localmente por Docker Compose.

### Motivos

- Ambiente reproduzível.
- Menos dependências instaladas diretamente.
- Mesma versão do PostgreSQL para todos.
- Inicialização simplificada.

### Consequências

O desenvolvedor precisa ter Docker instalado e compreender os comandos básicos de containers e volumes.

## 10. Decisão: EC2 no primeiro deploy

### Decisão

A primeira publicação utilizará uma instância EC2 executando containers Docker.

### Motivos

- Menor tempo de configuração.
- Demonstra uso de EC2.
- Permite executar FastAPI e PostgreSQL.
- Evita configurar Lambda, VPC, RDS Proxy e múltiplos serviços no MVP.

### Consequências positivas

- Deploy compreensível.
- Infraestrutura pequena.
- Facilidade para inspecionar containers e logs.

### Consequências negativas

- Aplicação e banco compartilham a mesma máquina.
- Não há alta disponibilidade.
- O banco depende do armazenamento da instância.
- A máquina gera custo enquanto estiver ativa.

### Evolução prevista

Migrar o PostgreSQL para RDS e manter somente a aplicação na camada de computação.

## 11. Decisão: autenticação fora do MVP

### Decisão

Autenticação e autorização não farão parte da primeira versão.

### Motivos

- O objetivo principal é demonstrar regras de limite e transações.
- JWT e gerenciamento de usuários aumentariam o escopo.
- O projeto precisa ser concluído em poucas horas.

### Consequências

A API não poderá ser considerada pronta para uso real.

Uma versão futura poderá adicionar login, tokens JWT, perfil `CUSTOMER`, perfil `ADMIN` e controle de acesso por cartão.

## 12. Decisão: dados exclusivamente fictícios

### Decisão

O sistema não armazenará dados financeiros ou pessoais reais.

### Motivos

- O projeto é educacional.
- Não existe necessidade de processar dados sensíveis.
- Armazenar dados reais aumentaria requisitos de segurança e conformidade.

### Consequências

Cartões serão identificados por UUID e quatro dígitos simulados.

Não serão armazenados:

- PAN completo.
- CVV.
- CPF.
- Senhas de cartão.
- Dados bancários.

## 13. Resultado

As decisões formam uma arquitetura que:

- Pode ser construída rapidamente.
- Demonstra fundamentos de back-end.
- Protege operações críticas.
- É compatível com o perfil técnico da vaga.
- Pode evoluir sem exigir uma reescrita imediata.

Este ADR deverá ser revisado caso o projeto passe a exigir autenticação, integração externa, maior escala ou processamento financeiro real.
