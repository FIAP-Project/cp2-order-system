from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from .service import ProductService
from .schemas import ProductOut

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductOut], summary="Lista todos os produtos")
def list_products(db: Session = Depends(get_db)):
    return ProductService(db).get_all()


@router.get("/{product_id}", response_model=ProductOut, summary="Consulta produto por ID")
def get_product(product_id: int, db: Session = Depends(get_db)):
    return ProductService(db).get_product(product_id)
