"""CZML (Cesium Markup Language) writer for 3DANTS simulation results.

Converts SimulationResults from the orchestrator into a .czml file
that can be loaded directly into CesiumJS for 3D visualization of
satellite trajectories, ground stations, coverage cells, and
channel-quality metrics.

The writer is framework-agnostic: it uses duck typing to access
results.sat_position, results.p_rx, results.sat_orbital_params,
results.interference, and results.config.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import matplotlib.cm as _cm
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False

try:
    from pyproj import Geod
    _HAS_PYPROJ = True
except ImportError:
    _HAS_PYPROJ = False


# ---------------------------------------------------------------------------
# Coordinate / colour helpers
# ---------------------------------------------------------------------------

def _rgba(r: int, g: int, b: int, a: int = 255) -> Dict:
    """CZML colour shorthand: {"rgba": [r, g, b, a]}."""
    return {"rgba": [r, g, b, a]}


def _pwr_to_rgba(pwr_dbw: float,
                 vmin_dbw: float = -120.0,
                 vmax_dbw: float = -60.0) -> List[int]:
    """Map received power (dBW) to an [r, g, b, a] colour list."""
    norm = float(np.clip((pwr_dbw - vmin_dbw) / (vmax_dbw - vmin_dbw), 0.0, 1.0))
    if _HAS_MPL:
        rgba = _cm.viridis(norm)
        return [int(c * 255) for c in rgba[:3]] + [255]
    return [int(255 * (1 - norm)), int(255 * norm), 0, 255]


def _ecef_km_to_m(arr: Any) -> np.ndarray:
    """Convert skyfield ITRF position (km) to Cesium ECEF (meters)."""
    return np.asarray(arr, dtype=float) * 1000.0


def _sub_satellite_latlon(x_m: float, y_m: float, z_m: float) -> Tuple[float, float]:
    """Convert ECEF (meters) to latitude/longitude (degrees)."""
    r = np.sqrt(x_m ** 2 + y_m ** 2 + z_m ** 2)
    if r == 0:
        return 0.0, 0.0
    lat = np.degrees(np.arcsin(z_m / r))
    lon = np.degrees(np.arctan2(y_m, x_m))
    return float(lat), float(lon)


def _hexagon_vertices(center_lat: float, center_lon: float,
                      radius_km: float = 25.0) -> List[float]:
    """Generate 6 vertices for a hexagonal cell (lon, lat, height) degrees."""
    coords: List[float] = []
    if _HAS_PYPROJ:
        geod = Geod(ellps="WGS84")
        for angle in range(0, 360, 60):
            lon, lat, _ = geod.fwd(center_lon, center_lat, angle, radius_km * 1000)
            coords.extend([float(lon), float(lat), 0.0])
    else:
        dlat = radius_km / 111.32
        dlon = radius_km / (111.32 * np.cos(np.radians(center_lat)))
        for angle in range(0, 360, 60):
            rad = np.radians(angle)
            clat = center_lat + dlat * np.cos(rad)
            clon = center_lon + dlon * np.sin(rad)
            coords.extend([float(clon), float(clat), 0.0])
    return coords


def _overlapping_rhombus_vertices(gs_lat: float, gs_lon: float,
                                  sat_lat: float, sat_lon: float,
                                  radius_km: float = 25.0) -> List[float]:
    """Calculate the 4 vertices of the overlapping rhombus between GS cell and Sat beam cell."""
    if _HAS_PYPROJ:
        geod = Geod(ellps="WGS84")
        mid_lat = (gs_lat + sat_lat) / 2.0
        mid_lon = (gs_lon + sat_lon) / 2.0
        fwd_az, _, _ = geod.inv(gs_lon, gs_lat, sat_lon, sat_lat)
        
        m1_lon, m1_lat, _ = geod.fwd(mid_lon, mid_lat, fwd_az + 90, radius_km * 500)
        m2_lon, m2_lat, _ = geod.fwd(mid_lon, mid_lat, fwd_az - 90, radius_km * 500)
        
        return [
            float(gs_lon), float(gs_lat), 0.0,
            float(m1_lon), float(m1_lat), 0.0,
            float(sat_lon), float(sat_lat), 0.0,
            float(m2_lon), float(m2_lat), 0.0,
        ]
    else:
        mid_lat = (gs_lat + sat_lat) / 2.0
        mid_lon = (gs_lon + sat_lon) / 2.0
        dlat = (sat_lat - gs_lat) * 0.4
        dlon = (sat_lon - gs_lon) * 0.4
        return [
            float(gs_lon), float(gs_lat), 0.0,
            float(mid_lon + dlon), float(mid_lat - dlat), 0.0,
            float(sat_lon), float(sat_lat), 0.0,
            float(mid_lon - dlon), float(mid_lat + dlat), 0.0,
        ]


def _to_float(val: Any) -> float:
    """Extract a Python float from scalars or 1-element arrays."""
    if isinstance(val, np.ndarray):
        return float(val.item())
    return float(val)


def _is_numeric(val: Any) -> bool:
    """Check if *val* can be converted to a Python float."""
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def _sanitize_id(sat_id: Any) -> str:
    """Convert a satellite identifier to a URL-safe CZML entity id fragment.

    Spaces and special characters are replaced with underscores so that
    CZML entity ids are always valid (e.g. "Sat 1" -> "Sat_1").
    """
    return str(sat_id).replace(" ", "_").replace("-", "_").replace(".", "_")


def _safe_mean(values: Any, default: float = 0.0) -> float:
    """Mean of *values*, ignoring NaN. Returns *default* if empty."""
    arr = np.asarray(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        return default
    return float(np.mean(arr))


def _group_by_satellite(df: Optional[pd.DataFrame]) -> Dict[Any, pd.DataFrame]:
    """Group a DataFrame by its 'Satellite ID' column."""
    if df is None or len(df) == 0:
        return {}
    return dict(tuple(df.groupby('Satellite ID')))


# ---------------------------------------------------------------------------
# Main writer
# ---------------------------------------------------------------------------

class CZMLWriter:
    """Convert SimulationResults to Cesium Markup Language (CZML).

    Parameters
    ----------
    results : SimulationResults
        The results object produced by NetworkSimulation.run().
    max_points : int
        Maximum trajectory samples per satellite. Excess rows are evenly
        subsampled to keep file sizes manageable.
    circle_points : int
        Vertices per coverage circle.
    """

    def __init__(self, results: Any, max_points: int = 1000,
                 circle_points: int = 16):
        self.results = results
        self.max_points = max_points
        self.circle_points = circle_points
        self.cfg = getattr(results, 'config', None) if results is not None else None

    # -- public API --------------------------------------------------------

    def to_czml(self) -> str:
        """Return the CZML document as a pretty-printed JSON string."""
        return json.dumps(self._build_entities(), indent=2)

    def write(self, path: str) -> str:
        """Write the CZML document to *path*. Returns the path."""
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(self.to_czml())
        return path

    # -- entity builders ---------------------------------------------------

    def _build_entities(self) -> List[Dict]:
        """Assemble the full list of CZML entity dicts."""
        if self.results is None or self.cfg is None:
            return [self._document_entity("3DANTS CZML (no results)")]

        epoch_dt = self._compute_epoch_datetime()
        epoch_iso = epoch_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        entities: List[Dict] = [
            self._document_entity("3DANTS Simulation", epoch_iso),
            self._ground_station_entity(),
        ]

        sat_groups = _group_by_satellite(self.results.sat_position)
        p_rx_groups = _group_by_satellite(
            getattr(self.results, 'p_rx', None))
        orbital_groups = _group_by_satellite(
            getattr(self.results, 'sat_orbital_params', None))
        interference_groups = _group_by_satellite(
            getattr(self.results, 'interference', None))
        channel_groups = _group_by_satellite(
            getattr(self.results, 'satellite_channel_time_series', None))

        for sat_id, group in sat_groups.items():
            group = self._subsample(group)
            entities.append(self._satellite_entity(
                sat_id, group, epoch_dt,
                p_rx_groups.get(sat_id, None),
                orbital_groups.get(sat_id, None),
                interference_groups.get(sat_id, None),
                channel_groups.get(sat_id, None),
            ))
            entities.append(self._coverage_polygon_entity(sat_id, group, epoch_dt))
            entities.append(self._overlap_rhombus_entity(sat_id, group))

        return entities

    def _document_entity(self, name: str, epoch_iso: str = "") -> Dict:
        """The mandatory CZML document header entity."""
        if not epoch_iso:
            epoch_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        return {
            "id": "document",
            "name": name,
            "version": "1.0",
            "epoch": epoch_iso,
        }

    def _ground_station_entity(self) -> Dict:
        """A fixed point/billboard at the configured ground-station location."""
        cfg = self.cfg
        r_e = cfg.r_E
        lat_r = np.radians(cfg.gs_lat)
        lon_r = np.radians(cfg.gs_lon)
        x = r_e * np.cos(lat_r) * np.cos(lon_r)
        y = r_e * np.cos(lat_r) * np.sin(lon_r)
        z = r_e * np.sin(lat_r)

        return {
            "id": "ground_station",
            "name": "Ground Station",
            "description": f"Ground station at {cfg.gs_lat}°N, {cfg.gs_lon}°E",
            "position": {"cartesian": [x, y, z]},
            "point": {
                "color": _rgba(0, 255, 0, 255),
                "pixelSize": 10,
                "outlineColor": _rgba(255, 255, 255, 255),
                "outlineWidth": 2,
            },
            "label": {
                "text": "Ground Station",
                "font": "14px sans-serif",
                "fillColor": _rgba(255, 255, 255, 200),
                "outlineColor": _rgba(0, 0, 0, 255),
                "outlineWidth": 2,
                "pixelOffset": {"cartesian2": [0, 20]},
            },
        }

    def _satellite_entity(self, sat_id: Any, group: pd.DataFrame,
                          epoch_dt: datetime,
                          p_rx_group: Optional[pd.DataFrame],
                          orbital_group: Optional[pd.DataFrame],
                          interference_group: Optional[pd.DataFrame],
                          channel_group: Optional[pd.DataFrame] = None) -> Dict:
        """Build a time-dynamic satellite trajectory entity."""
        # -- positions (ECEF, meters) ----------------------------------
        raw_positions = group['Sat Position (km)'].tolist()
        positions_m = [_ecef_km_to_m(p) for p in raw_positions]

        # -- time offsets from document epoch --------------------------
        times = pd.to_datetime(group['Time'])
        offsets = (times - epoch_dt).dt.total_seconds().tolist()

        # -- build cartesian: [t, x, y, z, t, x, y, z, ...] -----------
        cartesian: List[float] = []
        for pos_m, t_off in zip(positions_m, offsets):
            cartesian.extend([
                float(t_off), float(pos_m[0]), float(pos_m[1]), float(pos_m[2]),
            ])

        # -- mean P_Rx → path colour -----------------------------------
        if p_rx_group is not None and 'P_rx_at_User (dBW)' in p_rx_group.columns:
            mean_p_rx = _safe_mean(p_rx_group['P_rx_at_User (dBW)'], default=-90.0)
        else:
            mean_p_rx = -90.0
        colour = _pwr_to_rgba(mean_p_rx)

        # -- entity properties -------------------------------------------
        # Handle both numeric and string satellite IDs gracefully.
        if _is_numeric(sat_id):
            satellite_id_prop = {"number": _to_float(sat_id)}
        else:
            satellite_id_prop = {"string": str(sat_id)}

        properties: Dict[str, Any] = {
            "satelliteId": satellite_id_prop,
            "meanPRx": {"number": round(mean_p_rx, 2)},
        }

        if p_rx_group is not None:
            if 'SNR (dB)' in p_rx_group.columns:
                properties["meanSNR"] = {
                    "number": round(_safe_mean(p_rx_group['SNR (dB)']), 2)}
            if 'Distance (km)' in p_rx_group.columns:
                properties["meanDistance"] = {
                    "number": round(_safe_mean(p_rx_group['Distance (km)']), 2)}

        if interference_group is not None and 'SINR (dB)' in interference_group.columns:
            properties["meanSINR"] = {
                "number": round(_safe_mean(interference_group['SINR (dB)']), 2)}

        if orbital_group is not None:
            for col in ['Theta_el_sat_see_vsat', 'Theta_az_sat_see_vsat',
                        'theta_el_vsat_see_sat', 'theta_az_vsat_see_sat']:
                if col in orbital_group.columns:
                    properties[f"mean_{col}"] = {
                        "number": round(_safe_mean(orbital_group[col]), 4)}

        if channel_group is not None:
            for col in ['small scale fading-channel', 'large scale shadowing']:
                if col in channel_group.columns:
                    values = channel_group[col].dropna().values
                    if len(values) > 0:
                        properties[f"mean_{col}"] = {
                            "number": round(float(np.mean(
                                np.abs(values))), 4)}

        return {
            "id": f"sat_{_sanitize_id(sat_id)}",
            "name": f"Satellite {sat_id}",
            "description": (
                f"Satellite {sat_id} — mean P_Rx: {mean_p_rx:.1f} dBW"),
            "position": {
                "epoch": epoch_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "cartesian": cartesian,
            },
            "path": {
                "material": {"solidColor": {"color": _rgba(*colour)}},
                "width": 2,
                "resolution": 1,
                "leadTime": 0,
                "trailTime": 0,
            },
            "point": {
                "color": _rgba(*colour),
                "pixelSize": 5,
                "outlineColor": _rgba(0, 0, 0, 0),
            },
            "properties": properties,
        }

    def _coverage_polygon_entity(self, sat_id: Any, group: pd.DataFrame,
                                 epoch_dt: datetime) -> Dict:
        """Build a hexagonal beam footprint coverage polygon for a satellite sub-point."""
        radius_km = self.cfg.cell_radius_km
        first_pos_km = group['Sat Position (km)'].iloc[0]
        pos_m = _ecef_km_to_m(first_pos_km)
        lat, lon = _sub_satellite_latlon(pos_m[0], pos_m[1], pos_m[2])
        hexagon = _hexagon_vertices(lat, lon, radius_km)

        return {
            "id": f"coverage_sat_{_sanitize_id(sat_id)}",
            "name": f"Satellite {sat_id} Hexagonal Beam Footprint",
            "description": f"Hexagonal beam footprint (radius: {radius_km} km) for satellite {sat_id}",
            "polygon": {
                "positions": {
                    "cartographicDegrees": hexagon,
                },
                "material": {"solidColor": {"color": _rgba(0, 220, 255, 80)}},
                "outline": True,
                "outlineColor": _rgba(0, 220, 255, 220),
                "perPositionHeight": True,
                "closeTop": True,
                "closeBottom": False,
            },
        }

    def _overlap_rhombus_entity(self, sat_id: Any, group: pd.DataFrame) -> Dict:
        """Build an overlapping rhombus polygon highlighting intersection between GS and satellite beam."""
        cfg = self.cfg
        radius_km = cfg.cell_radius_km
        first_pos_km = group['Sat Position (km)'].iloc[0]
        pos_m = _ecef_km_to_m(first_pos_km)
        sat_lat, sat_lon = _sub_satellite_latlon(pos_m[0], pos_m[1], pos_m[2])
        rhombus = _overlapping_rhombus_vertices(cfg.gs_lat, cfg.gs_lon, sat_lat, sat_lon, radius_km)

        return {
            "id": f"overlap_rhombus_{_sanitize_id(sat_id)}",
            "name": f"Overlap Rhombus (Sat {sat_id} / GS)",
            "description": f"Overlapping rhombus area between Ground Station cell and Satellite {sat_id} beam footprint",
            "polygon": {
                "positions": {
                    "cartographicDegrees": rhombus,
                },
                "material": {"solidColor": {"color": _rgba(50, 205, 50, 140)}},
                "outline": True,
                "outlineColor": _rgba(50, 255, 50, 255),
                "perPositionHeight": True,
                "closeTop": True,
                "closeBottom": False,
            },
        }

    # -- internal helpers --------------------------------------------------

    def _compute_epoch_datetime(self) -> datetime:
        """Return the earliest timestamp across all satellite positions."""
        times = pd.to_datetime(self.results.sat_position['Time'])
        return times.min().to_pydatetime()

    def _subsample(self, group: pd.DataFrame) -> pd.DataFrame:
        """Evenly subsample *group* to at most self.max_points rows."""
        n = len(group)
        if n <= self.max_points:
            return group
        indices = np.linspace(0, n - 1, self.max_points, dtype=int)
        return group.iloc[indices].reset_index(drop=True)
