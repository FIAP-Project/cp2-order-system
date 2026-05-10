"""
Circuit Breaker — padrão de resiliência para chamadas ao gateway de pagamento.

Estados:
  CLOSED    → operação normal; falhas são contadas
  OPEN      → gateway indisponível; chamadas bloqueadas para não sobrecarregar
  HALF_OPEN → período de teste após timeout; uma chamada de prova é permitida

Fluxo quando OPEN:
  O pedido é registrado com status AGUARDANDO_PAGAMENTO.
  Em produção, um worker faria retry via fila (ex: Celery + Redis).
  Aqui expõe-se POST /payments/retry/{order_id} para demonstrar o conceito.
"""

import time
import logging

logger = logging.getLogger("circuit_breaker")


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self._state = "CLOSED"

    @property
    def state(self) -> str:
        if self._state == "OPEN" and self.last_failure_time:
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                logger.info("[CircuitBreaker] Transição OPEN → HALF_OPEN (timeout expirado)")
                self._state = "HALF_OPEN"
        return self._state

    def is_open(self) -> bool:
        return self.state == "OPEN"

    def record_success(self) -> None:
        if self._state == "HALF_OPEN":
            logger.info("[CircuitBreaker] Chamada de prova OK — HALF_OPEN → CLOSED")
        self._state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            if self._state != "OPEN":
                logger.warning(
                    f"[CircuitBreaker] {self.failure_count} falhas — CLOSED → OPEN"
                )
            self._state = "OPEN"

    def status_dict(self) -> dict:
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "description": {
                "CLOSED": "Gateway operacional",
                "OPEN": "Gateway indisponível — pedidos em AGUARDANDO_PAGAMENTO",
                "HALF_OPEN": "Testando recuperação do gateway",
            }.get(self.state, ""),
        }


# Singleton — compartilhado pela aplicação inteira
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
