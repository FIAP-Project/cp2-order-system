from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database import get_db
from .service import OrderService
from .schemas import OrderIn, OrderOut, OrderUpdateIn, StatusUpdateIn

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED,
             summary="Cria um novo pedido e dispara fluxo de pagamento")
def create_order(data: OrderIn, db: Session = Depends(get_db)):
    return OrderService(db).create_order(data)


@router.get("/", response_model=list[OrderOut], summary="Lista todos os pedidos")
def list_orders(db: Session = Depends(get_db)):
    return OrderService(db).get_all()


@router.get("/{order_id}", response_model=OrderOut, summary="Consulta pedido por ID")
def get_order(order_id: int, db: Session = Depends(get_db)):
    return OrderService(db).get_order(order_id)


@router.put("/{order_id}", response_model=OrderOut,
            summary="Atualiza dados do pedido (somente enquanto não processado)")
def update_order(order_id: int, data: OrderUpdateIn, db: Session = Depends(get_db)):
    return OrderService(db).update_order(order_id, data)


@router.patch("/{order_id}/status", response_model=OrderOut,
              summary="Atualiza status do pedido (PAGO → FINALIZADO)")
def update_status(order_id: int, body: StatusUpdateIn, db: Session = Depends(get_db)):
    return OrderService(db).update_status(order_id, body.status)


@router.delete("/{order_id}", response_model=OrderOut, status_code=status.HTTP_200_OK,
               summary="Cancela pedido e estorna estoque (somente antes do pagamento)")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    return OrderService(db).cancel_order(order_id)
