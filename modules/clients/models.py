from sqlalchemy import Column, BigInteger, Integer, String
from database import Base


class Client(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False)
