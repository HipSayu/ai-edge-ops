"""Node-health early warning on the Edge: live telemetry → model window → risk → alarm → Cloud (via outbox)."""

import logging
import time
from collections.abc import Callable
from datetime import datetime, timedelta

from pydantic import BaseModel

from src.edge.application.ports.edge_publisher import EdgePublisher
from src.edge.application.ports.health_predictor import HealthPredictor
from src.edge.application.ports.health_store import HealthStore
from src.ml.node_health import AlarmTracker, AlarmTransition, FeatureWindow
from src.shared.contracts import (
    GpuTelemetry,
    HealthAlarmEvent,
    HealthPrediction,
    RuntimeTelemetry,
    Severity,
    SystemTelemetry,
    TelemetryKind,
)
from src.shared.contracts.health import ALARM_CLEARED, ALARM_RAISED
from src.shared.contracts.topics import EventKind
from src.shared.domain.clock import Clock

logger = logging.getLogger(__name__)

_TELEMETRY, _EVENT = "telemetry", "event"


class HealthService:
    """Fed by TelemetryReportService (`observe`), scored on a timer (`tick`).

    Connectivity features are Edge-side proxies of what the model was trained on:
    `heartbeat_age_sec` = seconds since telemetry last left while the broker was connected,
    `connection_reconnect_count` = broker disconnects seen by this agent.
    """

    def __init__(
        self,
        node_id: str,
        predictor: HealthPredictor,
        store: HealthStore,
        publisher: EdgePublisher,
        is_connected: Callable[[], bool],
        runtime_stale_sec: float = 30.0,
        retention: timedelta = timedelta(days=7),
        max_rows: int = 200_000,
        flush_batch: int = 200,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._node_id = node_id
        self._predictor = predictor
        self._store = store
        self._publisher = publisher
        self._is_connected = is_connected
        self._runtime_stale = timedelta(seconds=runtime_stale_sec)
        self._retention = retention
        self._max_rows = max_rows
        self._flush_batch = flush_batch
        self._mono = monotonic
        self._window = FeatureWindow(predictor.features, predictor.window, predictor.counters)
        self._alarm = AlarmTracker(predictor.threshold, raise_after=predictor.alarm_consecutive)
        self._alarm_started: datetime | None = None
        self._system: SystemTelemetry | None = None
        self._gpu: GpuTelemetry | None = None
        self._runtimes: dict[str, RuntimeTelemetry] = {}
        self._last_ok = monotonic()
        self._was_connected = True
        self._disconnects = 0
        self._ticks = 0

    # --- input -------------------------------------------------------------------------------------------
    def observe(self, kind: str, sample: BaseModel) -> None:
        if isinstance(sample, SystemTelemetry):
            self._system = sample
        elif isinstance(sample, GpuTelemetry):
            self._gpu = sample
        elif isinstance(sample, RuntimeTelemetry):
            self._runtimes[sample.runtime_id] = sample
        if kind == TelemetryKind.SYSTEM and self._is_connected():
            self._last_ok = self._mono()

    def feature_row(self) -> dict[str, float | None]:
        s, g, now = self._system, self._gpu, Clock.now()
        runtimes = [r for r in self._runtimes.values() if now - r.timestamp <= self._runtime_stale]
        fps = [r.inference_fps for r in runtimes if r.inference_fps is not None]
        latency = [r.inference_latency_ms for r in runtimes if r.inference_latency_ms is not None]
        row: dict[str, float | None] = {
            "heartbeat_age_sec": self._mono() - self._last_ok,
            "connection_reconnect_count": self._disconnects,
            "cpu_usage_pct": s.cpu_usage_pct if s else None,
            "memory_usage_pct": s.memory_usage_pct if s else None,
            "disk_usage_pct": s.disk_usage_pct if s else None,
            "gpu_usage_pct": g.gpu_usage_pct if g else None,
            "gpu_temperature_c": g.gpu_temperature_c if g else None,
            # a node is as healthy as its worst runtime
            "inference_fps": min(fps) if fps else None,
            "inference_latency_ms": max(latency) if latency else None,
            "runtime_restart_count": sum(r.runtime_restart_count or 0 for r in runtimes) if runtimes else None,
            "runtime_error_count": sum(self._error_count(r) for r in runtimes) if runtimes else None,
        }
        return {k: row.get(k) for k in self._predictor.features}

    @staticmethod
    def _error_count(r: RuntimeTelemetry) -> float:
        if r.runtime_error_count is not None:
            return r.runtime_error_count
        if r.runtime_error_rate is not None and r.inference_fps is not None:  # runtimes that only report a rate
            return r.runtime_error_rate / 100 * r.inference_fps * 5
        return 0.0

    # --- scoring -----------------------------------------------------------------------------------------
    async def tick(self) -> HealthPrediction | None:
        connected = self._is_connected()
        if self._was_connected and not connected:
            self._disconnects += 1
        self._was_connected = connected

        row = self.feature_row()
        self._window.push(row)
        if not self._window.ready:
            return None
        now = Clock.now()
        risk = self._predictor.score(self._window.matrix())
        transition = self._alarm.update(risk)
        prediction = HealthPrediction(
            node_id=self._node_id, timestamp=now, risk=round(risk, 5), alarm=self._alarm.active,
            threshold=self._predictor.threshold, horizon_sec=self._predictor.horizon_sec,
            model_version=self._predictor.version, features=row,
        )
        self._store.enqueue(_TELEMETRY, TelemetryKind.HEALTH, prediction.model_dump_json(), now)
        if transition is not None:
            self._on_transition(transition, risk, now)

        self._ticks += 1
        if self._ticks % 720 == 0:  # hourly at 5 s
            self._store.prune(now - self._retention, self._max_rows)
        await self.flush()
        return prediction

    def _on_transition(self, transition: AlarmTransition, risk: float, now: datetime) -> None:
        if transition == AlarmTransition.RAISED:
            self._alarm_started = now
            self._store.save_alarm_window(now, risk, self._window.matrix())
        started = self._alarm_started or now
        raised = transition == AlarmTransition.RAISED
        event = HealthAlarmEvent(
            node_id=self._node_id, timestamp=now,
            severity=Severity.WARNING if raised else Severity.INFO,
            event_type=ALARM_RAISED if raised else ALARM_CLEARED,
            message=(f"Degradation likely within {self._predictor.horizon_sec / 60:.0f} min (risk {risk:.2f})"
                     if raised else f"Degradation risk cleared (peak {self._alarm.peak:.2f})"),
            alarm_started_at=started, risk=risk, peak_risk=self._alarm.peak,
            model_version=self._predictor.version,
        )
        self._store.enqueue(_EVENT, EventKind.HEALTH, event.model_dump_json(), now)
        if raised:
            logger.warning("%s", event.message)
        else:
            logger.info("%s", event.message)
            self._alarm_started = None

    # --- delivery ----------------------------------------------------------------------------------------
    async def flush(self) -> int:
        """Send the outbox oldest-first; stops at the first failure so ordering is preserved."""
        if not self._is_connected():
            return 0
        sent: list[int] = []
        try:
            for msg_id, channel, kind, payload in self._store.pending(self._flush_batch):
                if channel == _EVENT:
                    await self._publisher.event(kind, HealthAlarmEvent.model_validate_json(payload))
                else:
                    await self._publisher.telemetry(kind, HealthPrediction.model_validate_json(payload))
                sent.append(msg_id)
        except Exception as exc:  # broker dropped mid-flush: keep the rest for the next tick
            logger.debug("Health outbox flush interrupted: %s", exc)
        finally:
            if sent:
                self._store.mark_sent(sent)
        return len(sent)
