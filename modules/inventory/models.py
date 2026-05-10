from sqlalchemy import Column, BigInteger, Integer, ForeignKey
from database import Base


class Inventory(Base):
    __tablename__ = "estoque"

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(BigInteger, ForeignKey("produtos.id"), nullable=False, unique=True)
    quantidade = Column(Integer, nullable=False, default=0)
