from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from .service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/{product_id}", summary="Consulta saldo em estoque de um produto")
def get_stock(product_id: int, db: Session = Depends(get_db)):
    qty = InventoryService(db).get_stock(product_id)
    return {"produto_id": product_id, "quantidade": qty}
