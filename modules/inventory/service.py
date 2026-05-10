import logging
from sqlalchemy.orm import Session
from exceptions import EstoqueInsuficiente
from .repository import InventoryRepository

logger = logging.getLogger("inventory.service")


class InventoryService:
    """
    Domínio de estoque: controle físico e lógico de mercadorias.
    Separado do catálogo (ProductService) porque suas responsabilidades
    são distintas — produto é dado estático; estoque muda a cada venda.

    Chamado de forma síncrona pelo OrderService porque a reserva deve
    ser confirmada ANTES de criar o pedido (evita vender item indisponível).
    """

    def __init__(self, db: Session):
        self.repo = InventoryRepository(db)

    def reserve(self, product_id: int, quantidade: int) -> None:
        """
        Reserva itens. Lança EstoqueInsuficiente se não houver saldo.
        A reserva é confirmada (baixa definitiva) após pagamento aprovado.
        """
        inv = self.repo.get_by_product(product_id)
        disponivel = inv.quantidade if inv else 0

        if disponivel < quantidade:
            raise EstoqueInsuficiente(product_id, disponivel, quantidade)

        inv.quantidade -= quantidade
        self.repo.save(inv)
        logger.info(f"[Inventory] Reserva: produto={product_id}, qtd={quantidade}, saldo_restante={inv.quantidade}")

    def release(self, product_id: int, quantidade: int) -> None:
        """
        Estorna a reserva em caso de cancelamento do pedido.
        Chamado via evento order.cancelled para manter consistência.
        """
        inv = self.repo.get_by_product(product_id)
        if inv:
            inv.quantidade += quantidade
            self.repo.save(inv)
            logger.info(f"[Inventory] Estorno: produto={product_id}, qtd={quantidade}")

    def get_stock(self, product_id: int) -> int:
        inv = self.repo.get_by_product(product_id)
        return inv.quantidade if inv else 0
