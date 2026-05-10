from sqlalchemy.orm import Session
from .models import Inventory


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_product(self, product_id: int) -> Inventory | None:
        return self.db.query(Inventory).filter(Inventory.produto_id == product_id).first()

    def save(self, inventory: Inventory) -> Inventory:
        self.db.add(inventory)
        self.db.commit()
        self.db.refresh(inventory)
        return inventory
