from sqlalchemy.orm import Session
from .models import Payment


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_by_order(self, pedido_id: int) -> Payment | None:
        return (
            self.db.query(Payment)
            .filter(Payment.pedido_id == pedido_id)
            .order_by(Payment.id.desc())
            .first()
        )

    def save(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
