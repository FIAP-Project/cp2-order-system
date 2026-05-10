from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from .repository import ClientRepository
from .schemas import ClientOut

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=list[ClientOut], summary="Lista clientes")
def list_clients(db: Session = Depends(get_db)):
    return ClientRepository(db).get_all()
