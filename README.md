# CP2 — Sistema de Pedidos

**Disciplina:** SOA — Arquitetura de Software  
**Turma:** 3ESPY — 2026  
**Professora:** Damiana Costa

## Integrantes

| Nome | RM |
|------|----|
| Felipe Cerboncini Cordeiro | 554909 |
| Pedro Henrique Martins Alves dos Santos | 558107 |
| Milena Codinhoto da Silva | 554682 |
| Anthony K. Motobe | 558488 |
| Evellyn Valencia | 557929 |

---

## Descrição do Sistema

Sistema de pedidos para uma operação de delivery, implementado como uma **aplicação monolítica modular com separação clara de domínios e comunicação via EventBus in-process**.

A arquitetura responde diretamente ao feedback do CP1:

| Feedback recebido | Como foi endereçado |
|---|---|
| Muito HTTP síncrono | EventBus pub/sub desacopla Payment, Notification e Integration do fluxo principal |
| Order Service como orquestrador forte | Substituído por **coreografia**: Order publica `order.created` e não sabe quem processa |
| Catálogo e Estoque agrupados sem justificativa | Separados em módulos distintos com responsabilidades explícitas |
| Resiliência limitada | Circuit Breaker + retry com backoff linear implementados em código |
| Diagrama pouco legível | Novo diagrama com legenda de chamadas síncronas vs assíncronas |

---

## Tecnologias

- **Python 3.12**
- **FastAPI 0.111** — framework REST com Swagger UI automático
- **SQLAlchemy 2.0** — ORM com SQLite (sem servidor externo)
- **Pydantic v2** — validação e contratos da API
- **EventBus in-process** — pub/sub customizado para desacoplamento

---

## Como Executar

**Pré-requisito:** Python 3.11+

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Iniciar o servidor
uvicorn main:app --reload

# 3. Acessar a documentação interativa
# http://localhost:8000/docs
```

O banco SQLite (`orders.db`) é criado automaticamente na primeira execução.  
Os dados de exemplo (3 clientes, 4 produtos, estoques) são inseridos via seed automático.

---

## Estrutura do Projeto

```
cp2-order-system/
├── main.py              # Inicialização, registro de rotas e event handlers
├── database.py          # Configuração SQLAlchemy + SQLite
├── event_bus.py         # EventBus in-process (pub/sub)
├── exceptions.py        # Exceções de domínio centralizadas
├── seed.py              # Dados iniciais
├── requirements.txt
│
└── modules/
    ├── orders/          # Domínio de vendas (core)
    │   ├── controller.py
    │   ├── service.py
    │   ├── repository.py
    │   ├── models.py
    │   └── schemas.py
    ├── products/        # Domínio de catálogo
    ├── inventory/       # Domínio de estoque
    ├── payments/        # Domínio financeiro + circuit_breaker.py
    ├── notifications/   # Domínio de comunicação
    └── clients/         # Domínio de identidade
```

Cada módulo segue a mesma estrutura em camadas:  
`Controller → Service → Repository → Model`

---

## Fluxo Principal

```
POST /orders
    │
    ├── [sync] ProductService.get_product()     ← valida e obtém preço
    ├── [sync] InventoryService.reserve()       ← reserva estoque
    ├── Persiste pedido com status AGUARDANDO_PAGAMENTO
    │
    └── EventBus.publish("order.created") ──────────────────────────────┐
                                                                         ▼
                                                            PaymentService.handle_order_created()
                                                                 │
                                                    ┌────────────┴────────────┐
                                                    ▼                         ▼
                                        EventBus.publish(              EventBus.publish(
                                         "payment.approved")            "payment.refused")
                                                    │                         │
                              ┌─────────────────────┤              ┌──────────┘
                              ▼                     ▼              ▼
                  Order → PAGO             Notification     Order → CANCELADO
                              │             notifica         InventoryService.release()
                              ▼                              EventBus.publish("order.cancelled")
                  EventBus.publish("order.paid")                     │
                              │                                      ▼
                              ▼                              Notification notifica
                  Notification notifica
