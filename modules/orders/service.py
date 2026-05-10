"""
OrderService — núcleo do domínio de vendas.

Responsabilidades síncronas (resposta necessária antes de prosseguir):
  1. Validar itens
  2. Consultar preços (ProductService)
  3. Reservar estoque (InventoryService)
  4. Calcular total e persistir pedido

Responsabilidades assíncronas via EventBus (coreografia):
  5. Publicar 'order.created' → PaymentService reage de forma independente
  6. Escutar 'payment.approved' → atualiza status para PAGO
  7. Escutar 'payment.refused' → estorna estoque, atualiza para CANCELADO
  8. Escutar 'order.paid' → NotificationService notifica (não implementado aqui)

O OrderService NÃO importa PaymentService nem NotificationService.
O desacoplamento é total via EventBus.
"""

import logging
from decimal import Decimal
from sqlalchemy.orm import Session
from event_bus import event_bus
from exceptions import PedidoNaoEncontrado, PedidoSemItens, TransicaoDeStatusInvalida, ClienteNaoEncontrado
from modules.products.service import ProductService
from modules.inventory.service import InventoryService
from database import SessionLocal
from .models import Order, OrderItem
from .repository import OrderRepository
from .schemas import OrderIn

logger = logging.getLogger("order.service")

# Transições de status permitidas via PATCH manual
ALLOWED_MANUAL_TRANSITIONS = {
    "CRIADO":               ["AGUARDANDO_PAGAMENTO", "CANCELADO"],
    "AGUARDANDO_PAGAMENTO": ["CANCELADO"],
    "PAGO":                 ["FINALIZADO"],
}


class OrderService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = OrderRepository(db)
        self.product_svc = ProductService(db)
        self.inventory_svc = InventoryService(db)

    def create_order(self, data: OrderIn) -> Order:
        if not data.itens:
            raise PedidoSemItens()

        self._validate_client(data.cliente_id)

        itens_db = []
        total = Decimal("0")

        for item_in in data.itens:
            product = self.product_svc.get_product(item_in.produto_id)
            self.inventory_svc.reserve(item_in.produto_id, item_in.quantidade)

            preco = Decimal(str(product.preco))
            subtotal = preco * item_in.quantidade
            total += subtotal

            itens_db.append(OrderItem(
                produto_id=item_in.produto_id,
                quantidade=item_in.quantidade,
                preco_unitario=preco,
                subtotal=subtotal,
            ))

        order = Order(
            cliente_id=data.cliente_id,
            valor_total=total,
            status="CRIADO",
            itens=itens_db,
        )
        self.repo.create(order)
        logger.info(f"[Order] Pedido {order.id} criado | total=R${total} | status=CRIADO")

        # Transição imediata CRIADO → AGUARDANDO_PAGAMENTO antes de disparar o evento
        order.status = "AGUARDANDO_PAGAMENTO"
        self.repo.save(order)
        logger.info(f"[Order] Pedido {order.id} → AGUARDANDO_PAGAMENTO")

        event_bus.publish("order.created", {
            "order_id": order.id,
            "valor_total": float(total),
            "forma_pagamento": data.forma_pagamento,
        })

        self.db.refresh(order)
        return order

    def get_order(self, order_id: int) -> Order:
        order = self.repo.get_by_id(order_id)
        if not order:
            raise PedidoNaoEncontrado(order_id)
        return order

    def get_all(self) -> list[Order]:
        return self.repo.get_all()

    def update_status(self, order_id: int, new_status: str) -> Order:
        order = self.get_order(order_id)
        allowed = ALLOWED_MANUAL_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise TransicaoDeStatusInvalida(order.status, new_status)

        order.status = new_status
        self.repo.save(order)

        if new_status == "FINALIZADO":
            event_bus.publish("order.finalized", {"order_id": order_id})

        return order

    def cancel_order(self, order_id: int) -> Order:
        """
        DELETE /orders/{id} — cancela o pedido manualmente.
        Só é permitido para pedidos ainda não pagos.
        Estorna estoque e publica evento de cancelamento.
        """
        order = self.get_order(order_id)
        if order.status in ("PAGO", "FINALIZADO", "CANCELADO"):
            from exceptions import TransicaoDeStatusInvalida
            raise TransicaoDeStatusInvalida(order.status, "CANCELADO")

        for item in order.itens:
            self.inventory_svc.release(item.produto_id, item.quantidade)

        order.status = "CANCELADO"
        self.repo.save(order)
        logger.info(f"[Order] Pedido {order_id} cancelado manualmente")
        event_bus.publish("order.cancelled", {
            "order_id": order_id,
            "motivo": "cancelado pelo cliente",
        })
        return order

    def update_order(self, order_id: int, data: "OrderUpdateIn") -> Order:
        """
        PUT /orders/{id} — atualiza forma de pagamento enquanto pedido não foi pago.
        """
        from .schemas import OrderUpdateIn
        order = self.get_order(order_id)
        if order.status not in ("CRIADO", "AGUARDANDO_PAGAMENTO"):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Pedido já processado não pode ser alterado")
        if data.forma_pagamento:
            # Atualiza no pagamento pendente se existir
            from database import SessionLocal
            from modules.payments.repository import PaymentRepository
            db2 = SessionLocal()
            try:
                pay = PaymentRepository(db2).get_by_order(order_id)
                if pay:
                    pay.forma_pagamento = data.forma_pagamento
                    PaymentRepository(db2).save(pay)
            finally:
                db2.close()
        return order

    def _validate_client(self, cliente_id: int) -> None:
        from modules.clients.repository import ClientRepository
        client = ClientRepository(self.db).get_by_id(cliente_id)
        if not client:
            raise ClienteNaoEncontrado(cliente_id)

    # ------------------------------------------------------------------
    # Event handlers (registrados no main.py)
    # ------------------------------------------------------------------

    def handle_payment_approved(self, payload: dict) -> None:
        order_id = payload["order_id"]
        db = SessionLocal()
        try:
            repo = OrderRepository(db)
            order = repo.get_by_id(order_id)
            if order:
                order.status = "PAGO"
                repo.save(order)
                logger.info(f"[Order] Pedido {order_id} → PAGO")
                event_bus.publish("order.paid", {"order_id": order_id})
        finally:
            db.close()

    def handle_payment_refused(self, payload: dict) -> None:
        order_id = payload["order_id"]
        db = SessionLocal()
        try:
            repo = OrderRepository(db)
            order = repo.get_by_id(order_id)
            if order:
                # Estorna estoque de todos os itens
                inv_svc = InventoryService(db)
                for item in order.itens:
                    inv_svc.release(item.produto_id, item.quantidade)

                order.status = "CANCELADO"
                repo.save(order)
                logger.info(f"[Order] Pedido {order_id} → CANCELADO (estoque estornado)")
                event_bus.publish("order.cancelled", {
                    "order_id": order_id,
                    "motivo": payload.get("motivo", "pagamento recusado"),
                })
        finally:
            db.close()


# Singleton para handlers de eventos (não precisam de DB no momento da criação)
_order_event_handler = OrderService.__new__(OrderService)


def get_order_event_handler():
    return _order_event_handler
