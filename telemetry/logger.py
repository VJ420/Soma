"""
Structured Observability, Telemetry & Logging Subsystem.
Zero print() statements for production operational telemetry. High performance, non-blocking queue logging.
"""
import sys
import time
import json
import threading
import queue
from typing import Any, Dict, Optional
from config.settings import LogLevel, TelemetryConfig

class MetricsCollector:
    __slots__ = ("_counters", "_gauges", "_timings", "_lock")

    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._timings: Dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def increment(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def record_timing(self, name: str, duration_ms: float) -> None:
        with self._lock:
            if name not in self._timings:
                self._timings[name] = []
            self._timings[name].append(duration_ms)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timings": {
                    k: {
                        "count": len(v),
                        "avg_ms": sum(v) / len(v) if v else 0.0,
                        "min_ms": min(v) if v else 0.0,
                        "max_ms": max(v) if v else 0.0,
                    } for k, v in self._timings.items()
                }
            }

class TelemetryLogger:
    __slots__ = ("_config", "_queue", "_worker_thread", "_running", "_metrics")

    def __init__(self, config: TelemetryConfig, metrics: MetricsCollector):
        self._config = config
        self._metrics = metrics
        self._queue: queue.Queue[Optional[Dict[str, Any]]] = queue.Queue(maxsize=10000)
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_logs, daemon=True, name="TelemetryWorker")
        self._worker_thread.start()

    def _process_logs(self) -> None:
        while self._running:
            try:
                record = self._queue.get(timeout=0.1)
                if record is None:
                    break
                if self._config.structured_json:
                    sys.stderr.write(json.dumps(record) + "\n")
                else:
                    ts = record.get("timestamp", "")
                    lvl = record.get("level", "")
                    msg = record.get("message", "")
                    sys.stderr.write(f"[{ts}] [{lvl}] {msg}\n")
                sys.stderr.flush()
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

    def log(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        record = {
            "timestamp": time.time(),
            "level": level.value,
            "message": message,
            "context": context or {}
        }
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            self._metrics.increment("telemetry_logs_dropped")

    def debug(self, msg: str, **ctx: Any) -> None:
        self.log(LogLevel.DEBUG, msg, ctx)

    def info(self, msg: str, **ctx: Any) -> None:
        self.log(LogLevel.INFO, msg, ctx)

    def warning(self, msg: str, **ctx: Any) -> None:
        self.log(LogLevel.WARNING, msg, ctx)

    def error(self, msg: str, **ctx: Any) -> None:
        self.log(LogLevel.ERROR, msg, ctx)

    def shutdown(self) -> None:
        self._running = False
        try:
            self._queue.put_nowait(None)
            self._worker_thread.join(timeout=1.0)
        except Exception:
            pass
