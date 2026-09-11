"""Interference detection and scenario classification.

Vectorised helpers extracted from the analysis tail of the original example.
The classification semantics (active-source detection, scenario labels) are
preserved exactly.
"""
from __future__ import annotations

import numpy as np

# Noise floor used by the original example's analysis tail.
NOISE_FLOOR = -122.086

# (dataframe column, scenario label) pairs, in the original order.
DEFAULT_SOURCES = [
    ("HAPS_rx", "HAPS"),
    ("BaseStation1_rx", "BS1"),
    ("BaseStation2_rx", "BS2"),
    ("BaseStation3_rx", "BS3"),
]


def detect_interference(values, noise_floor=NOISE_FLOOR):
    """Return a boolean array: True where a value differs from the noise floor.

    Vectorised over array-like inputs. A sample is considered 'interfering'
    when ``abs(value - noise_floor) > 0.1``, matching the original logic.
    """
    arr = np.asarray(values)
    return np.abs(arr - noise_floor) > 0.1


def _scenario_label(active):
    """Map a list of active source names to the original scenario label."""
    n = len(active)
    if n == 0:
        return "No Interference"
    if n == 1:
        return f"{active[0]} only"
    if n == 2:
        return f"Two sources: {"+".join(active)}"
    if n == 3:
        return f"Three sources: {"+".join(active)}"
    if n == 4:
        return "All four sources"
    return "Unknown"


def classify_interference(df, sources=None, noise_floor=NOISE_FLOOR):
    """Add per-source ``*_active`` flags and an overall ``Scenario`` column.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain the interference columns referenced by ``sources``.
    sources : list of (column, label) tuples, optional
        Defaults to the four sources from the original example.
    noise_floor : float
        Reference noise floor for the detection threshold.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with the added ``*_active`` and ``Scenario`` columns.
    """
    if sources is None:
        sources = DEFAULT_SOURCES

    out = df.copy()
    for col, name in sources:
        out[name + "_active"] = detect_interference(out[col].values, noise_floor)

    def _row_scenario(row):
        active = [name for col, name in sources if row[name + "_active"]]
        return _scenario_label(active)

    out["Scenario"] = out.apply(_row_scenario, axis=1)
    return out