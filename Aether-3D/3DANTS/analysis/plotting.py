"""Reusable matplotlib figure/axes helpers.

All functions accept (or create) an Axes, return the Axes, and never call
``plt.show()`` so simulation runs can stay headless.
"""
from __future__ import annotations

import numpy as np


def plot_visibility_bars(summary, ax=None, **kwargs):
    """Bar plot of total visibility (minutes) per satellite.

    ``summary`` is a DataFrame with ``Satellite`` and ``Visibility`` columns
    (as produced by :func:`analysis.visibility.visibility_summary`).
    """
    import matplotlib.pyplot as plt

    if ax is None:
        fig, ax = plt.subplots(**kwargs)
    ax.bar(summary["Satellite"].astype(str), summary["Visibility"].values)
    ax.set_xlabel("Satellite")
    ax.set_ylabel("Total Visibility Duration (minutes)")
    ax.set_title("Satellite Visibility Durations")
    ax.tick_params(axis="x", rotation=90)
    return ax


def plot_network_geometry(
    cell_vertices_positions,
    gs_pos,
    user_pos,
    bs_positions,
    haps_pos,
    ax=None,
    **kwargs,
):
    """2D scatter of the ground-cell geometry.

    Replicates the per-pass geometry plot from the original example, but runs
    once after the simulation with the last pass's positions.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        fig, ax = plt.subplots(**kwargs)

    for ver in range(cell_vertices_positions.shape[1]):
        ax.plot(
            cell_vertices_positions[0, ver],
            cell_vertices_positions[1, ver],
            label="cell border",
            c="blue",
            marker="o",
        )
    ax.scatter(gs_pos[0], gs_pos[1], label="Cell center", c="red", marker="o")
    ax.scatter(user_pos[0], user_pos[1], label="Sat. User", c="c", marker="o")
    for iii, bs in enumerate(bs_positions):
        ax.scatter(bs[0], bs[1], label=f"Base Station {iii + 1}", marker="d", s=150)
    ax.scatter(haps_pos[:, 0], haps_pos[:, 1], label="HAP", c="m", marker="h")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True)
    return ax


def plot_interference_cdf(interference_df, ax=None, sources=None, colors=None, **kwargs):
    """Empirical CDF of the interference source levels.

    Uses :func:`analysis.cdf.plot_cdf` so plotting is delegated and
    ``plt.show()`` is never called here.
    """
    from .cdf import plot_cdf

    if ax is None:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(**kwargs)

    if sources is None:
        sources = ("HAPS_rx", "BaseStation1_rx", "BaseStation2_rx", "BaseStation3_rx")
    if colors is None:
        colors = plt.cm.tab10.colors

    for idx, col in enumerate(sources):
        if col in interference_df.columns:
            data = interference_df[col].dropna().values
            color = colors[idx % len(colors)]
            plot_cdf(ax, data, label=col, color=color)

    ax.set_xlabel("Received power (dB)")
    ax.set_ylabel("Empirical CDF")
    ax.set_title("Interference source level distributions")
    ax.legend()
    return ax