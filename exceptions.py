"""
Exceções de domínio.
Mantidas aqui para que os handlers HTTP do FastAPI possam capturá-las
em um único lugar, separando regra de negócio de resposta HTTP.
"""

from fastapi import HTTPException


class ProdutoNaoEncontrado(HTTPException):
    def __init__(self, produto_id: int):
        super().__init__(status_code=404, detail=f"Produto {produto_id} não encontrado")


class EstoqueInsuficiente(HTTPException):
    def __init__(self, produto_id: int, disponivel: int, solicitado: int):
        super().__init__(
            status_code=409,
            detail=(
                f"Estoque insuficiente para produto {produto_id}: "
                f"disponível={disponivel}, solicitado={solicitado}"
            ),
        )


class PedidoNaoEncontrado(HTTPException):
    def __init__(self, pedido_id: int):
        super().__init__(status_code=404, detail=f"Pedido {pedido_id} não encontrado")


class PedidoSemItens(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="O pedido deve conter pelo menos um item")


class TransicaoDeStatusInvalida(HTTPException):
    def __init__(self, atual: str, destino: str):
        super().__init__(
            status_code=400,
            detail=f"Transição de status inválida: '{atual}' → '{destino}'",
        )


class PagamentoRecusado(HTTPException):
    def __init__(self, motivo: str = "Gateway recusou a transação"):
        super().__init__(status_code=402, detail=motivo)


class ClienteNaoEncontrado(HTTPException):
    def __init__(self, cliente_id: int):
        super().__init__(status_code=404, detail=f"Cliente {cliente_id} não encontrado")
