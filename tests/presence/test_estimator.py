from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bluelatch.config.models import ProtectionConfig
from bluelatch.models import PresenceMode
from bluelatch.presence.estimator import PresenceEstimator, SignalBand


def test_estimator_smooths_rssi_and_classifies_signal_band() -> None:
    settings = ProtectionConfig(
        mode=PresenceMode.WEAK_SIGNAL_OR_DISCONNECT,
        near_threshold=-65,
        far_threshold=-80,
        signal_smoothing_window=3,
    )
    estimator = PresenceEstimator(settings=settings)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)

    estimator.update(connected=True, rssi=-60, observed_at=base)
    estimator.update(connected=True, rssi=-68, observed_at=base + timedelta(seconds=1))
    assessment = estimator.update(
        connected=True,
        rssi=-64,
        observed_at=base + timedelta(seconds=2),
    )

    assert round(assessment.smoothed_rssi or 0, 2) == -64.0
    assert assessment.signal_band is SignalBand.NEAR
    assert assessment.appears_present is True


def test_hybrid_mode_holds_short_disconnects() -> None:
    estimator = PresenceEstimator(
        settings=ProtectionConfig(mode=PresenceMode.HYBRID, away_grace_seconds=20),
    )
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)

    estimator.update(connected=True, rssi=-70, observed_at=base)
    assessment = estimator.update(
        connected=False,
        rssi=None,
        observed_at=base + timedelta(seconds=2),
    )

    assert assessment.appears_present is True
