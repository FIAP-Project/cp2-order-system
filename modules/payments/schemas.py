from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import datetime


class PaymentOut(BaseModel):
    id: int
    pedido_id: int
    valor: Decimal
    status: str
    forma_pagamento: Optional[str] = None
    tentativas: int
    data_pagamento: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CircuitBreakerStatus(BaseModel):
    state: str
    failure_count: int
    failure_threshold: int
    description: str
