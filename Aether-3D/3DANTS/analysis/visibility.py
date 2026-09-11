"""Visibility-overlap computation for satellite constellations.

These functions extract the reusable visibility/event-sweep logic that was
embedded in the original example, so the orchestrator stays thin and the
behavior can be reused/tested independently.
"""
from __future__ import annotations

from collections import defaultdict

import pandas as pd


def compute_simultaneous_visibility(df, t_start, t_end):
    """Compute simultaneous-visibility group durations.

    Mirrors the event-sweep behavior of the original example: every satellite
    rise/set is treated as an event, events are sorted chronologically (rise
    before set on ties), the set of currently-visible satellites is tracked,
    and the duration of each unique visible-group is accumulated in minutes.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain ``Rise``, ``Set`` and ``Satellite`` columns whose
        ``Rise``/``Set`` values are datetimes (or anything comparable/sortable
        with subtraction yielding seconds).
    t_start, t_end : datetime-like
        Overall observation window.

    Returns
    -------
    pandas.DataFrame with columns ``group`` (a comma-joined label, or
    ``'No satellites'``) and ``duration_min`` (float minutes), one row per
    unique visibility group.
    """
    events = []
    for _, row in df.iterrows():
        events.append((row["Rise"], row["Satellite"], "rise"))
        events.append((row["Set"], row["Satellite"], "set"))

    # Sort by time; on equal times, 'rise' (==0) before 'set' (==1).
    sorted_events = sorted(events, key=lambda x: (x[0], x[2]))

    current_visible = set()
    group_durations = defaultdict(float)
    previous_time = t_start

    for time, satellite, event_type in sorted_events:
        if time > previous_time:
            duration = (time - previous_time).total_seconds() / 60.0
            group_durations[frozenset(current_visible)] += duration
        if event_type == "rise":
            current_visible.add(satellite)
        else:
            current_visible.remove(satellite)
        previous_time = time

    # Account for any remaining time until the simulation end.
    if t_end > previous_time:
        duration = (t_end - previous_time).total_seconds() / 60.0
        group_durations[frozenset(current_visible)] += duration

    rows = []
    for group in sorted(group_durations, key=lambda x: sorted(x)):
        label = ", ".join(sorted(group)) if group else "No satellites"
        rows.append({"group": label, "duration_min": group_durations[group]})

    return pd.DataFrame(rows, columns=["group", "duration_min"])


def visibility_summary(df):
    """Return total visibility duration (minutes) per satellite.

    Reproduces the original aggregation: group by satellite, sum the
    ``Visibility`` column (timedelta -> minutes), and order satellites by
    their first rise time.
    """
    total_visibility = df.groupby("Satellite")["Visibility"].sum()
    total_visibility_minutes = total_visibility.dt.total_seconds() / 60
    first_rise = df.groupby("Satellite")["Rise"].min()
    satellite_order = first_rise.sort_values().index
    total_visibility_minutes = total_visibility_minutes.loc[satellite_order]

    return pd.DataFrame(
        {
            "Satellite": total_visibility_minutes.index,
            "Visibility": total_visibility_minutes.values,
        }
    )