from sqlalchemy.orm import Session
from .models import Product


class ProductRepository:
    """Responsabilidade única: persistência de produtos. Sem lógica de negócio."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id: int) -> Product | None:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_all(self) -> list[Product]:
        return self.db.query(Product).all()
