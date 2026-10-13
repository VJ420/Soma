"""
Dependency Injection Container and Runtime Context Factory.
Central IoC orchestrator for the Fractal Production Platform.
"""
from config.settings import SystemConfig
from telemetry.logger import TelemetryLogger, MetricsCollector
from concurrency.circuit_breaker import CircuitBreaker
from runtime_engine.enterprise_interpreter import EnterpriseInterpreterStrategy

class FractalContainer:
    __slots__ = ("config", "metrics", "logger", "circuit_breaker", "interpreter")

    def __init__(self, config: SystemConfig):
        self.config = config
        self.metrics = MetricsCollector()
        self.logger = TelemetryLogger(config.telemetry, self.metrics)
        self.circuit_breaker = CircuitBreaker(
            name="core_interpreter_circuit",
            config=config.concurrency,
            logger=self.logger,
            metrics=self.metrics
        )
        self.interpreter = EnterpriseInterpreterStrategy(
            config=self.config,
            logger=self.logger,
            metrics=self.metrics,
            circuit_breaker=self.circuit_breaker
        )

    def shutdown(self) -> None:
        self.logger.shutdown()

    @classmethod
    def create_default(cls) -> 'FractalContainer':
        config = SystemConfig.load_from_env()
        return cls(config)
