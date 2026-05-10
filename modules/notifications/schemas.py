from pydantic import BaseModel
from datetime import datetime


class NotificationOut(BaseModel):
    id: int
    pedido_id: int
    tipo: str
    mensagem: str
    data_envio: datetime | None = None

    model_config = {"from_attributes": True}
