from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class MetricsCollector:
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    timings: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    gauges: dict[str, float] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def increment(self, name: str, value: int = 1, **labels: Any) -> None:
        key = _metric_key(name, labels)
        with self._lock:
            self.counters[key] += value

    def observe_ms(self, name: str, value: float, **labels: Any) -> None:
        key = _metric_key(name, labels)
        with self._lock:
            self.timings[key].append(value)

    def set_gauge(self, name: str, value: float, **labels: Any) -> None:
        key = _metric_key(name, labels)
        with self._lock:
            self.gauges[key] = value

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            timings = {
                key: {
                    "count": len(values),
                    "avg_ms": round(sum(values) / len(values), 2) if values else 0,
                    "max_ms": round(max(values), 2) if values else 0,
                }
                for key, values in self.timings.items()
            }
            return {
                "counters": dict(self.counters),
                "timings": timings,
                "gauges": dict(self.gauges),
            }


metrics = MetricsCollector()


def _metric_key(name: str, labels: dict[str, Any]) -> str:
    if not labels:
        return name
    label_text = ",".join(f"{key}={value}" for key, value in sorted(labels.items()))
    return f"{name}{{{label_text}}}"
