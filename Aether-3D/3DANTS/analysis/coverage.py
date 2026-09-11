"""Coverage-probability helpers.

Coverage is defined as the fraction of locations (or time samples)
whose SINR exceeds a given threshold.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def coverage_probability(sinr_db, threshold_db=-5.0):
    """Fraction of SINR samples at or above *threshold_db*.

    Parameters
    ----------
    sinr_db : array-like
        SINR values in dB.
    threshold_db : float
        SINR threshold in dB (default -5.0).

    Returns
    -------
    float
        Coverage probability in [0, 1].
    """
    arr = np.asarray(sinr_db, dtype=float)
    if arr.size == 0:
        return 0.0
    return float(np.mean(arr >= threshold_db))


def coverage_vs_elevation(
    sinr_df,
    elevation_col="Elevation Angle (degree)",
    sinr_col="SINR (dB)",
    threshold_db=-5.0,
    num_bins=9,
):
    """Coverage probability binned by elevation angle.

    Parameters
    ----------
    sinr_df : pandas.DataFrame
        DataFrame with elevation and SINR columns.
    elevation_col : str
        Name of the elevation-angle column.
    sinr_col : str
        Name of the SINR column (dB).
    threshold_db : float
        SINR threshold for coverage.
    num_bins : int
        Number of equal-width elevation bins.

    Returns
    -------
    pandas.DataFrame
        Columns: elevation_bin, elevation_center, coverage_prob, count.
    """
    elev = np.asarray(sinr_df[elevation_col].values, dtype=float)
    sinr = np.asarray(sinr_df[sinr_col].values, dtype=float)

    lo = float(np.nanmin(elev)) if elev.size else 0.0
    hi = float(np.nanmax(elev)) if elev.size else 90.0
    bins = np.linspace(lo, hi, num_bins + 1)
    indices = np.digitize(elev, bins) - 1
    indices = np.clip(indices, 0, num_bins - 1)

    rows = []
    for b in range(num_bins):
        mask = indices == b
        count = int(np.sum(mask))
        if count > 0:
            cov = float(np.mean(sinr[mask] >= threshold_db))
        else:
            cov = 0.0
        lo_b = float(bins[b])
        hi_b = float(bins[b + 1])
        rows.append({
            "elevation_bin": f"{lo_b:.1f}-{hi_b:.1f}",
            "elevation_center": float((bins[b] + bins[b + 1]) / 2),
            "coverage_prob": cov,
            "count": count,
        })

    return pd.DataFrame(rows)