```

**Chamadas síncronas** (resposta necessária antes de prosseguir): Product e Inventory.  
**Todo o restante é assíncrono** via EventBus — Order não importa Payment nem Notification.

---

## Endpoints

### Orders
| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `POST` | `/orders/` | 201 / 400 / 404 / 409 | Cria pedido e dispara fluxo |
| `GET` | `/orders/` | 200 | Lista todos os pedidos |
| `GET` | `/orders/{id}` | 200 / 404 | Consulta pedido por ID |
| `PATCH` | `/orders/{id}/status` | 200 / 400 / 404 | Avança status (PAGO → FINALIZADO) |

### Products
| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/products/` | 200 | Lista catálogo |
| `GET` | `/products/{id}` | 200 / 404 | Consulta produto |

### Inventory
| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/inventory/{product_id}` | 200 | Consulta saldo em estoque |

### Payments
| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/payments/{order_id}` | 200 / 404 | Consulta pagamento do pedido |
| `POST` | `/payments/retry/{order_id}` | 200 | Retry manual de pagamento pendente |
| `GET` | `/payments/circuit-breaker` | 200 | Estado atual do circuit breaker |

### Notifications
| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/notifications/` | 200 | Lista todas as notificações |
| `GET` | `/notifications/order/{id}` | 200 | Notificações de um pedido |

### Clients
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/clients/` | Lista clientes |

---

## Regras de Negócio Implementadas

- Pedido não pode ser criado sem itens
- Produto deve existir no catálogo
- Estoque é verificado e reservado antes de confirmar o pedido
- Fluxo de status: `AGUARDANDO_PAGAMENTO → PAGO → FINALIZADO` ou `→ CANCELADO`
- Se pagamento for recusado, estoque é estornado automaticamente
- Pedido avança para PAGO apenas se pagamento for aprovado
- Transições de status inválidas retornam 400 com motivo

---

## Tratamento de Exceções

| Situação | Status HTTP | Mensagem |
|----------|-------------|----------|
| Pedido não encontrado | 404 | `Pedido {id} não encontrado` |
| Produto não encontrado | 404 | `Produto {id} não encontrado` |
| Cliente não encontrado | 404 | `Cliente {id} não encontrado` |
| Estoque insuficiente | 409 | `disponível=N, solicitado=M` |
| Pagamento recusado | 402 | `Gateway recusou a transação` |
| Transição de status inválida | 400 | `'ATUAL' → 'DESTINO'` |

---

## Resiliência — Circuit Breaker

O `PaymentService` implementa o padrão Circuit Breaker com três estados:

```
CLOSED ──(3 falhas)──► OPEN ──(30s timeout)──► HALF_OPEN ──(sucesso)──► CLOSED
                                                     │
                                               (falha) ──► OPEN
```

- **CLOSED:** operação normal; falhas são contadas
- **OPEN:** gateway indisponível; pedidos ficam em `AGUARDANDO_PAGAMENTO`; chamadas bloqueadas para não sobrecarregar o gateway
- **HALF_OPEN:** após 30s, uma chamada de prova é permitida

Além do circuit breaker, o serviço executa **retry com backoff linear** (até 3 tentativas, delay crescente) antes de abrir o circuito.

Estado visível em `GET /payments/circuit-breaker`.

---

## Diagrama Arquitetural

```
┌─────────────────────────────────────────────┐
│             Cliente (app / web)             │
└──────────────────────┬──────────────────────┘
                       │ HTTP
                       ▼
┌─────────────────────────────────────────────┐
│                  API Gateway                │
│         (FastAPI — roteamento)              │
└──┬──────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────┐   [sync] ┌───────────────────┐
│       Order Service          ├─────────►│  Product Service  │
│    (core — coreografia)      │          │  catálogo, preços │
│                              ├─────────►│ Inventory Service │
└──────────────┬───────────────┘   [sync] │ reserva, estoque  │
               │                          └───────────────────┘
               │ publish event
               ▼
┌─────────────────────────────────────────────────────────────────┐
│              Event Bus (in-process pub/sub)                     │
│  order.created · payment.approved · payment.refused · order.paid│
└───┬─────────────────────┬─────────────────────┬────────────────┘
    │ subscribe           │ subscribe            │ subscribe
    ▼                     ▼                      ▼
┌───────────────┐  ┌─────────────────┐  ┌────────────────────┐
│Payment Service│  │Notification Svc │  │ Integration Service│
│retry+circuit  │  │log/console/lista│  │  ERP/CRM adapter   │
│   breaker     │  └─────────────────┘  └────────────────────┘
└───────┬───────┘
        │ API
        ▼
  Gateway externo
  (simulado)
```

