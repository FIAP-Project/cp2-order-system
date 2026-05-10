from sqlalchemy.orm import Session
from exceptions import ProdutoNaoEncontrado
from .repository import ProductRepository
from .models import Product


class ProductService:
    """
    Responsável pelo domínio de catálogo.
    Regra de negócio: produto deve existir antes de ser vendido.
    Chamado de forma síncrona pelo OrderService — resposta necessária
    antes de prosseguir com a criação do pedido.
    """

    def __init__(self, db: Session):
        self.repo = ProductRepository(db)

    def get_product(self, product_id: int) -> Product:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise ProdutoNaoEncontrado(product_id)
        return product

    def get_all(self) -> list[Product]:
        return self.repo.get_all()
