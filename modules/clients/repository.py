from sqlalchemy.orm import Session
from .models import Client


class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, client_id: int) -> Client | None:
        return self.db.query(Client).filter(Client.id == client_id).first()

    def get_all(self) -> list[Client]:
        return self.db.query(Client).all()
