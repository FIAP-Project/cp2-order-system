"""
Seed de dados iniciais conforme especificado no CP2.
Executado automaticamente na inicialização da aplicação se o BD estiver vazio.
"""

import logging
from sqlalchemy.orm import Session
from modules.clients.models import Client
from modules.products.models import Product
from modules.inventory.models import Inventory

logger = logging.getLogger("seed")


def run_seed(db: Session) -> None:
    if db.query(Client).count() > 0:
        return  # já foi populado

    logger.info("[Seed] Populando banco de dados...")

    clientes = [
        Client(nome="Ana Souza", email="ana@email.com"),
        Client(nome="Bruno Lima", email="bruno@email.com"),
        Client(nome="Carla Mendes", email="carla@email.com"),
    ]
    db.add_all(clientes)
    db.flush()

    produtos = [
        Product(nome="Hambúrguer Artesanal",  descricao="Pão, carne, queijo e molho especial", preco=32.90),
        Product(nome="Pizza Calabresa",        descricao="Pizza média de calabresa",             preco=49.90),
        Product(nome="Refrigerante 2L",        descricao="Refrigerante cola 2 litros",           preco=12.00),
        Product(nome="Batata Frita",           descricao="Porção média de batata frita",         preco=18.50),
    ]
    db.add_all(produtos)
    db.flush()

    estoques = [
        Inventory(produto_id=produtos[0].id, quantidade=10),
        Inventory(produto_id=produtos[1].id, quantidade=5),
        Inventory(produto_id=produtos[2].id, quantidade=20),
        Inventory(produto_id=produtos[3].id, quantidade=8),
    ]
    db.add_all(estoques)
    db.commit()

    logger.info("[Seed] Dados inseridos: 3 clientes, 4 produtos, 4 registros de estoque")
