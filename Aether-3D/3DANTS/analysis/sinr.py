"""SINR computation and summary statistics.

Reusable helpers for converting received-power / interference values
(dB) into SINR and summarising the result.  All SINR *values* returned
are in linear scale unless otherwise stated.
"""
from __future__ import annotations

import numpy as np


def compute_sinr(p_rx_db, noise_power_db, interference_db=0):
    """Compute linear-scale SINR from dB inputs.

    Parameters
    ----------
    p_rx_db : array-like
        Received signal power in dB.
    noise_power_db : array-like or float
        Noise-plus-interference-floor power in dB.
    interference_db : array-like or float, optional
        Interference power in dB.  Pass *0* to effectively disable
        the interference term.

    Returns
    -------
    numpy.ndarray
        SINR in linear scale.
    """
    p_rx_lin = 10 ** (np.asarray(p_rx_db, dtype=float) / 10.0)
    noise_lin = 10 ** (np.asarray(noise_power_db, dtype=float) / 10.0)
    interf_lin = 10 ** (np.asarray(interference_db, dtype=float) / 10.0)
    return p_rx_lin / (noise_lin + interf_lin)


def outage_probability(sinr_db, threshold_db=-5.0):
    """Fraction of SINR samples below *threshold_db*.

    Parameters
    ----------
    sinr_db : array-like
        SINR values in dB.
    threshold_db : float
        SINR threshold in dB (default -5.0).

    Returns
    -------
    float
        Outage probability in [0, 1].
    """
    arr = np.asarray(sinr_db, dtype=float)
    if arr.size == 0:
        return 0.0
    return float(np.mean(arr < threshold_db))


def sinr_summary(df, column="SINR (dB)", threshold_db=-5.0):
    """Compute summary statistics for an SINR column.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing the SINR column.
    column : str
        Name of the SINR column (values in dB).
    threshold_db : float
        Threshold for outage probability.

    Returns
    -------
    dict
        Keys: mean, median, p05, p50, p95, outage_prob, count.
    """
    values = np.asarray(df[column].values, dtype=float)
    if values.size == 0:
        return {
            "mean": float("nan"),
            "median": float("nan"),
            "p05": float("nan"),
            "p50": float("nan"),
            "p95": float("nan"),
            "outage_prob": 0.0,
            "count": 0,
        }
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "p05": float(np.percentile(values, 5)),
        "p50": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
        "outage_prob": outage_probability(values, threshold_db),
        "count": int(values.size),
    }
