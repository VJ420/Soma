"""
Configuration subsystem for Fractal Language System.
Zero magic numbers; strictly typed, validated, and externalized runtime configuration.
"""
from dataclasses import dataclass, field
from enum import Enum
import os

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ExecutionMode(Enum):
    INTERPRETER = "INTERPRETER"
    BYTECODE_VM = "BYTECODE_VM"
    JIT = "JIT"
    AOT_NATIVE = "AOT_NATIVE"

@dataclass(slots=True, frozen=True)
class RuntimeConfig:
    max_recursion_depth: int = 1000
    max_call_stack_frames: int = 10000
    execution_timeout_sec: float = 30.0
    memory_limit_bytes: int = 512 * 1024 * 1024  # 512MB resource budget
    max_channel_buffer_capacity: int = 4096

@dataclass(slots=True, frozen=True)
class ConcurrencyConfig:
    max_worker_threads: int = 16
    max_agent_fibers: int = 1024
    task_queue_bound: int = 8192
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout_sec: float = 10.0

@dataclass(slots=True, frozen=True)
class TelemetryConfig:
    log_level: LogLevel = LogLevel.INFO
    structured_json: bool = True
    metrics_collection_enabled: bool = True
    trace_sample_rate: float = 1.0

@dataclass(slots=True, frozen=True)
class SystemConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    concurrency: ConcurrencyConfig = field(default_factory=ConcurrencyConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    mode: ExecutionMode = ExecutionMode.INTERPRETER

    @classmethod
    def load_from_env(cls) -> 'SystemConfig':
        log_level_str = os.getenv("FRACTAL_LOG_LEVEL", "INFO").upper()
        log_level = getattr(LogLevel, log_level_str, LogLevel.INFO)
        
        mode_str = os.getenv("FRACTAL_EXEC_MODE", "INTERPRETER").upper()
        mode = getattr(ExecutionMode, mode_str, ExecutionMode.INTERPRETER)

        return cls(
            runtime=RuntimeConfig(
                max_recursion_depth=int(os.getenv("FRACTAL_MAX_RECURSION", "1000")),
                max_call_stack_frames=int(os.getenv("FRACTAL_MAX_FRAMES", "10000")),
                execution_timeout_sec=float(os.getenv("FRACTAL_TIMEOUT_SEC", "30.0")),
                memory_limit_bytes=int(os.getenv("FRACTAL_MEM_LIMIT", str(512 * 1024 * 1024))),
                max_channel_buffer_capacity=int(os.getenv("FRACTAL_CHANNEL_BOUND", "4096"))
            ),
            concurrency=ConcurrencyConfig(
                max_worker_threads=int(os.getenv("FRACTAL_WORKERS", "16")),
                max_agent_fibers=int(os.getenv("FRACTAL_MAX_FIBERS", "1024")),
                task_queue_bound=int(os.getenv("FRACTAL_QUEUE_BOUND", "8192")),
                circuit_breaker_failure_threshold=int(os.getenv("FRACTAL_CB_FAILURES", "5")),
                circuit_breaker_recovery_timeout_sec=float(os.getenv("FRACTAL_CB_TIMEOUT", "10.0"))
            ),
            telemetry=TelemetryConfig(
                log_level=log_level,
                structured_json=os.getenv("FRACTAL_STRUCTURED_LOGS", "true").lower() == "true",
                metrics_collection_enabled=True,
                trace_sample_rate=float(os.getenv("FRACTAL_TRACE_SAMPLE_RATE", "1.0"))
            ),
            mode=mode
        )
