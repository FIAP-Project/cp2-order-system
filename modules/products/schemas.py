from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class ProductOut(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    preco: Decimal

    model_config = {"from_attributes": True}
