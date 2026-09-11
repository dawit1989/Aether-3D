"""Reusable traffic-model construction.

Wraps the existing ``TrafficModel`` implementation (located in the legacy
``3DANTS.Traffic`` package) with small factory functions so the orchestrator
does not duplicate construction logic. The behaviour of the underlying
``TrafficModel`` is preserved.
"""
from __future__ import annotations

from typing import Dict

from ..Traffic.Traffic_models import TrafficModel

# Base station label ordering used by the orchestrator.
BS_LABELS = ("BS1", "BS2", "BS3")


def cbr(packet_size=1000, packet_rate=10) -> TrafficModel:
    """Constant Bit Rate traffic model."""
    return TrafficModel("CBR", packet_size=packet_size, packet_rate=packet_rate)


def poisson(avg_packet_rate=10, packet_size_mean=1000, packet_size_std=200) -> TrafficModel:
    """Poisson traffic model."""
    return TrafficModel(
        "Poisson",
        avg_packet_rate=avg_packet_rate,
        packet_size_mean=packet_size_mean,
        packet_size_std=packet_size_std,
    )


def bursty(on_duration=0.5, off_duration=0.5, packet_rate_on=20, packet_size=1000) -> TrafficModel:
    """Bursty (ON/OFF) traffic model."""
    return TrafficModel(
        "Bursty",
        on_duration=on_duration,
        off_duration=off_duration,
        packet_rate_on=packet_rate_on,
        packet_size=packet_size,
    )


def build_traffic_models(duration_s, num_sat, haps_rate=10, bs_rates=(10, 8, 5)) -> Dict[str, TrafficModel]:
    """Build and pre-generate packets for all traffic models.

    - ``num_sat`` satellite models using CBR (packet_size=1000, packet_rate=10),
      keyed ``'Sat {i}'``.
    - One HAPS model using Poisson (``avg_packet_rate=haps_rate``).
    - One Poisson model per entry in ``bs_rates``, keyed ``BS1``, ``BS2``, ...

    ``generate_packets(duration_s)`` is called on every model so the returned
    objects are ready for ``get_packets_at_time``.
    """
    models: Dict[str, TrafficModel] = {}

    for i in range(1, num_sat + 1):
        m = cbr(packet_size=1000, packet_rate=10)
        m.generate_packets(duration_s)
        models[f"Sat {i}"] = m

    haps = poisson(avg_packet_rate=haps_rate, packet_size_mean=1000, packet_size_std=200)
    haps.generate_packets(duration_s)
    models["HAPS"] = haps

    for idx, rate in enumerate(bs_rates):
        label = BS_LABELS[idx] if idx < len(BS_LABELS) else f"BS{idx + 1}"
        m = poisson(avg_packet_rate=rate, packet_size_mean=1000, packet_size_std=200)
        m.generate_packets(duration_s)
        models[label] = m

    return models