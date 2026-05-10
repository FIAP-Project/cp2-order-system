from pydantic import BaseModel


class ClientOut(BaseModel):
    id: int
    nome: str
    email: str

    model_config = {"from_attributes": True}
