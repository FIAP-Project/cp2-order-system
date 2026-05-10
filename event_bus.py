"""
EventBus — barramento de eventos in-process.

Substitui chamadas síncronas diretas entre serviços por um modelo
publish/subscribe: o publicador não sabe quem vai processar o evento.

Eventos publicados neste sistema:
  order.created          → PaymentService processa o pagamento
  payment.approved       → OrderService avança status; NotificationService notifica
  payment.refused        → OrderService cancela; NotificationService notifica
  order.paid             → NotificationService notifica cliente
  order.cancelled        → NotificationService notifica cliente
"""

import logging
from collections import defaultdict
from typing import Callable, Any

logger = logging.getLogger("event_bus")


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable) -> None:
        self._subscribers[event].append(handler)
        logger.debug(f"[EventBus] '{handler.__qualname__}' inscrito em '{event}'")

    def publish(self, event: str, payload: Any) -> None:
        handlers = self._subscribers.get(event, [])
        logger.info(f"[EventBus] Publicando '{event}' para {len(handlers)} handler(s) | payload={payload}")
        for handler in handlers:
            try:
                handler(payload)
            except Exception as exc:
                logger.error(f"[EventBus] Erro em '{handler.__qualname__}' ao processar '{event}': {exc}")


# Singleton compartilhado por toda a aplicação
event_bus = EventBus()
