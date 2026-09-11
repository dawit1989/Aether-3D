"""Reconfigurable, extendable orchestrator for the 3DANTS network-with-traffic example.

This module replaces the original monolithic ``if __name__ == '__main__'`` script
with a fluent, layer-based simulation architecture. The simulation behaviour
(constellation setup, geometry, fading, shadowing, traffic, HAPS, base-station
interference, SINR and the produced DataFrames) is preserved; the code is
reorganised for configuration, testing and extension.

The ``3DANTS`` package name begins with a digit, so it cannot be imported with
a plain ``import``/``from`` statement. Package submodules are therefore loaded
through :func:`importlib.import_module`, which accepts arbitrary strings.
"""
from __future__ import annotations

import argparse
import datetime
import importlib
import os
import sys
from abc import ABC, abstractmethod
from types import SimpleNamespace
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Ensure the inner 3DANTS package (which starts with a digit and therefore
# cannot be imported with a plain import statement) is reachable.
_PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

import numpy as np
import pandas as pd
import skyfield.api as sf
from skyfield.api import wgs84


def _cls(dotted: str) -> type:
    """Resolve a dotted ``package.module.Attribute`` string to the attribute."""
    mod, _, name = dotted.rpartition(".")
    return getattr(importlib.import_module(mod), name)


# --- Package symbols (resolved at import time via importlib) ---
LEO_GEO = _cls("3DANTS.position_and_mobility.geo.LEO_GEO")
HexagonGrid = _cls("3DANTS.position_and_mobility.hexagon_grid.HexagonGrid")
HAPS_trajectory = _cls("3DANTS.position_and_mobility.haps.HAPS_trajectory")
terresterial_network = _cls("3DANTS.position_and_mobility.terrestrial.terresterial_network")
Satellite_communication_parameter = _cls("3DANTS.communication_channel.satellite_comm_param.Satellite_communication_parameter")
Rx_power = _cls("3DANTS.communication_channel.rx_power_calc.Rx_power")
Satellite_Fading_channel = _cls("3DANTS.communication_channel.satellite_fading_channel.Satellite_Fading_channel")
Air_Fading_channel = _cls("3DANTS.communication_channel.air_2_ground_fading.Air_Fading_channel")
ShadowingFading = _cls("3DANTS.communication_channel.shadowing_temporally_correlated_AR.ShadowingFading")
Uav_trajectory = _cls("3DANTS.position_and_mobility.uav.Uav_trajectory")

_analysis = importlib.import_module("3DANTS.analysis")
compute_simultaneous_visibility = _analysis.compute_simultaneous_visibility
visibility_summary = _analysis.visibility_summary
classify_interference = _analysis.classify_interference
detect_interference = _analysis.detect_interference
build_traffic_models = _analysis.build_traffic_models
ComponentRegistry = _analysis.ComponentRegistry


@dataclass
class SimulationConfig:
    """All configurable parameters for a 3DANTS network-with-traffic run.

    Defaults mirror the original ``3D_network_with_traffic.py`` example so
    that behaviour is preserved unless explicitly overridden.
    """

    # Reproducibility
    seed: int = 42

    # Constellation
    h_leo: float = 600e3
    inclination: int = 60
    num_sat: int = 120
    num_planes: int = 10
    phasing: int = 1
    r_E: float = 6371e3
    gm: float = 3.986004418e14
    h_GEO: float = 20000e3

    # Transmission
    f: float = 2.0e9
    A_z: float = 1 * 10 ** (-1)
    G_max_Rx: float = 4.0
    noise_figure_db: float = 7.0
    temperature_k: float = 25 + 273.15

    # Ground station
    gs_lat: float = 53.110987
    gs_lon: float = 8.851239

    # Time window (UTC)
    time_start: Tuple[int, int, int, int, int, int] = (2022, 9, 22, 0, 0, 0)
    time_end: Tuple[int, int, int, int, int, int] = (2022, 9, 22, 18, 0, 0)

    # HAPS
    haps_height: float = 10.0
    haps_velocity: float = 25.0
    haps_radius: float = 6.0
    haps_P_tx: float = 6.0
    haps_G_tx: float = 8 + 10 * np.log10(16)
    haps_gen_intervals: int = 3
    haps_fading_samples: int = 3000
    haps_fading_samples_rician: int = 300
    haps_shadowing_interval: int = 10
    haps_shadowing_tau: int = 30

    # Terrestrial network
    terrestrial_radius: float = 20.0
    ppp_lambda: int = 10
    radius_per_bs: int = 10
    num_base_stations: int = 3
    uav_height: float = 0.1
    uav_velocity: float = 18.0
    bs_height: float = 35.0
    bs_P_tx: int = 16
    bs_G_tx: float = 8 + 10 * np.log10(16)
    bs_gen_intervals: int = 10

    # Fading / shadowing
    fading_batch_size: int = 10000
    fading_N: int = 256
    fading_fs_initial: int = 10000
    fading_mode: str = "full"
    shadowing_num_samples: int = 10000
    satellite_user_radius: float = 5.0
    haps_user_radius: float = 10.0

    # Traffic
    haps_rate: int = 10
    bs_rates: Tuple[int, ...] = (10, 8, 5)

    # Execution flags
    steps: Optional[int] = None
    plot: bool = False
    verbose: bool = False


@dataclass
class SimulationResults:
    """Container for the five DataFrames produced by a run."""

    sat_position: pd.DataFrame
    sat_orbital_params: pd.DataFrame
    satellite_channel_time_series: pd.DataFrame
    p_rx: pd.DataFrame
    interference: pd.DataFrame
    visibility: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    config: SimulationConfig = None


class SimLayer(ABC):
    """Base class for simulation layers.

    A layer has three hooks:

    * :meth:`configure` is called once per satellite pass. On the first pass
      it delegates to :meth:`_configure` for once-only resource construction
      (guarded by an internal ``_built`` flag so later calls are cheap); it
      then delegates to :meth:`_configure_pass` for per-pass setup.
    * :meth:`begin_pass` / :meth:`end_pass` are called around the inner
      millisecond loop; the default implementations are no-ops.
    * :meth:`step` is called once per simulation millisecond and returns a
      dictionary fragment that is merged into the step context.

    Layers may store per-pass/per-run mutable state on ``self``; the shared
    pass context is stored on the ``NetworkSimulation`` instance.
    """

    name: str = "layer"

    def configure(self, sim: "NetworkSimulation") -> None:
        if not getattr(self, "_built", False):
            self._built = True
            self._configure(sim)
        self._configure_pass(sim)

    def _configure(self, sim: "NetworkSimulation") -> None:
        self.sim = sim

    def _configure_pass(self, sim: "NetworkSimulation") -> None:
        pass

    def begin_pass(self, sim: "NetworkSimulation") -> None:
        pass

    def end_pass(self, sim: "NetworkSimulation") -> None:
        pass

    def step(self, ctx: SimpleNamespace) -> Dict[str, Any]:
        return {}


class GeometryLayer(SimLayer):
    name = "geometry"

    def _configure(self, sim: "NetworkSimulation") -> None:
        super()._configure(sim)
        cfg = sim.cfg

        # Satellite transmission parameters (3GPP TR 38.811 / TR 38.821)
        params = Satellite_communication_parameter().parameters(cfg.f, "S", "DL")
        (cfg.satellite_EIRP_density, cfg.satellite_Tx_max_Gain,
         cfg.satellite_3dB_beamwidth, cfg.satellite_beam_diameter,
         cfg.max_Bandwidth_per_beam) = params
        cfg.satellite_EIRP_total = 10 * np.log10((10 ** (cfg.satellite_EIRP_density / 10)) * cfg.max_Bandwidth_per_beam)

        # Constellation
        self.LG = LEO_GEO(cfg.r_E, cfg.gm, cfg.h_GEO)
        self.LEOs = self.LG.walkerConstellation(
            cfg.h_leo, cfg.inclination, cfg.num_sat, cfg.num_planes, cfg.phasing, name="Sat")
        self.ts = sf.load.timescale()
        self.time1 = self.ts.utc(*cfg.time_start)
        self.time2 = self.ts.utc(*cfg.time_end)
        self.groundstation = wgs84.latlon(cfg.gs_lat, cfg.gs_lon)

        # Ground grid / beam cell
        self.hex_grid = HexagonGrid(cfg.gs_lat, cfg.gs_lon, cfg.satellite_beam_diameter / 2)
        self.satellite_cell_vertices = self.hex_grid.get_vertices()
        self.satellite_cell_vertices_in_wgs84 = self.hex_grid.convert_vertices_to_wgs84(self.satellite_cell_vertices)

        # User locations
        self.User_sat_initial_location = self.hex_grid.Point_initial_location_generation(cfg.gs_lat, cfg.gs_lon, cfg.satellite_user_radius)
        self.HAPS_initial_location = self.hex_grid.Point_initial_location_generation(cfg.gs_lat, cfg.gs_lon, cfg.haps_user_radius)

        # Visibility
        self.DF = self.LG.simulateConstellation(self.LEOs, self.groundstation, 20, self.time1, self.time2, ts=None, safetyMargin=0)
        self.DF2 = self.DF.reset_index()
        sim._df2 = self.DF2
        sim._lg = self.LG
        sim._leos = self.LEOs
        sim._ts = self.ts
        sim._groundstation = self.groundstation
        sim._hex_grid = self.hex_grid
        sim._satellite_cell_vertices = self.satellite_cell_vertices
        sim._satellite_cell_vertices_in_wgs84 = self.satellite_cell_vertices_in_wgs84
        sim._user_sat_initial_location = self.User_sat_initial_location
        sim._haps_initial_location = self.HAPS_initial_location
        sim._time1 = self.time1
        sim._time2 = self.time2

        if cfg.plot:
            try:
                self.hex_grid.plot_hexagon()
            except Exception:
                pass

    def _configure_pass(self, sim: "NetworkSimulation") -> None:
        sim = sim
        cfg = sim.cfg
        i = sim._pass_index
        df2 = sim._df2
        row = df2.iloc[i]
        sim._sat_id = row.iloc[0]
        sim._sat_id_int = int(sim._sat_id[3:])
        t_rise = row.iloc[1]
        t_set = row.iloc[2]
        sim._t_rise_now = sim._ts.utc(t_rise.year, t_rise.month, t_rise.day, t_rise.hour, t_rise.minute, t_rise.second)
        sim._t_set_now = sim._ts.utc(t_set.year, t_set.month, t_set.day, t_set.hour, t_set.minute, t_set.second)

        # Initial geometry
        time_now = sim._t_rise_now
        position_LEO = sim._leos[sim._sat_id_int - 1].at(time_now)
        sim._elev0 = sim._lg.elevation_angel_calculator(position_LEO.xyz.km, sim._groundstation.at(time_now).position.km)
        time_later = sim._t_rise_now + datetime.timedelta(seconds=1)
        position_later = sim._leos[sim._sat_id_int - 1].at(time_later)
        elev1 = sim._lg.elevation_angel_calculator(position_later.xyz.km, sim._groundstation.at(time_later).position.km)
        rate = (elev1 - sim._elev0) / 1
        sim._initial_tau = 10.0
        if abs(rate) > 0.001:
            sim._initial_tau = 1 / abs(rate)

        sim._visibility_sec = sim._lg.difference_time_in_seconds(sim._t_rise_now, sim._t_set_now)
        sim._visibility_millisec = sim._visibility_sec * 1000

        # Serving-satellite selection (visible satellites at t_rise_now)
        visible_sats = []
        max_elevation = -90.0
        serving_sat_id = None
        for j in range(len(df2)):
            other_sat_id = df2.iloc[j, 0]
            other_t_rise_pd = df2.iloc[j, 1]
            other_t_set_pd = df2.iloc[j, 2]
            other_t_rise_dt = other_t_rise_pd.to_pydatetime()
            other_t_set_dt = other_t_set_pd.to_pydatetime()
            other_t_rise_sky = sim._ts.utc(other_t_rise_dt.year, other_t_rise_dt.month, other_t_rise_dt.day, other_t_rise_dt.hour, other_t_rise_dt.minute, other_t_rise_dt.second)
            other_t_set_sky = sim._ts.utc(other_t_set_dt.year, other_t_set_dt.month, other_t_set_dt.day, other_t_set_dt.hour, other_t_set_dt.minute, other_t_set_dt.second)
            if other_t_rise_sky.utc_datetime() <= sim._t_rise_now.utc_datetime():
                if sim._t_rise_now.utc_datetime() <= other_t_set_sky.utc_datetime():
                    other_sat_id_int = int(other_sat_id[3:])
                    other_pos = sim._leos[other_sat_id_int - 1].at(sim._t_rise_now)
                    elevation = sim._lg.elevation_angel_calculator(other_pos.xyz.km, sim._groundstation.at(sim._t_rise_now).position.km)
                    visible_sats.append((other_sat_id, other_sat_id_int, other_pos, elevation))
                    if elevation > max_elevation:
                        max_elevation = elevation
                        serving_sat_id = other_sat_id
        sim._serving_sat_id = serving_sat_id
        if sim.cfg.verbose:
            print(f"\nPass {i}: {sim._sat_id} visible sats={len(visible_sats)} serving={serving_sat_id}")

    def step(self, ctx: SimpleNamespace) -> Dict[str, Any]:
        sim = self.sim
        cfg = sim.cfg
        i1 = ctx.i1
        time_now = sim._t_rise_now + datetime.timedelta(microseconds=i1 * 1000)
        satellite_cell_vertice_at_time_now = sim._satellite_cell_vertices_in_wgs84.at(time_now)
        satellite_cell_vertice_positions = satellite_cell_vertice_at_time_now.position.km
        position_LEO = sim._leos[sim._sat_id_int - 1].at(time_now)
        LEO_velocity = sim._leos[sim._sat_id_int - 1].at(time_now).velocity
        LEO_velocity_km_per_sec = LEO_velocity.km_per_s
        line_of_sight_vector_from_GS_to_satellite = sim._groundstation.at(time_now).position.km - position_LEO.xyz.km
        r_hat = line_of_sight_vector_from_GS_to_satellite / np.linalg.norm(line_of_sight_vector_from_GS_to_satellite)
        v_LOS = np.dot(LEO_velocity_km_per_sec, r_hat)

        if cfg.verbose:
            print('satellite global position vector is:', position_LEO.xyz.km)
            print('satellite velocity in global coordinate vector is:', LEO_velocity_km_per_sec)

        # Orbital elements (rotation matrix approach)
        mu = 398600.4418
        h = np.cross(position_LEO.xyz.km, LEO_velocity_km_per_sec)
        h_norm = np.linalg.norm(h)
        inc_angle = np.arccos(h[2] / h_norm)
        n = np.array([-h[1], h[0], 0])
        n_norm = np.linalg.norm(n)
        Omega = np.arctan2(n[1], n[0])
        r_norm = np.linalg.norm(position_LEO.xyz.km)
        e = (np.cross(LEO_velocity_km_per_sec, h) / mu) - (position_LEO.xyz.km / r_norm)
        e_norm = np.linalg.norm(e)
        omega = np.arccos(np.dot(n, e) / (n_norm * e_norm))
        if e[2] < 0:
            omega = 2 * np.pi - omega
        if cfg.verbose:
            print(f"Inclination (inc_angle): {np.degrees(inc_angle):.2f} degrees")
            print(f"RAAN (Omega): {np.degrees(Omega):.2f} degrees")
            print(f"Argument of Perigee (omega): {np.degrees(omega):.2f} degrees")
        cos_Omega = np.cos(Omega)
        sin_Omega = np.sin(Omega)
        cos_i = np.cos(inc_angle)
        sin_i = np.sin(inc_angle)
        cos_omega = np.cos(omega)
        sin_omega = np.sin(omega)
        R_global_to_local = np.array([
            [cos_omega * cos_Omega - sin_omega * cos_i * sin_Omega,
             -cos_omega * sin_Omega - sin_omega * cos_i * cos_Omega,
             sin_omega * sin_i],
            [sin_omega * cos_Omega + cos_omega * cos_i * sin_Omega,
             -sin_omega * sin_Omega + cos_omega * cos_i * cos_Omega,
             -cos_omega * sin_i],
            [sin_i * sin_Omega, sin_i * cos_Omega, cos_i],
        ])
        if cfg.verbose:
            print("R_global_to_local:")
            print(R_global_to_local)
        R_local_to_global = R_global_to_local.T
        LEO_position_local = R_local_to_global @ position_LEO.xyz.km
        if cfg.verbose:
            print("LEO position in Local coordinate frame vector:", LEO_position_local)
        r_vsat_LEO_global = sim._groundstation.at(time_now).position.km - position_LEO.xyz.km
        r_vsat_LEO_local = R_local_to_global @ r_vsat_LEO_global
        r_vsat_LEO_local_norm = np.linalg.norm(r_vsat_LEO_local)
        r_x_local, r_y_local, r_z_local = r_vsat_LEO_local
        Theta_el_sat_see_vsat = np.arcsin(r_z_local / r_vsat_LEO_local_norm)
        Theta_az_sat_see_vsat = np.arctan2(r_y_local, r_x_local)
        if cfg.verbose:
            print(f"Relative position of VSAT to LEO in satellite local frame: {r_vsat_LEO_local}")
            print(f"Elevation angle (Theta_el): {np.degrees(Theta_el_sat_see_vsat):.2f} degrees")
            print(f"Azimuth angle (Theta_az): {np.degrees(Theta_az_sat_see_vsat):.2f} degrees")

        # ECEF -> ENU for VSAT->sat angles
        gs_pos_ecef = sim._groundstation.at(time_now).position.km
        gs_lat = sim._groundstation.latitude.radians
        gs_lon = sim._groundstation.longitude.radians
        R_ecef_to_enu = np.array([
            [-np.sin(gs_lon), np.cos(gs_lon), 0],
            [-np.sin(gs_lat) * np.cos(gs_lon), -np.sin(gs_lat) * np.sin(gs_lon), np.cos(gs_lat)],
            [np.cos(gs_lat) * np.cos(gs_lon), np.cos(gs_lat) * np.sin(gs_lon), np.sin(gs_lat)],
        ])
        r_gs_to_sat = position_LEO.xyz.km - gs_pos_ecef
        r_gs_to_sat_enu = R_ecef_to_enu @ r_gs_to_sat
        r_enu_norm = np.linalg.norm(r_gs_to_sat_enu)
        east, north, up = r_gs_to_sat_enu
        theta_el_vsat_see_sat = np.arcsin(up / r_enu_norm)
        theta_az_vsat_see_sat = np.arctan2(east, north)
        if cfg.verbose:
            print(f"Relative position of LEO to VSAT in global frame: {r_gs_to_sat_enu}")
            print(f"Elevation angle (theta_el): {np.degrees(theta_el_vsat_see_sat):.2f} degrees")
            print(f"Azimuth angle (theta_az): {np.degrees(theta_az_vsat_see_sat):.2f} degrees")

        position_GS = sim._groundstation.at(time_now).position.km


        User_satellite_initial_loc = sim._user_sat_initial_location.at(time_now).position.km
        distance_GS_sat = sim._lg.distance(sim._groundstation.at(time_now).position.km, position_LEO.xyz.km)
        elevation_angle = sim._lg.elevation_angel_calculator(position_LEO.xyz.km, sim._groundstation.at(time_now).position.km)
        lOS_prob = Rx_power().LOS_prob_calc(elevation_angle, 'Sub_Urban')

        return {
            "time_now": time_now,
            "satellite_cell_vertice_positions": satellite_cell_vertice_positions,
            "position_LEO": position_LEO,
            "LEO_velocity_km_per_sec": LEO_velocity_km_per_sec,
            "v_LOS": v_LOS,
            "distance_GS_sat": distance_GS_sat,
            "elevation_angle": elevation_angle,
            "Theta_el_sat_see_vsat": Theta_el_sat_see_vsat,
            "Theta_az_sat_see_vsat": Theta_az_sat_see_vsat,
            "theta_el_vsat_see_sat": theta_el_vsat_see_sat,
            "theta_az_vsat_see_sat": theta_az_vsat_see_sat,
            "position_GS": position_GS,
            "lOS_prob": lOS_prob,

            "User_satellite_initial_loc": User_satellite_initial_loc,
        }


class FadingLayer(SimLayer):
    name = "fading"

    def _configure(self, sim: "NetworkSimulation") -> None:
        super()._configure(sim)
        cfg = sim.cfg
        # Three Doppler options (only 'full' is used in the loop; all are
        # constructed in order to preserve the original RNG consumption).
        number_samples_nakagami = cfg.fading_batch_size
        num_samples_rician = cfg.fading_batch_size // 10
        fs_initial = cfg.fading_fs_initial
        N = cfg.fading_N
        self._channel_compensated = Satellite_Fading_channel(
            number_samples_nakagami, num_samples_rician, fs_initial, N,
            doppler_mode='compensated', v_residual_mps=1.5)
        self._channel_scaled = Satellite_Fading_channel(
            number_samples_nakagami, num_samples_rician, fs_initial, N,
            doppler_mode='scaled', Tc_target_s=0.05, fc_ref=2.5e9)
        self._channel = Satellite_Fading_channel(
            number_samples_nakagami, num_samples_rician, fs_initial, N,
            doppler_mode=cfg.fading_mode)
        sim._fading_channel = self._channel
        sim._fading_fs_initial = fs_initial

    def _configure_pass(self, sim: "NetworkSimulation") -> None:
        sim = sim
        cfg = sim.cfg
        sim_channel = sim._fading_channel
        self._last_regen_el_small = sim._elev0
        LEO_velocity = sim._leos[sim._sat_id_int - 1].at(sim._t_rise_now).velocity
        LEO_velocity_km_per_sec = LEO_velocity.km_per_s
        line_of_sight_vector_from_GS_to_satellite = sim._groundstation.at(sim._t_rise_now).position.km - sim._leos[sim._sat_id_int - 1].at(sim._t_rise_now).xyz.km
        r_hat = line_of_sight_vector_from_GS_to_satellite / np.linalg.norm(line_of_sight_vector_from_GS_to_satellite)
        v_LOS = np.dot(LEO_velocity_km_per_sec, r_hat)
        distance_GS_sat = sim._lg.distance(sim._groundstation.at(sim._t_rise_now).position.km, sim._leos[sim._sat_id_int - 1].at(sim._t_rise_now).xyz.km)
        self._batch = sim_channel.run_simulation(sim._elev0, v_LOS, cfg.f, distance_GS_sat)
        self._small_idx = 0
        self._v_los = v_LOS
        self._distance = distance_GS_sat
        sim._init_v_los = v_LOS
        sim._init_distance = distance_GS_sat

    def step(self, ctx: SimpleNamespace) -> Dict[str, Any]:
        sim = self.sim
        cfg = sim.cfg
        elevation_angle = ctx.elevation_angle
        if abs(elevation_angle - self._last_regen_el_small) >= 1:
            self._last_regen_el_small = elevation_angle
            distance_GS_sat = sim._lg.distance(sim._groundstation.at(ctx.time_now).position.km, ctx.position_LEO.xyz.km)
            line_of_sight_vector = ctx.position_LEO.xyz.km - sim._groundstation.at(ctx.time_now).position.km
            r_hat = line_of_sight_vector / np.linalg.norm(line_of_sight_vector)
            v_LOS = np.dot(ctx.LEO_velocity_km_per_sec, r_hat)
            self._batch = sim._fading_channel.run_simulation(elevation_angle, v_LOS, cfg.f, distance_GS_sat)
            self._small_idx = 0
            self._v_los = v_LOS
            self._distance = distance_GS_sat
        if self._small_idx >= len(self._batch):
            self._batch = sim._fading_channel.run_simulation(elevation_angle, self._v_los, cfg.f, self._distance)
            self._small_idx = 0
        Satellite_Channel_fading_samples = self._batch[self._small_idx]
        self._small_idx += 1
        return {
            "Satellite_Channel_fading_samples": Satellite_Channel_fading_samples,
            "v_LOS": self._v_los,
            "distance_GS_sat": self._distance,
        }
class ShadowingLayer(SimLayer):
    name = "shadowing"

    def _configure(self, sim: "NetworkSimulation") -> None:
        super()._configure(sim)
        sim._large_scale_shadowing_num_samples = 10000

    def _configure_pass(self, sim: "NetworkSimulation") -> None:
        sim = sim
        self._last_regen_el = sim._elev0
        self._last_regen_time = sim._t_rise_now
        self._shadowing = ShadowingFading(tau=sim._initial_tau, N=sim._large_scale_shadowing_num_samples)
        self._shadowing_interval = self._shadowing.SF_LOS_calc(sim._elev0, 'LOS', 'SBand')
        self._shadowing_idx = 0

    def step(self, ctx: SimpleNamespace) -> Dict[str, Any]:
        sim = self.sim
        elevation_angle = ctx.elevation_angle
        if abs(elevation_angle - self._last_regen_el) >= 5:
            delta_time = (ctx.time_now - self._last_regen_time).total_seconds()
            tau = sim._initial_tau
            if delta_time > 0:
                tau = delta_time / 5
            self._last_regen_time = ctx.time_now
            self._last_regen_el = elevation_angle
            self._shadowing = ShadowingFading(tau=tau, N=sim._large_scale_shadowing_num_samples)
            self._shadowing_interval = self._shadowing.SF_LOS_calc(elevation_angle, 'LOS', 'SBand')
            self._shadowing_idx = 0
        if self._shadowing_idx >= len(self._shadowing_interval):
            self._shadowing_interval = self._shadowing.SF_LOS_calc(elevation_angle, 'LOS', 'SBand')
            self._shadowing_idx = 0
        Satellite_Shadowing_samples = self._shadowing_interval[self._shadowing_idx]
        self._shadowing_idx += 1
        return {"Satellite_Shadowing_samples": Satellite_Shadowing_samples}


class TrafficLayer(SimLayer):
    name = "traffic"

    def _configure(self, sim: "NetworkSimulation") -> None:
        super()._configure(sim)
        seconds_difference_time = sim._lg.difference_time_in_seconds(sim._time1, sim._time2)
        sim._traffic_models = build_traffic_models(
            seconds_difference_time, sim.cfg.num_sat,
            haps_rate=sim.cfg.haps_rate, bs_rates=sim.cfg.bs_rates)

    def _configure_pass(self, sim: "NetworkSimulation") -> None:
        pass

    def step(self, ctx: SimpleNamespace) -> Dict[str, Any]:
        sim = self.sim
        satellite_packets = sim._traffic_models[sim._sat_id].get_packets_at_time(ctx.i1, time_window=0.001)
        return {"satellite_packets": satellite_packets}


class HAPSLayer(SimLayer):
    name = "haps"

    def _configure(self, sim: "NetworkSimulation") -> None:
        super()._configure(sim)
        cfg = sim.cfg
        sim._haps1 = HAPS_trajectory(cfg.haps_velocity, cfg.haps_radius, time_interval=1)
        sim._angular_haps, sim._number_step_haps = sim._haps1.get_values()
        sim._shiftak0_haps = 0
        sim._haps_fading = Air_Fading_channel(
            cfg.haps_fading_samples, cfg.haps_fading_samples_rician, cfg.fading_fs_initial, cfg.fading_N)
        sim._haps_shadowing = ShadowingFading(
            tau=cfg.haps_shadowing_tau, N=cfg.haps_shadowing_interval * 1000)
        sim._haps_channel_interval = None
        sim._haps_shadowing_interval = None

    def _configure_pass(self, sim: "NetworkSimulation") -> None:
        pass

    def step(self, ctx: SimpleNamespace) -> Dict[str, Any]:
        sim = self.sim
        cfg = sim.cfg
        shiftak_haps = (ctx.i1 + sim._shiftak0_haps) % sim._number_step_haps
        step_haps = shiftak_haps + 1
        HAPS1_initial_loc = sim._haps_initial_location.at(ctx.time_now).position.km
        HAPS1_position = sim._haps1.simulate_circular_trajectory(HAPS1_initial_loc, 10, step_haps, ctx.position_GS)
        elevation_angle_User_sat_HAPS = 90 - sim._lg.elevation_angel_calculator(HAPS1_position[0, :3].flatten(), ctx.User_satellite_initial_loc)
        distance_User_sat_to_HAPS = sim._lg.distance(HAPS1_position[0, :3].flatten(), ctx.User_satellite_initial_loc)
        if ctx.i1 % cfg.haps_gen_intervals * 1000 == 0:
            if cfg.verbose:
                print(f"Generating HAPS channel samples at i={sim._pass_index}, i1={ctx.i1}")
            sim._haps_channel_interval = sim._haps_fading.run_simulation(elevation_angle_User_sat_HAPS, cfg.haps_velocity, cfg.f, distance_User_sat_to_HAPS)
        if ctx.i1 % cfg.haps_shadowing_interval * 1000 == 0:
            sim._haps_shadowing_interval = sim._haps_shadowing.SF_LOS_calc(elevation_angle_User_sat_HAPS, 'LOS', 'SBand')
            if cfg.verbose:
                print(f"Generating LS shadowing samples at i={sim._pass_index}, i1={ctx.i1}")
        HAPS_start_idx_small_scale_fading = ctx.i1 % cfg.haps_gen_intervals * 1000
        HAPS_end_idx_small_scale_fading = HAPS_start_idx_small_scale_fading + 1
        if HAPS_end_idx_small_scale_fading <= len(sim._haps_channel_interval):
            HAPS_Channel_fading_samples = sim._haps_channel_interval[HAPS_start_idx_small_scale_fading:HAPS_end_idx_small_scale_fading]
        else:
            if cfg.verbose:
                print(f"Index out of range at i={sim._pass_index}, i1={ctx.i1}")
            HAPS_Channel_fading_samples = 0
        HAPS_start_idx_large_scale_fading = ctx.i1 % cfg.haps_shadowing_interval * 1000
        HAPS_end_idx_large_scale_fading = HAPS_start_idx_large_scale_fading + 1
        if HAPS_end_idx_large_scale_fading <= len(sim._haps_shadowing_interval):
            HAPS_Shadowing_samples = sim._haps_shadowing_interval[HAPS_start_idx_large_scale_fading:HAPS_end_idx_large_scale_fading]
        else:
            if cfg.verbose:
                print(f"Index out of range at i={sim._pass_index}, i1={ctx.i1}")
            HAPS_Shadowing_samples = 0
        fspl_HAPS_User_satellite = Rx_power().FSPl_only(cfg.f, distance_User_sat_to_HAPS)
        haps_packets = sim._traffic_models['HAPS'].get_packets_at_time(ctx.i1, time_window=0.001)
        haps_rx_power = 0
        if haps_packets:
            for packet_size in haps_packets:
                interference_power = (cfg.haps_P_tx + cfg.haps_G_tx + 20 * np.log10(np.abs(HAPS_Channel_fading_samples))) - fspl_HAPS_User_satellite - HAPS_Shadowing_samples
                haps_rx_power += 10 ** (interference_power / 10)
        sim._shiftak0_haps = (sim._shiftak0_haps + sim._visibility_sec) % sim._number_step_haps
        return {
            "HAPS1_position": HAPS1_position,
            "hips_rx_power": haps_rx_power,
            "BaseStation_positions_time_now": None,
        }


class BaseStationLayer(SimLayer):
    name = "base_station"

    def _configure(self, sim: "NetworkSimulation") -> None:
        super()._configure(sim)
        cfg = sim.cfg
        sim._terrestrial = terresterial_network(cfg.f, 'Sub_Urban')
        center_x, center_y, center_z = sim._groundstation.itrs_xyz.km
        sim._bs_pos0 = sim._terrestrial.generate_base_station_positions(
            center_x, center_y, cfg.terrestrial_radius, cfg.num_base_stations, center_z, cfg.radius_per_bs, 1000)
        sim._bs_latlon = sim._terrestrial.cartesian_to_latlon(np.array([sim._bs_pos0]).reshape(-1, 3))
        sim._bs_latlon = np.array([sim._bs_latlon]).reshape(-1, 2)
        sim._bs_skyfield_positions = sim._terrestrial.skyfield_position_for_BaseStations(sim._bs_latlon)
        sim._rician_bs = None

    def _configure_pass(self, sim: "NetworkSimulation") -> None:
        pass

    def step(self, ctx: SimpleNamespace) -> Dict[str, Any]:
        sim = self.sim
        cfg = sim.cfg
        BaseStation_positions_time_now = sim._terrestrial.get_base_station_positions_at_time_now(ctx.time_now, sim._bs_skyfield_positions, cfg.bs_height)
        bs_interference = [0, 0, 0]
        bs1_packets = sim._traffic_models['BS1'].get_packets_at_time(ctx.i1, time_window=0.001)
        bs2_packets = sim._traffic_models['BS2'].get_packets_at_time(ctx.i1, time_window=0.001)
        bs3_packets = sim._traffic_models['BS3'].get_packets_at_time(ctx.i1, time_window=0.001)
        for iii, bs_pos in enumerate(BaseStation_positions_time_now):
            distance_user_to_bs = sim._lg.distance(bs_pos, ctx.User_satellite_initial_loc)
            Pathloss_bs_User_LoS, Pathloss_bs_User_nLoS = sim._terrestrial.pathloss_calculator_up_to_7GHz(ctx.User_satellite_initial_loc, bs_pos, 35, 1.5)
            Pathloss_bs_User = max(Pathloss_bs_User_LoS, Pathloss_bs_User_nLoS)
            if ctx.i1 % cfg.bs_gen_intervals * 1000 == 0:
                if cfg.verbose:
                    print(f"Generating BS channel samples at i={sim._pass_index}, i1={ctx.i1}")
                sim._rician_bs = sim._terrestrial.rician_fading_accurate(10000, 1, cfg.fading_fs_initial, 10, np.pi / 4)
            BSs_start_idx_small_scale_fading = ctx.i1 % (cfg.bs_gen_intervals * 1000)
            BSs_end_idx_small_scale_fading = BSs_start_idx_small_scale_fading + 1
            if BSs_end_idx_small_scale_fading <= len(sim._rician_bs):
                Rician_channel_bs_to_User_samples = sim._rician_bs[BSs_start_idx_small_scale_fading:BSs_end_idx_small_scale_fading]
            else:
                if cfg.verbose:
                    print(f"Index out of range at i={sim._pass_index}, i1={ctx.i1}")
                Rician_channel_bs_to_User_samples = [0]
            if iii == 0 and bs1_packets:
                for packet_size in bs1_packets:
                    interference_power = (cfg.bs_P_tx + cfg.bs_G_tx + 20 * np.log10(np.abs(Rician_channel_bs_to_User_samples))) - Pathloss_bs_User
                    bs_interference[iii] += 10 ** (interference_power / 10)
            if iii == 1 and bs2_packets:
                for packet_size in bs2_packets:
                    interference_power = (cfg.bs_P_tx + cfg.bs_G_tx + 20 * np.log10(np.abs(Rician_channel_bs_to_User_samples))) - Pathloss_bs_User
                    bs_interference[iii] += 10 ** (interference_power / 10)
            if iii == 2 and bs3_packets:
                for packet_size in bs3_packets:
                    interference_power = (cfg.bs_P_tx + cfg.bs_G_tx + 20 * np.log10(np.abs(Rician_channel_bs_to_User_samples))) - Pathloss_bs_User
                    bs_interference[iii] += 10 ** (interference_power / 10)
        return {
            "BaseStation_positions_time_now": BaseStation_positions_time_now,
            "bs_interference": bs_interference,
        }


class InterferenceLayer(SimLayer):
    name = "interference"

    def step(self, ctx: SimpleNamespace) -> Dict[str, Any]:
        sim = self.sim
        cfg = sim.cfg
        fspl_solo = Rx_power().FSPl_only(cfg.f, ctx.distance_GS_sat)
        atmospheric_loss = Rx_power().atmospheric_att(cfg.A_z, ctx.elevation_angle)
        P_received_fspl_ShF_SSF = (cfg.satellite_EIRP_total + cfg.G_max_Rx + 20 * np.log10(np.abs(ctx.Satellite_Channel_fading_samples))) - fspl_solo - atmospheric_loss - ctx.Satellite_Shadowing_samples
        User_satellite_initial_loc = sim._user_sat_initial_location.at(ctx.time_now).position.km
        distance_User_sat_center_beam = sim._lg.distance(sim._groundstation.at(ctx.time_now).position.km, User_satellite_initial_loc)
        P_rx_User_sat = P_received_fspl_ShF_SSF - 10 * 2 * np.log10(1 - distance_User_sat_center_beam / cfg.satellite_beam_diameter / 2)
        Noise_power = Rx_power().Noise_power_with_NoiseFigure(cfg.noise_figure_db, cfg.max_Bandwidth_per_beam, cfg.temperature_k)
        SINR = (10 ** (P_rx_User_sat / 10)) / (10 ** (Noise_power / 10) + ctx.hips_rx_power + ctx.bs_interference[0] + ctx.bs_interference[1] + ctx.bs_interference[2])
        return {
            "fspl_solo": fspl_solo,
            "atmospheric_loss": atmospheric_loss,
            "P_received_fspl_ShF_SSF": P_received_fspl_ShF_SSF,
            "P_rx_User_sat": P_rx_User_sat,
            "Noise_power": Noise_power,
            "SINR": SINR,
            "User_satellite_initial_loc": User_satellite_initial_loc,
            "distance_User_sat_center_beam": distance_User_sat_center_beam,
        }
class NetworkSimulation:
    """Fluent, layer-based orchestrator for the 3DANTS network-with-traffic simulation.

    Configuration is supplied via :class:`SimulationConfig`. The simulation
    loop is generic: it merely configures each layer and calls ``step`` per
    millisecond, merging the returned fragments. Adding a new feature means
    writing a new :class:`SimLayer` and registering it with :meth:`add_layer`
    — the loop itself is not modified.
    """

    DEFAULT_LAYER_ORDER = [
        "geometry",
        "fading",
        "shadowing",
        "traffic",
        "haps",
        "base_station",
        "interference",
    ]

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.cfg = config or SimulationConfig()
        self.registry = ComponentRegistry()
        self.registry.register("geometry", GeometryLayer)
        self.registry.register("fading", FadingLayer)
        self.registry.register("shadowing", ShadowingLayer)
        self.registry.register("traffic", TrafficLayer)
        self.registry.register("haps", HAPSLayer)
        self.registry.register("base_station", BaseStationLayer)
        self.registry.register("interference", InterferenceLayer)
        self.layers: List[SimLayer] = [
            self.registry.get(name)() for name in self.DEFAULT_LAYER_ORDER
        ]
        self.results: Optional[SimulationResults] = None
        self._rows_sat_position: List[dict] = []
        self._rows_orbital: List[dict] = []
        self._rows_channel: List[dict] = []
        self._rows_p_rx: List[dict] = []
        self._rows_interference: List[dict] = []
        self._visibility_df: pd.DataFrame = pd.DataFrame()
        self._last_ctx: Optional[SimpleNamespace] = None

    # ------------------------------------------------------------------ #
    # Fluent configuration
    # ------------------------------------------------------------------ #
    def with_constellation(self, h_leo=None, num_sat=None, num_planes=None, inclination=None) -> "NetworkSimulation":
        if h_leo is not None:
            self.cfg.h_leo = h_leo
        if num_sat is not None:
            self.cfg.num_sat = num_sat
        if num_planes is not None:
            self.cfg.num_planes = num_planes
        if inclination is not None:
            self.cfg.inclination = inclination
        return self

    def with_ground_station(self, lat=None, lon=None) -> "NetworkSimulation":
        if lat is not None:
            self.cfg.gs_lat = lat
        if lon is not None:
            self.cfg.gs_lon = lon
        return self

    def with_ground_grid(self) -> "NetworkSimulation":
        # The ground grid is derived from the satellite beam diameter in
        # GeometryLayer; this flag simply makes configuration explicit.
        return self

    def with_fading(self, mode: str = "full", fc: float = None) -> "NetworkSimulation":
        self.cfg.fading_mode = mode
        if fc is not None:
            self.cfg.f = fc
        return self

    def with_traffic(self, num_sat=None, haps_rate=None, bs_rates=None) -> "NetworkSimulation":
        if num_sat is not None:
            self.cfg.num_sat = num_sat
        if haps_rate is not None:
            self.cfg.haps_rate = haps_rate
        if bs_rates is not None:
            self.cfg.bs_rates = tuple(bs_rates)
        return self

    def with_haps(self, height=None, velocity=None) -> "NetworkSimulation":
        if height is not None:
            self.cfg.haps_height = height
        if velocity is not None:
            self.cfg.haps_velocity = velocity
        return self

    def with_base_stations(self, n: int = 3) -> "NetworkSimulation":
        self.cfg.num_base_stations = n
        return self

    def add_layer(self, layer: SimLayer) -> "NetworkSimulation":
        """Register a custom layer appended after the built-in layers."""
        layer.sim = self
        self.layers.append(layer)
        self.registry.register(layer.name, type(layer))
        return self

    def with_registry(self, registry: "ComponentRegistry") -> "NetworkSimulation":
        """Swap the component registry for a custom one."""
        self.registry = registry
        return self

    def with_uav(self, height=None, velocity=None) -> "NetworkSimulation":
        """Configure UAV interference parameters."""
        if height is not None:
            self.cfg.uav_height = height
        if velocity is not None:
            self.cfg.uav_velocity = velocity
        return self

    def _resolve_layer(self, name: str) -> SimLayer:
        """Instantiate a layer from the registry by name."""
        return self.registry.get(name)()

    # ------------------------------------------------------------------ #
    # Simulation lifecycle
    # ------------------------------------------------------------------ #
    def run(self) -> "NetworkSimulation":
        sim = self
        cfg = sim.cfg
        np.random.seed(cfg.seed)

        # Prime pass 0 so the constellation/visibility (DF2) is built, which
        # lets us know how many passes the simulation has.
        sim._pass_index = 0
        for layer in self.layers:
            layer.configure(sim)
        num_passes = cfg.steps if cfg.steps is not None else len(sim._df2)

        for i in range(num_passes):
            sim._pass_index = i
            for layer in self.layers:
                layer.configure(sim)
            for layer in self.layers:
                layer.begin_pass(sim)
            visibility_millisec = int(sim._visibility_millisec)
            for i1 in range(visibility_millisec):
                ctx = SimpleNamespace(i1=i1)
                for layer in self.layers:
                    frag = layer.step(ctx)
                    if frag:
                        ctx.__dict__.update(frag)
                self._record_row(ctx)
                self._last_ctx = ctx
                if cfg.verbose and (i1 % 1000 == 0):
                    print(i1)
            for layer in self.layers:
                layer.end_pass(sim)
            if cfg.verbose:
                print(i)

        self._build_results()
        return self


class UAVLayer(SimLayer):
    """UAV interference layer (extracted from the original Engine).

    Simulates a low-altitude UAV flying a circular trajectory around the
    ground station and computes the UAV-to-ground-station distance.
    The interference contribution can be extended by overriding ``step``.
    """
    name = "uav"

    def _configure(self, sim: "NetworkSimulation") -> None:
        super()._configure(sim)
        cfg = sim.cfg
        sim._uav = Uav_trajectory(cfg.uav_velocity, cfg.uav_height, time_interval=1)
        sim._angular_uav, sim._number_step_uav = sim._uav.get_values()
        sim._shiftak0_uav = 0

    def _configure_pass(self, sim: "NetworkSimulation") -> None:
        pass

    def step(self, ctx: SimpleNamespace) -> Dict[str, Any]:
        sim = self.sim
        cfg = sim.cfg
        shiftak_uav = (ctx.i1 + sim._shiftak0_uav) % sim._number_step_uav
        step_uav = shiftak_uav + 1
        uav_position = sim._uav.simulate_circular_trajectory(
            ctx.position_GS + np.array([0, 0, 0.1]),
            cfg.uav_height, step_uav, ctx.position_GS)
        distance_uav_to_gs = sim._lg.distance(
            uav_position[:, :3].flatten(), ctx.position_GS)
        return {
            "uav_position": uav_position,
            "distance_uav_to_gs": distance_uav_to_gs,
            "uav_rx_power": 0,
        }

    def _record_row(self, ctx: SimpleNamespace) -> None:
        sim = self
        cfg = sim.cfg
        t = ctx.time_now.utc_datetime()
        self._rows_sat_position.append({
            'Satellite ID': sim._sat_id,
            'Time': t,
            'Sat Position (km)': ctx.position_LEO.xyz.km,
            'GS Position (km)': ctx.position_GS,
            'Distance from Earth Surface (km)': np.linalg.norm(ctx.position_LEO.xyz.km) - cfg.r_E / 1000,
            'distance to GS (km)': ctx.distance_GS_sat,
            'Elevation Angle (degree)': ctx.elevation_angle,
            'satellite velocity (km)': ctx.LEO_velocity_km_per_sec,
            'v_LOS (km/s)': ctx.v_LOS,
        })
        self._rows_orbital.append({
            'Satellite ID': sim._sat_id,
            'Time': t,
            'Theta_el_sat_see_vsat': ctx.Theta_el_sat_see_vsat,
            'Theta_az_sat_see_vsat': ctx.Theta_az_sat_see_vsat,
            'theta_el_vsat_see_sat': ctx.theta_el_vsat_see_sat,
            'theta_az_vsat_see_sat': ctx.theta_az_vsat_see_sat,
        })
        self._rows_channel.append({
            'Satellite ID': sim._sat_id,
            'Time': t,
            'Elevation Angle (degree)': ctx.elevation_angle,
            'small scale fading-channel': ctx.Satellite_Channel_fading_samples,
            'large scale shadowing': ctx.Satellite_Shadowing_samples,
        })
        self._rows_p_rx.append({
            'Satellite ID': sim._sat_id,
            'Time': t,
            'Elevation Angle (degree)': ctx.elevation_angle,
            'Distance (km)': ctx.distance_GS_sat,
            'LoS Prob (%)': ctx.lOS_prob,
            'P_Rx_fspl_ShF_SSF (dBW)': ctx.P_received_fspl_ShF_SSF,
            'P_rx_at_User (dBW)': ctx.P_rx_User_sat,
            'SNR (dB)': ctx.P_rx_User_sat - ctx.Noise_power,
            'shadowedrician_ssf': ctx.Satellite_Channel_fading_samples,
            'shadowing_lsf': ctx.Satellite_Shadowing_samples,
        })
        self._rows_interference.append(self._assemble_interference_row(ctx))

    def _assemble_interference_row(self, ctx: SimpleNamespace) -> dict:
        sim = self
        return {
            'Satellite ID': sim._serving_sat_id if sim._serving_sat_id else sim._sat_id,
            'Time': ctx.time_now.utc_datetime(),
            'HAPS_rx': 10 * np.log10(ctx.hips_rx_power) if ctx.hips_rx_power > 0 else ctx.Noise_power,
            'BaseStation1_rx': 10 * np.log10(ctx.bs_interference[0]) if ctx.bs_interference[0] > 0 else ctx.Noise_power,
            'BaseStation2_rx': 10 * np.log10(ctx.bs_interference[1]) if ctx.bs_interference[1] > 0 else ctx.Noise_power,
            'BaseStation3_rx': 10 * np.log10(ctx.bs_interference[2]) if ctx.bs_interference[2] > 0 else ctx.Noise_power,
            'Satellite_rx': ctx.P_rx_User_sat if 10 ** (ctx.P_rx_User_sat / 10) > 0 else ctx.Noise_power,
            'SINR (dB)': 10 * np.log10(ctx.SINR),
        }

    def _build_results(self) -> None:
        sim = self
        try:
            sim._visibility_df = compute_simultaneous_visibility(
                sim._df2, sim._time1.utc_datetime(), sim._time2.utc_datetime()
            )
        except Exception:
            sim._visibility_df = pd.DataFrame()
        sim.results = SimulationResults(
            sat_position=pd.DataFrame(sim._rows_sat_position),
            sat_orbital_params=pd.DataFrame(sim._rows_orbital),
            satellite_channel_time_series=pd.DataFrame(sim._rows_channel),
            p_rx=pd.DataFrame(sim._rows_p_rx),
            interference=pd.DataFrame(sim._rows_interference),
            visibility=sim._visibility_df,
            config=sim.cfg,
        )


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="3DANTS network-with-traffic simulation"
    )
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--f", type=float, default=None)
    parser.add_argument("--haps-rate", type=int, default=None)
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    sim = NetworkSimulation(
        SimulationConfig(
            steps=args.steps,
            plot=args.plot,
            verbose=args.verbose,
        )
    )
    if args.f is not None:
        sim.with_fading(fc=args.f)
    if args.haps_rate is not None:
        sim.with_traffic(haps_rate=args.haps_rate)
    sim.run()
    if args.plot and sim.results is not None:
        try:
            summary = visibility_summary(sim._visibility_df)
            _analysis.plot_visibility_bars(summary)
            import matplotlib.pyplot as plt
            plt.show()
        except Exception:
            pass
    print("Simulation complete.")
    if sim.results is not None:
        print("  sat_position rows:", len(sim.results.sat_position))
        print("  interference rows:", len(sim.results.interference))