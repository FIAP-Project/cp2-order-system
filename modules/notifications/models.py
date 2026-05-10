from sqlalchemy import Column, BigInteger, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from database import Base


class Notification(Base):
    __tablename__ = "notificacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(BigInteger, ForeignKey("pedidos.id"), nullable=False)
    tipo = Column(String(100), nullable=False)
    mensagem = Column(String(255), nullable=False)
    data_envio = Column(TIMESTAMP, server_default=func.now())
