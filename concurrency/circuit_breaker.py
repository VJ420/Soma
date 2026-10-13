"""
Enterprise Concurrency & Fault Tolerance Subsystem.
Implements Circuit Breaker, Bounded Thread Pools, and Fiber Task Scheduling.
"""
import time
import threading
from enum import Enum
from typing import Any, Callable, Optional, TypeVar
from config.settings import ConcurrencyConfig
from telemetry.logger import TelemetryLogger, MetricsCollector

T = TypeVar("T")

class CircuitState(Enum):
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # Failing, reject requests
    HALF_OPEN = "HALF_OPEN" # Testing recovery

class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted while the circuit breaker is OPEN."""
    pass

class CircuitBreaker:
    __slots__ = (
        "_name", "_failure_threshold", "_recovery_timeout",
        "_state", "_failure_count", "_last_failure_time",
        "_lock", "_logger", "_metrics"
    )

    def __init__(
        self,
        name: str,
        config: ConcurrencyConfig,
        logger: TelemetryLogger,
        metrics: MetricsCollector
    ):
        self._name = name
        self._failure_threshold = config.circuit_breaker_failure_threshold
        self._recovery_timeout = config.circuit_breaker_recovery_timeout_sec
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()
        self._logger = logger
        self._metrics = metrics

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._state

    def execute(self, action: Callable[[], T]) -> T:
        with self._lock:
            now = time.time()
            if self._state == CircuitState.OPEN:
                if now - self._last_failure_time > self._recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._logger.info(f"Circuit '{self._name}' transitioning to HALF_OPEN")
                else:
                    self._metrics.increment(f"circuit_{self._name}_rejected")
                    raise CircuitBreakerOpenException(f"CircuitBreaker '{self._name}' is OPEN. Request rejected.")

        try:
            result = action()
            with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._logger.info(f"Circuit '{self._name}' recovered to CLOSED")
            return result
        except Exception as ex:
            with self._lock:
                self._failure_count += 1
                self._last_failure_time = time.time()
                self._metrics.increment(f"circuit_{self._name}_failure")
                if self._failure_count >= self._failure_threshold:
                    self._state = CircuitState.OPEN
                    self._logger.error(
                        f"Circuit '{self._name}' tripped to OPEN. Failures: {self._failure_count}",
                        error=str(ex)
                    )
            raise ex
