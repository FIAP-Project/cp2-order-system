"""
NotificationService — domínio de comunicação transacional.

Não é chamado diretamente por nenhum serviço.
Escuta eventos do EventBus e registra as notificações de forma assíncrona.

Este desacoplamento garante que uma falha no serviço de notificação
nunca afete o fluxo de criação ou pagamento de pedidos.
"""

import logging
from database import SessionLocal
from .models import Notification
from .repository import NotificationRepository

logger = logging.getLogger("notification.service")

TEMPLATES = {
    "order.paid": "Seu pedido #{order_id} foi confirmado e está sendo preparado!",
    "order.cancelled": "Infelizmente seu pedido #{order_id} foi cancelado. Motivo: {motivo}",
    "order.finalized": "Seu pedido #{order_id} foi finalizado. Obrigado pela preferência!",
}


class NotificationService:

    def handle_order_paid(self, payload: dict) -> None:
        self._log("PAGAMENTO_APROVADO", payload["order_id"],
                  TEMPLATES["order.paid"].format(**payload))

    def handle_order_cancelled(self, payload: dict) -> None:
        motivo = payload.get("motivo", "pagamento recusado")
        self._log(
            "PEDIDO_CANCELADO",
            payload["order_id"],
            TEMPLATES["order.cancelled"].format(order_id=payload["order_id"], motivo=motivo),
        )

    def handle_order_finalized(self, payload: dict) -> None:
        self._log("PEDIDO_FINALIZADO", payload["order_id"],
                  TEMPLATES["order.finalized"].format(**payload))

    def _log(self, tipo: str, order_id: int, mensagem: str) -> None:
        logger.info(f"[Notification] {tipo} | pedido={order_id} | {mensagem}")
        db = SessionLocal()
        try:
            repo = NotificationRepository(db)
            repo.create(Notification(pedido_id=order_id, tipo=tipo, mensagem=mensagem))
        finally:
            db.close()


notification_service = NotificationService()
