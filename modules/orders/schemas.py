from pydantic import BaseModel, field_validator
from decimal import Decimal
from typing import Optional
from datetime import datetime


class OrderItemIn(BaseModel):
    produto_id: int
    quantidade: int

    @field_validator("quantidade")
    @classmethod
    def quantidade_positiva(cls, v):
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v


class OrderIn(BaseModel):
    cliente_id: int
    itens: list[OrderItemIn]
    forma_pagamento: Optional[str] = "CARTAO_CREDITO"

    @field_validator("itens")
    @classmethod
    def itens_nao_vazios(cls, v):
        if not v:
            raise ValueError("O pedido deve conter pelo menos um item")
        return v


class StatusUpdateIn(BaseModel):
    status: str


class OrderItemOut(BaseModel):
    id: int
    produto_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    cliente_id: int
    valor_total: Decimal
    status: str
    data_criacao: Optional[datetime] = None
    itens: list[OrderItemOut] = []

    model_config = {"from_attributes": True}


class OrderUpdateIn(BaseModel):
    forma_pagamento: Optional[str] = None

