from sqlalchemy import Column, BigInteger, Integer, Numeric, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from database import Base


class Payment(Base):
    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(BigInteger, ForeignKey("pedidos.id"), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False, default="PENDENTE")
    forma_pagamento = Column(String(50), nullable=True)
    tentativas = Column(BigInteger, nullable=False, default=0)
    data_pagamento = Column(TIMESTAMP, nullable=True)
    criado_em = Column(TIMESTAMP, server_default=func.now())
