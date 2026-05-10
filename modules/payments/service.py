"""
PaymentService — domínio de pagamentos.

Este serviço NÃO é chamado diretamente pelo OrderService.
Ele ESCUTA o evento 'order.created' publicado no EventBus.
Isso elimina o acoplamento direto: OrderService não importa PaymentService.

Estratégias de resiliência implementadas:
  1. Retry com backoff linear (até 3 tentativas)
  2. Circuit Breaker: após 3 falhas consecutivas, abre o circuito
     e pedidos ficam em AGUARDANDO_PAGAMENTO até recuperação
  3. Fallback: se gateway indisponível, não bloqueia o fluxo principal
"""

import random
import time
import logging
from datetime import datetime

from database import SessionLocal
from event_bus import event_bus
from .models import Payment
from .repository import PaymentRepository
from .circuit_breaker import circuit_breaker

logger = logging.getLogger("payment.service")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 0.2


class PaymentService:

    def handle_order_created(self, payload: dict) -> None:
        """
        Handler do evento 'order.created'.
        Recebe: {order_id, valor_total, forma_pagamento}
        """
        order_id = payload["order_id"]
        valor = payload["valor_total"]
        forma = payload.get("forma_pagamento", "CARTAO_CREDITO")

        db = SessionLocal()
        try:
            repo = PaymentRepository(db)
            payment = Payment(pedido_id=order_id, valor=valor, forma_pagamento=forma)
            repo.create(payment)

            if circuit_breaker.is_open():
                logger.warning(
                    f"[Payment] Circuit OPEN — pedido {order_id} aguardará retry"
                )
                # Pedido já está em AGUARDANDO_PAGAMENTO (definido pelo OrderService
                # ao publicar o evento). Nenhuma ação adicional necessária aqui.
                return

            self._process_with_retry(payment, repo, db)
        finally:
            db.close()

    def _process_with_retry(self, payment: Payment, repo: PaymentRepository, db) -> None:
        order_id = payment.pedido_id

        for attempt in range(1, MAX_RETRIES + 1):
            payment.tentativas = attempt
            try:
                approved = self._call_gateway(float(payment.valor))

                if approved:
                    payment.status = "APROVADO"
                    payment.data_pagamento = datetime.now()
                    repo.save(payment)
                    circuit_breaker.record_success()
                    logger.info(f"[Payment] Pedido {order_id} APROVADO (tentativa {attempt})")
                    event_bus.publish("payment.approved", {"order_id": order_id})
                else:
                    payment.status = "RECUSADO"
                    repo.save(payment)
                    logger.info(f"[Payment] Pedido {order_id} RECUSADO pelo gateway")
                    event_bus.publish(
                        "payment.refused",
                        {"order_id": order_id, "motivo": "Gateway recusou a transação"},
                    )
                return

            except GatewayUnavailableError as exc:
                circuit_breaker.record_failure()
                logger.warning(
                    f"[Payment] Tentativa {attempt}/{MAX_RETRIES} falhou: {exc}"
                )
                if attempt < MAX_RETRIES and not circuit_breaker.is_open():
                    time.sleep(RETRY_DELAY_SECONDS * attempt)
                else:
                    logger.error(f"[Payment] Esgotou retries — pedido {order_id} aguarda retry manual")
                    payment.status = "PENDENTE"
                    repo.save(payment)
                    return

    def retry_pending(self, order_id: int) -> dict:
        """Retry manual para pedidos em AGUARDANDO_PAGAMENTO (simula worker agendado)."""
        db = SessionLocal()
        try:
            repo = PaymentRepository(db)
            payment = repo.get_by_order(order_id)
            if not payment or payment.status != "PENDENTE":
                return {"message": "Nenhum pagamento pendente para este pedido"}

            if circuit_breaker.is_open():
                return {"message": "Circuit ainda OPEN — tente novamente mais tarde"}

            self._process_with_retry(payment, repo, db)
            return {"message": f"Retry executado — status atual: {payment.status}"}
        finally:
            db.close()

    @staticmethod
    def _call_gateway(valor: float) -> bool:
        """
        Simula chamada ao gateway externo.
        - Valor == 0.01 → sempre recusado (útil para testes)
        - Valor > 500  → 50% de aprovação
        - Demais       → 85% de aprovação
        Lança GatewayUnavailableError para simular indisponibilidade
        (probabilidade baixa: 5%).
        """
        if random.random() < 0.05:
            raise GatewayUnavailableError("Gateway timeout")

        if valor == 0.01:
            return False
        if valor > 500:
            return random.random() < 0.50
        return random.random() < 0.85


class GatewayUnavailableError(Exception):
    pass


payment_service = PaymentService()
