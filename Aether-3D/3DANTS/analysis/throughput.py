"""Throughput and spectral-efficiency helpers.

Uses the Shannon-Hartley formula ``B * log2(1 + SINR)`` with SINR
converted from dB to linear scale.
"""
from __future__ import annotations

import numpy as np


def spectral_efficiency(sinr_db, bandwidth_hz):
    """Per-sample spectral efficiency (bits/s) via Shannon-Hartley.

    Parameters
    ----------
    sinr_db : array-like
        SINR values in dB.
    bandwidth_hz : float
        Channel bandwidth in Hz.

    Returns
    -------
    numpy.ndarray
        Throughput in bits/s for each SINR sample.
    """
    sinr_lin = 10 ** (np.asarray(sinr_db, dtype=float) / 10.0)
    return bandwidth_hz * np.log2(1 + sinr_lin)


def mean_throughput(sinr_db, bandwidth_hz):
    """Average throughput across all SINR samples.

    Parameters
    ----------
    sinr_db : array-like
        SINR values in dB.
    bandwidth_hz : float
        Channel bandwidth in Hz.

    Returns
    -------
    float
        Mean throughput in bits/s.
    """
    se = spectral_efficiency(sinr_db, bandwidth_hz)
    if se.size == 0:
        return 0.0
    return float(np.mean(se))


def throughput_cdf(sinr_db, bandwidth_hz):
    """Empirical CDF of per-sample throughput.

    Parameters
    ----------
    sinr_db : array-like
        SINR values in dB.
    bandwidth_hz : float
        Channel bandwidth in Hz.

    Returns
    -------
    tuple of (numpy.ndarray, numpy.ndarray)
        Sorted throughput values and cumulative proportions.
    """
    se = spectral_efficiency(sinr_db, bandwidth_hz)
    sorted_data = np.sort(se)
    n = sorted_data.size
    if n <= 1:
        yvals = np.zeros(n)
    else:
        yvals = np.arange(n) / float(n - 1)
    return sorted_data, yvals
