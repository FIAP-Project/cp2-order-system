from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from .repository import NotificationRepository
from .schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[NotificationOut],
            summary="Lista todos os eventos de notificação registrados")
def list_notifications(db: Session = Depends(get_db)):
    return NotificationRepository(db).get_all()


@router.get("/order/{order_id}", response_model=list[NotificationOut],
            summary="Lista notificações de um pedido específico")
def get_notifications_by_order(order_id: int, db: Session = Depends(get_db)):
    return NotificationRepository(db).get_by_order(order_id)
