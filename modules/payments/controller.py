from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from .repository import PaymentRepository
from .service import payment_service
from .circuit_breaker import circuit_breaker
from .schemas import PaymentOut, CircuitBreakerStatus

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/circuit-breaker", response_model=CircuitBreakerStatus,
            summary="Exibe estado atual do circuit breaker do gateway")
def get_circuit_breaker_status():
    s = circuit_breaker.status_dict()
    return CircuitBreakerStatus(**s)


@router.get("/{order_id}", response_model=PaymentOut,
            summary="Consulta pagamento de um pedido")
def get_payment(order_id: int, db: Session = Depends(get_db)):
    payment = PaymentRepository(db).get_by_order(order_id)
    if not payment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return payment


@router.post("/retry/{order_id}", summary="Retry manual de pagamento pendente")
def retry_payment(order_id: int):
    return payment_service.retry_pending(order_id)
