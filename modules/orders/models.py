from sqlalchemy import Column, BigInteger, Numeric, String, TIMESTAMP, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Order(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    valor_total = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False, default="CRIADO")
    data_criacao = Column(TIMESTAMP, server_default=func.now())

    itens = relationship("OrderItem", back_populates="pedido", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "pedido_itens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(BigInteger, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(BigInteger, nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    pedido = relationship("Order", back_populates="itens")
