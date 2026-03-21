from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from bluelatch.config.models import ProtectionConfig
from bluelatch.models import PresenceMode
from bluelatch.presence.models import PresenceAssessment, SignalBand


@dataclass(slots=True)
class PresenceEstimator:
    settings: ProtectionConfig
    _samples: deque[int] = field(init=False)
    _last_band: SignalBand = field(init=False, default=SignalBand.UNKNOWN)
    _last_connected_at: datetime | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        self._samples = deque(maxlen=self.settings.signal_smoothing_window)

    def update(
        self,
        *,
        connected: bool,
        rssi: int | None,
        observed_at: datetime,
    ) -> PresenceAssessment:
        if connected:
            self._last_connected_at = observed_at
        if rssi is not None:
            self._samples.append(rssi)

        smoothed = self.smoothed_rssi
        band = self._classify_band(smoothed)
        appears_present, reason = self._evaluate_presence(
            connected=connected,
            band=band,
            observed_at=observed_at,
        )
        self._last_band = band
        return PresenceAssessment(
            connected=connected,
            rssi=rssi,
            smoothed_rssi=smoothed,
            signal_band=band,
            appears_present=appears_present,
            mode=self.settings.mode,
            reason=reason,
            observed_at=observed_at,
        )

    @property
    def smoothed_rssi(self) -> float | None:
        if not self._samples:
            return None
        return sum(self._samples) / len(self._samples)

    def _classify_band(self, smoothed: float | None) -> SignalBand:
        if smoothed is None:
            return SignalBand.UNKNOWN
        if smoothed >= self.settings.near_threshold:
            return SignalBand.NEAR
        if smoothed <= self.settings.far_threshold:
            return SignalBand.FAR
        if self._last_band in {SignalBand.NEAR, SignalBand.FAR}:
            return self._last_band
        return SignalBand.MID

    def _evaluate_presence(
        self,
        *,
        connected: bool,
        band: SignalBand,
        observed_at: datetime,
    ) -> tuple[bool, str]:
        if self.settings.mode is PresenceMode.DISCONNECT_ONLY:
            return connected, "device connected" if connected else "device disconnected"

        if self.settings.mode is PresenceMode.WEAK_SIGNAL_OR_DISCONNECT:
            if connected and band is not SignalBand.FAR:
                return True, "link up with acceptable signal"
            if connected:
                return False, "signal below far threshold"
            return False, "device disconnected"

        # HYBRID mode keeps a short hold after disconnect to absorb transient drops,
        # but still treats a stably weak signal as away.
        disconnect_hold = timedelta(seconds=min(5, self.settings.away_grace_seconds))
        if connected and band is not SignalBand.FAR:
            return True, "hybrid mode sees a live connection"
        if connected and band is SignalBand.FAR:
            return False, "hybrid mode sees stably weak signal"
        if (
            self._last_connected_at is not None
            and observed_at - self._last_connected_at <= disconnect_hold
            and band in {SignalBand.NEAR, SignalBand.MID, SignalBand.UNKNOWN}
        ):
            return True, "recent disconnect within hybrid hold window"
        return False, "disconnected beyond hold window"