**Legenda:**
- `──►` Chamada síncrona HTTP (resposta necessária)
- `- -►` Evento assíncrono via EventBus

---

## Perguntas Discursivas

### 1. Como a comunicação entre os componentes do sistema foi organizada no código?

A comunicação foi dividida em dois tipos com critério claro:

**Chamadas síncronas (HTTP direto)** são usadas apenas quando a resposta é **obrigatória antes de prosseguir**. O `OrderService` chama o `ProductService` para obter o preço (sem preço, não há total) e o `InventoryService` para reservar o estoque (sem reserva, o produto pode ser vendido a alguém que não tem o item). Essas duas chamadas bloqueiam o fluxo intencionalmente — se falharem, o pedido não é criado.

**Comunicação assíncrona via EventBus** é usada para tudo que **não precisa de resposta imediata**. Após salvar o pedido, o `OrderService` publica `order.created` no `EventBus` e retorna `201` para o cliente. A partir daí, o `PaymentService` reage ao evento de forma independente, processa o pagamento e publica `payment.approved` ou `payment.refused`. O `OrderService` *escuta* esses eventos e atualiza o status. O `NotificationService` escuta `order.paid` e `order.cancelled` sem que nenhum outro serviço precise chamá-lo.

Essa separação está visível em `main.py`, na função `register_event_handlers()`, que centraliza o mapa completo de quem escuta o quê. O `OrderService` não tem nenhum `import` de `PaymentService` ou `NotificationService` — o desacoplamento é estrutural, não apenas de design.

### 2. Se o componente de pagamento ficasse indisponível em um cenário real, qual seria o impacto na sua arquitetura? Como sua solução poderia evoluir?

**Impacto na arquitetura atual:** como o `PaymentService` é acionado via EventBus e não bloqueia a criação do pedido, uma indisponibilidade do gateway **não derruba o fluxo principal**. O pedido é criado normalmente com status `AGUARDANDO_PAGAMENTO`. O `PaymentService` tenta o processamento com retry (até 3 tentativas com backoff linear) e, após falhas consecutivas, o circuit breaker muda para `OPEN`, parando chamadas ao gateway para não sobrecarregá-lo durante a recuperação. Pedidos pendentes ficam registrados no banco e podem ser reprocessados via `POST /payments/retry/{order_id}`.

**Como a solução evoluiria em produção:**

1. **Fila de mensagens persistente (RabbitMQ ou Kafka):** o EventBus in-process perde eventos se o processo cair. Em produção, `order.created` seria publicado em uma fila durável. O consumer do `PaymentService` leria dessa fila e, em caso de falha, a mensagem voltaria para a fila automaticamente (dead-letter queue), sem perda de dados.

2. **Worker de retry agendado (Celery + Redis):** em vez do retry manual exposto por endpoint, um worker executaria periodicamente buscando pagamentos com status `PENDENTE` e tentaria reprocessá-los, respeitando o estado do circuit breaker.

3. **Saga pattern com compensação:** para garantir consistência distribuída, cada etapa do fluxo teria uma ação de compensação registrada. Se o pagamento falhar após o estoque ser reservado, a saga garante o estorno — o que já é feito aqui no handler de `payment.refused`, mas de forma manual. Em produção, um orquestrador de saga (como Temporal ou AWS Step Functions) gerenciaria esse fluxo com garantias transacionais.

4. **Observabilidade:** circuit breaker exposto em `/payments/circuit-breaker` seria integrado com alertas (PagerDuty, Grafana) para notificar a equipe quando o circuito abrisse.
