from pydantic import BaseModel


class InventoryOut(BaseModel):
    produto_id: int
    quantidade: int

    model_config = {"from_attributes": True}
