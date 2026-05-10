"""
CP2 — Sistema de Pedidos
Arquitetura em camadas com EventBus para desacoplamento entre domínios.

Inicialização:
  1. Cria tabelas no SQLite
  2. Executa seed de dados iniciais
  3. Registra event handlers no EventBus
  4. Registra routers HTTP
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import engine, Base, SessionLocal
from event_bus import event_bus
from seed import run_seed

# -- Importar todos os models para que o Base os conheça antes do create_all
from modules.clients.models import Client           # noqa: F401
from modules.products.models import Product         # noqa: F401
from modules.inventory.models import Inventory      # noqa: F401
from modules.orders.models import Order, OrderItem  # noqa: F401
from modules.payments.models import Payment         # noqa: F401
from modules.notifications.models import Notification  # noqa: F401

# -- Importar controllers
from modules.clients.controller import router as clients_router
from modules.products.controller import router as products_router
from modules.inventory.controller import router as inventory_router
from modules.orders.controller import router as orders_router
from modules.payments.controller import router as payments_router
from modules.notifications.controller import router as notifications_router

# -- Importar services com handlers de eventos
from modules.payments.service import payment_service
from modules.notifications.service import notification_service
from modules.orders.service import OrderService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("main")


def register_event_handlers() -> None:
    """
    Inscreve os handlers no EventBus.

    Esta função é o mapa de toda a comunicação assíncrona do sistema.
    Para saber quem reage a cada evento, basta ler este bloco.
    """
    # order.created → PaymentService inicia processamento
    event_bus.subscribe("order.created", payment_service.handle_order_created)

    # payment.approved → OrderService avança status; NotificationService notifica
    order_handler = OrderService.__new__(OrderService)
    event_bus.subscribe("payment.approved", order_handler.handle_payment_approved)
    event_bus.subscribe("payment.approved", notification_service.handle_order_paid)

    # payment.refused → OrderService cancela e estorna estoque
    event_bus.subscribe("payment.refused", order_handler.handle_payment_refused)

    # order.cancelled → NotificationService notifica cancelamento
    event_bus.subscribe("order.cancelled", notification_service.handle_order_cancelled)

    # order.finalized → NotificationService notifica finalização
    event_bus.subscribe("order.finalized", notification_service.handle_order_finalized)

    logger.info("[Main] Event handlers registrados com sucesso")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("[Main] Tabelas criadas/verificadas")

    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()

    register_event_handlers()
    yield


app = FastAPI(
    title="CP2 — Sistema de Pedidos",
    description=(
        "Arquitetura em camadas com separação de domínios e EventBus in-process.\n\n"
        "**Fluxo principal:** `POST /orders` → estoque reservado (sync) → "
        "`order.created` publicado → PaymentService reage (async) → "
        "`payment.approved` ou `payment.refused` → OrderService atualiza status → "
        "NotificationService registra evento."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(clients_router)
app.include_router(products_router)
app.include_router(inventory_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(notifications_router)


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "system": "CP2 Order System"}
