"""Empirical CDF helpers.

Pure numerical helpers plus a plotting function. The numerical helper has no
dependency on matplotlib so it can be used in any context.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np


def empirical_cdf(data) -> Tuple["np.ndarray", "np.ndarray"]:
    """Return ``(sorted_data, yvals)`` for the empirical CDF of ``data``.

    ``yvals`` are the cumulative proportions in ``[0, 1]``. For a single
    sample the denominator is guarded against zero.
    """
    sorted_data = np.sort(np.asarray(data))
    n = sorted_data.size
    if n <= 1:
        yvals = np.zeros(n)
    else:
        yvals = np.arange(n) / float(n - 1)
    return sorted_data, yvals


def plot_cdf(ax, data, label, color, marker=None) -> bool:
    """Plot the empirical CDF of ``data`` on the given Axes.

    Returns ``True`` if anything was plotted, ``False`` if ``data`` was empty.
    Does not call ``plt.show()``.
    """
    if len(data) == 0:
        return False
    sorted_data, yvals = empirical_cdf(data)
    ax.plot(
        sorted_data,
        yvals,
        label=label,
        color=color,
        linewidth=2,
        marker=marker,
        markersize=5,
        markevery=20 if marker else None,
    )
    return True