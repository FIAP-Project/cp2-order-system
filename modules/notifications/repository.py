from sqlalchemy.orm import Session
from .models import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_by_order(self, pedido_id: int) -> list[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.pedido_id == pedido_id)
            .all()
        )

    def get_all(self) -> list[Notification]:
        return self.db.query(Notification).order_by(Notification.id.desc()).all()
