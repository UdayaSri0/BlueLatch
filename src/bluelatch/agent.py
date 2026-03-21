from __future__ import annotations

import logging
import subprocess
import sys
import threading
from datetime import datetime, timedelta, timezone

from bluelatch.bluetooth.bluez import BluezClient
from bluelatch.bluetooth.reconnect import ReconnectBackoff, ReconnectController
from bluelatch.config.manager import ConfigManager
from bluelatch.config.models import AppConfig
from bluelatch.models import EventRecord, LockMethod, ProtectionState, StatusSnapshot
from bluelatch.presence import PresenceEstimator, ProtectionStateMachine
from bluelatch.runtime import RuntimeStore
from bluelatch.session import LockManager, SessionMonitor
from bluelatch.updates import UpdateService
from bluelatch.util.logging import configure_logging
from bluelatch.util.notify import send_notification
from bluelatch.util.single_instance import SingleInstanceLock
from bluelatch.util.xdg import AppPaths
from bluelatch.version import __version__

try:
    from gi.repository import GLib
except ImportError as exc:  # pragma: no cover - integration-only import
    raise RuntimeError(
        "PyGObject is required to run the BlueLatch background agent",
    ) from exc


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BlueLatchAgent:
    def __init__(self) -> None:
        self.paths = AppPaths()
        self.paths.ensure()
        self.config_manager = ConfigManager(paths=self.paths)
        self.config = self.config_manager.load()
        self.logger = configure_logging(
            debug=self.config.logging.debug_enabled,
            paths=self.paths,
        )
        self.runtime = RuntimeStore(self.paths)
        self.history = self.runtime.load_events(limit=1)
        self.status = self.runtime.load_status()
        self.instance_lock = SingleInstanceLock(self.paths.agent_lock_file)
        self.bluez = BluezClient(self.logger)
        self.session_monitor = SessionMonitor(self.logger)
        self.lock_manager = LockManager(self.logger)
        self.update_service = UpdateService()
        self.presence_estimator = PresenceEstimator(self.config.protection)
        self.state_machine = ProtectionStateMachine(self.config.protection)
        self.reconnect_controller = ReconnectController(
            backoff=ReconnectBackoff(
                initial_seconds=self.config.bluetooth.reconnect_initial_seconds,
                max_seconds=self.config.bluetooth.reconnect_max_seconds,
                jitter_ratio=self.config.bluetooth.reconnect_jitter_ratio,
            ),
        )
        self._main_loop: GLib.MainLoop | None = None
        self._next_lock_retry_at: datetime | None = None
        self._previous_state = self.status.current_state
        if self.status.manual_override_active:
            self.state_machine.restore_manual_override(now=utc_now())

    def run(self) -> int:
        if not self.instance_lock.acquire():
            self.logger.info("Another BlueLatch agent instance is already running")
            return 0

        self.logger.info("Starting BlueLatch agent")
        self._record_event("INFO", "agent.start", "BlueLatch agent started")
        self.bluez.start()
        self.bluez.on_device_change(self._on_bluetooth_change)
        self.bluez.on_adapter_change(self._on_adapter_change)
        self.session_monitor.on_state_change(self._on_session_lock_change)
        self.session_monitor.on_resume(self._on_resume)
        self.session_monitor.start()
        self._refresh_status(force=True)
        self._schedule_update_check()

        GLib.timeout_add_seconds(1, self._tick)
        GLib.timeout_add_seconds(2, self._reload_config_if_needed)
        self._main_loop = GLib.MainLoop()
        try:
            self._main_loop.run()
        finally:
            self.instance_lock.release()
        return 0

    def stop(self) -> None:
        if self._main_loop:
            self._main_loop.quit()

    def _tick(self) -> bool:
        try:
            self._refresh_status()
        except Exception:
            self.logger.exception("Agent tick failed")
            self._record_event("ERROR", "agent.tick_failed", "Agent tick failed")
        return True

    def _refresh_status(self, *, force: bool = False) -> None:
        now = utc_now()
        self.bluez.maybe_refresh()
        device = self.bluez.resolve_trusted_device(self.config.bluetooth.trusted_device)
        bluetooth_available = self.bluez.available
        adapter_powered = self.bluez.adapter.powered
        connected = bool(device and device.connected)
        rssi = device.rssi if device else None

        if connected:
            self.reconnect_controller.mark_success()
        elif self._should_attempt_reconnect(now, device=device):
            self._attempt_reconnect(now, device=device)

        assessment = self.presence_estimator.update(
            connected=connected,
            rssi=rssi,
            observed_at=now,
        )
        previous_state = self.state_machine.state
        decision = self.state_machine.advance(
            assessment=assessment,
            session_locked=self.session_monitor.is_locked,
        )

        if (
            self.config.protection.enabled
            and decision.should_lock
            and (self._next_lock_retry_at is None or now >= self._next_lock_retry_at)
        ):
            self._attempt_lock(now)
            decision = self.state_machine._decision(assessment.reason)

        if previous_state != self.state_machine.state or force:
            self._record_state_change(previous_state, self.state_machine.state)

        self.status = StatusSnapshot(
            current_state=self.state_machine.state,
            trusted_device=self.config.bluetooth.trusted_device,
            protection_enabled=self.config.protection.enabled,
            bluetooth_available=bluetooth_available,
            adapter_powered=adapter_powered,
            connection_state="connected" if connected else "disconnected",
            proximity_summary=assessment.reason,
            session_locked=self.session_monitor.is_locked,
            manual_override_active=self.state_machine.manual_override_active,
            last_lock_reason=self.state_machine.last_lock_reason,
            last_seen_at=now.isoformat() if connected else self.status.last_seen_at,
            away_since=self.state_machine.away_since.isoformat() if self.state_machine.away_since else None,
            last_state_change_at=(
                self.state_machine.last_state_change_at.isoformat()
                if self.state_machine.last_state_change_at
                else None
            ),
            reconnect_state=self._reconnect_status(now, connected),
            last_error=self.status.last_error,
            update_available=self.status.update_available,
            latest_version=self.status.latest_version,
        )
        self.runtime.save_status(self.status)

    def _should_attempt_reconnect(self, now: datetime, device) -> bool:
        if not self.config.bluetooth.auto_reconnect:
            return False
        if not self.config.bluetooth.trusted_device.address:
            return False
        if not self.bluez.adapter.powered:
            return False
        if device and device.connected:
            return False
        return self.reconnect_controller.should_attempt(now=now)

    def _attempt_reconnect(self, now: datetime, device) -> None:
        object_path = None
        if device:
            object_path = device.object_path
        elif self.config.bluetooth.trusted_device.object_path:
            object_path = self.config.bluetooth.trusted_device.object_path
        if not object_path:
            return
        try:
            self.bluez.trust_device(object_path, True)
            self.bluez.connect_device(object_path)
            self.reconnect_controller.mark_success()
            self._record_event(
                "INFO",
                "bluetooth.reconnect",
                "Reconnect attempt dispatched",
                object_path=object_path,
            )
        except Exception as exc:
            next_attempt = self.reconnect_controller.mark_failure(now=now)
            self._record_event(
                "WARNING",
                "bluetooth.reconnect_failed",
                "Reconnect attempt failed",
                object_path=object_path,
                error=str(exc),
                next_attempt_at=next_attempt.isoformat(),
            )

    def _attempt_lock(self, now: datetime) -> None:
        result = self.lock_manager.lock(self.config.session.lock_method)
        if result.success:
            self._next_lock_retry_at = None
            self.state_machine.mark_lock_success(now=now, reason="trusted phone absent")
            self._record_event(
                "WARNING",
                "session.locked",
                "Session locked because the trusted phone is away",
                strategy=result.strategy,
            )
            if self.config.session.notifications_enabled:
                send_notification(
                    "BlueLatch locked this session",
                    "Trusted phone is away. Manual unlock override will suppress re-locking until the phone returns.",
                )
        else:
            self._next_lock_retry_at = now + timedelta(seconds=30)
            self.status.last_error = result.message
            self._record_event(
                "ERROR",
                "session.lock_failed",
                "Failed to lock the current session",
                strategy=result.strategy,
                error=result.message,
            )

    def _record_state_change(self, old: ProtectionState, new: ProtectionState) -> None:
        if old == new:
            return
        self._previous_state = new
        message = f"Protection state changed from {old.value} to {new.value}"
        self._record_event(
            "INFO",
            "presence.state_changed",
            message,
            old_state=old.value,
            new_state=new.value,
        )
        if (
            new is ProtectionState.AWAY_MANUAL_OVERRIDE
            and self.config.session.notifications_enabled
        ):
            send_notification(
                "BlueLatch manual override active",
                "The session was unlocked while the trusted phone is still away. Re-locking is suspended until the phone returns.",
            )

    def _record_event(self, level: str, event: str, message: str, **context: object) -> None:
        record = EventRecord.new(level=level, event=event, message=message, **context)
        self.runtime.append_event(record)
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, message, extra={"context": context})

    def _reload_config_if_needed(self) -> bool:
        if not self.config_manager.has_external_change():
            return True
        self.config = self.config_manager.load()
        self.logger.setLevel(logging.DEBUG if self.config.logging.debug_enabled else logging.INFO)
        self.presence_estimator = PresenceEstimator(self.config.protection)
        self.state_machine.settings = self.config.protection
        self.reconnect_controller = ReconnectController(
            backoff=ReconnectBackoff(
                initial_seconds=self.config.bluetooth.reconnect_initial_seconds,
                max_seconds=self.config.bluetooth.reconnect_max_seconds,
                jitter_ratio=self.config.bluetooth.reconnect_jitter_ratio,
            ),
        )
        self._record_event("INFO", "config.reloaded", "Configuration reloaded")
        return True

    def _on_session_lock_change(self, locked: bool) -> None:
        event = "session.locked_signal" if locked else "session.unlocked_signal"
        message = "Session reported locked" if locked else "Session reported unlocked"
        self._record_event("INFO", event, message, backend=self.session_monitor.backend)

    def _on_resume(self) -> None:
        self.reconnect_controller.next_attempt_at = utc_now()
        self._record_event("INFO", "system.resumed", "System resumed from suspend")

    def _on_bluetooth_change(self) -> None:
        self.bluez.maybe_refresh()

    def _on_adapter_change(self) -> None:
        self.bluez.maybe_refresh()
        self._record_event(
            "INFO",
            "bluetooth.adapter_changed",
            "Bluetooth adapter state changed",
            powered=self.bluez.adapter.powered,
            discovering=self.bluez.adapter.discovering,
        )

    def _schedule_update_check(self) -> None:
        if not self.config.updates.check_on_startup:
            return
        thread = threading.Thread(target=self._update_check_worker, daemon=True)
        thread.start()

    def _update_check_worker(self) -> None:
        result = self.update_service.check_for_updates(__version__)
        self.status.update_available = result.update_available
        self.status.latest_version = result.latest_version
        self.runtime.save_status(self.status)
        if result.update_available:
            self._record_event(
                "INFO",
                "updates.available",
                "Update available",
                latest_version=result.latest_version,
                package_type=result.package_type.value,
            )
            if self.config.session.notifications_enabled:
                send_notification(
                    "BlueLatch update available",
                    result.guidance,
                )

    def _reconnect_status(self, now: datetime, connected: bool) -> str:
        if connected:
            return "connected"
        if self.reconnect_controller.next_attempt_at is None:
            return "idle"
        if now >= self.reconnect_controller.next_attempt_at:
            return "ready"
        return f"waiting until {self.reconnect_controller.next_attempt_at.isoformat()}"


def run_agent() -> int:
    agent = BlueLatchAgent()
    return agent.run()


def spawn_background_agent() -> None:
    subprocess.Popen(
        [sys.executable, "-m", "bluelatch.main", "--agent"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
