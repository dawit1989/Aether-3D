#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reference example: 3DANTS orchestrator demo.

This script demonstrates the **layer-based orchestrator** introduced in
examples/3D_network_with_traffic.py.  It shows the full workflow:

    configure -> compose -> run -> inspect results

The orchestrator (NetworkSimulation) is kept separate from the
simulation algorithm logic.  Every functional block — geometry, fading,
shadowing, traffic, HAPS, base-stations, interference — lives in its own
SimLayer subclass.  The simulation loop merely configures each layer
and calls step per millisecond, merging the returned fragments.

**Major components demonstrated**

* **SimulationConfig** — single dataclass holding all tunable parameters.
* **NetworkSimulation** — the fluent orchestrator with methods
  with_constellation, with_ground_station, with_fading,
  with_traffic, with_haps, with_base_stations, with_uav.
* **Layers** — GeometryLayer, FadingLayer, ShadowingLayer, TrafficLayer,
  HAPSLayer, BaseStationLayer, InterferenceLayer (all pre-registered).
  Optional extension layers: GEOLayer, AirObjectsLayer,
  FrequencySelectiveLayer, PPPInterferenceLayer, GaussianFieldLayer,
  AtmosphericLossLayer, SatelliteCellGeomLayer, NTNFadingLayer,
  ConstellationLayer, SphereUtilLayer, BaseFadingLayer.
* **ShadowingFading** — selected/configured through the built-in
  ShadowingLayer which is part of the default layer order.  Users
  never instantiate it directly; they configure shadowing via
  SimulationConfig parameters and the orchestrator wires it up.
* **Analysis utilities** — SINR, throughput, coverage, CDF helpers from
  the 3DANTS.analysis sub-package.

**Existing implementations reused**

All channel, mobility, fading, shadowing, traffic, and interference
models are the *unmodified* classes from the 3DANTS package:
LEO_GEO, HexagonGrid, HAPS_trajectory, Uav_trajectory,
Satellite_Fading_channel, Air_Fading_channel,
ShadowingFading, Rx_power, terresterial_network, etc.
This example only *wires them together* through the orchestrator API.

**Adapting the example**

To run a different scenario, change the fluent configuration calls
below (e.g. different carrier frequency, constellation size, or number
of base-stations).  To add a new functional block, write a new
SimLayer subclass and call sim.add_layer(MyLayer()) — the core
loop needs no modification.

Usage::

    python examples/orchestrator_demo.py             # small run
    python examples/orchestrator_demo.py --steps 5    # more passes
    python examples/orchestrator_demo.py --verbose    # per-ms progress
"""
from __future__ import annotations

import importlib
import os
import sys

import numpy as np

# --- path setup ----------------------------------------------------------
# The 3DANTS package starts with a digit, so it must be imported via
# importlib.  The orchestrator lives in examples/3D_network_with_traffic.py
_EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(_EXAMPLES_DIR)
for _p in (_PKG_PARENT, _EXAMPLES_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Import the orchestrator module (starts with a digit — use importlib).
_orchestrator = importlib.import_module("3D_network_with_traffic")

# Public API from the orchestrator module.
NetworkSimulation = _orchestrator.NetworkSimulation
SimulationConfig = _orchestrator.SimulationConfig
SimLayer = _orchestrator.SimLayer
ComponentRegistry = _orchestrator.ComponentRegistry

# Analysis utilities from the 3DANTS.analysis sub-package.
_analysis = importlib.import_module("3DANTS.analysis")
compute_sinr = _analysis.compute_sinr
sinr_summary = _analysis.sinr_summary
outage_probability = _analysis.outage_probability
spectral_efficiency = _analysis.spectral_efficiency
mean_throughput = _analysis.mean_throughput
coverage_probability = _analysis.coverage_probability
empirical_cdf = _analysis.empirical_cdf
plot_cdf = _analysis.plot_cdf


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def run_simulation(steps: int = 2, verbose: bool = False) -> NetworkSimulation:
    """Configure and run a small network-with-traffic simulation.

    Demonstrates the full orchestrator workflow:

    1. **Create + configure** — SimulationConfig with explicit defaults.
    2. **Compose network** — constellation, ground station, base-stations.
    3. **Configure nodes** — HAPS and UAV interference parameters.
    4. **Configure traffic** — per-satellite, HAPS, and base-station rates.
    5. **Configure channel** — fading mode and carrier frequency.
    6. **Execute** — sim.run().
    7. **Inspect** — returned SimulationResults DataFrames.
    """
    # ------------------------------------------------------------------
    # Step 1: Create configuration with explicit parameters.
    # ------------------------------------------------------------------
    print_section("Step 1: Create & configure SimulationConfig")

    cfg = SimulationConfig(
        seed=42,
        h_leo=600e3,
        inclination=60,
        num_sat=48,
        num_planes=4,
        phasing=1,
        f=2.5e9,               # S-band carrier frequency
        noise_figure_db=7.0,
        temperature_k=290.0,
        gs_lat=53.110987,
        gs_lon=8.851239,
        time_start=(2022, 9, 22, 0, 0, 0),
        time_end=(2022, 9, 22, 0, 30, 0),
        steps=steps,
        max_ms=200,          # cap per-pass iterations for faster demo
        plot=False,
        verbose=verbose,
    )
    # Reduced batch size and N for faster demo execution.
    cfg.fading_batch_size = 1000
    cfg.fading_N = 64
    print(f"  h_leo         = {cfg.h_leo / 1e3:.0f} km")
    print(f"  num_sat       = {cfg.num_sat}")
    print(f"  num_planes    = {cfg.num_planes}")
    print(f"  carrier freq  = {cfg.f / 1e9:.1f} GHz")
    print(f"  ground station = ({cfg.gs_lat:.4f}, {cfg.gs_lon:.4f})")

    # ------------------------------------------------------------------
    # Step 2: Create the orchestrator and configure the network topology.
    # ------------------------------------------------------------------
    print_section("Step 2: Configure network topology (fluent)")

    sim = NetworkSimulation(cfg)

    # Fluent configuration — each call returns *self* so they chain.
    sim.with_constellation(
        h_leo=600e3, num_sat=48, num_planes=4, inclination=60
    ).with_ground_station(
        lat=53.110987, lon=8.851239
    ).with_base_stations(
        n=3
    )

    print(f"  Layers: {[l.name for l in sim.layers]}")
    print(f"  Registry: {sim.registry.names()}")

    # ------------------------------------------------------------------
    # Step 3: Configure nodes / terminals (HAPS, UAV).
    # ------------------------------------------------------------------
    print_section("Step 3: Configure terminal nodes")

    sim.with_haps(
        height=10.0, velocity=25.0
    ).with_uav(
        height=0.1, velocity=18.0
    )
    print(f"  haps_height = {sim.cfg.haps_height} km")
    print(f"  uav_height  = {sim.cfg.uav_height} km")

    # ------------------------------------------------------------------
    # Step 4: Configure traffic models.
    # ------------------------------------------------------------------
    print_section("Step 4: Configure traffic")

    sim.with_traffic(
        num_sat=40, haps_rate=10, bs_rates=(10, 8, 5)
    )
    print(f"  num_sat   = {sim.cfg.num_sat}")
    print(f"  haps_rate = {sim.cfg.haps_rate} pkts/ms")
    print(f"  bs_rates  = {sim.cfg.bs_rates}")

    # ------------------------------------------------------------------
    # Step 5: Configure channel / propagation models.
    # ------------------------------------------------------------------
    print_section("Step 5: Configure channel & propagation")

    # Fading mode: 'compensated' uses residual UE speed for the Doppler
    # correlation time (physical at ms resolution); 'full' uses the true
    # orbital velocity; 'scaled' derives a target coherence time.
    sim.with_fading(mode="compensated", fc=2.5e9)
    print(f"  fading_mode = {sim.cfg.fading_mode}")
    print(f"  carrier freq = {sim.cfg.f / 1e9:.1f} GHz")
    print("  ShadowingFading is wired via ShadowingLayer (default layer order).")
    print(f"  Layers including shadowing: "
          f"{'shadowing' in sim.registry.names()}")

    # ------------------------------------------------------------------
    # Step 6: Execute the simulation.
    # ------------------------------------------------------------------
    print_section("Step 6: Execute simulation")

    results = sim.run().results
    print(f"  Results type: {type(results).__name__}")
    print(f"  sat_position rows: {len(results.sat_position)}")
    print(f"  channel rows: {len(results.satellite_channel_time_series)}")
    print(f"  p_rx rows: {len(results.p_rx)}")
    print(f"  interference rows: {len(results.interference)}")

    return sim


def inspect_results(sim: NetworkSimulation) -> None:
    """Display key results from a completed simulation run."""
    print_section("Inspect results")

    results = sim.results

    # --- Received power and SNR -------------------------------------------
    p_rx = results.p_rx
    if len(p_rx) > 0:
        print("\n  Received-power statistics (P_rx_user in dBW):")
        print(f"    mean   = {p_rx['P_rx_at_User (dBW)'].mean():.2f} dBW")
        print(f"    min    = {p_rx['P_rx_at_User (dBW)'].min():.2f} dBW")
        print(f"    max    = {p_rx['P_rx_at_User (dBW)'].max():.2f} dBW")

        print("\n  SNR statistics (dB):")
        snr = p_rx["SNR (dB)"]
        print(f"    mean   = {snr.mean():.2f} dB")
        print(f"    min    = {snr.min():.2f} dB")
        print(f"    max    = {snr.max():.2f} dB")

    # --- Interference / SINR ----------------------------------------------
    interf = results.interference
    if len(interf) > 0 and "SINR (dB)" in interf.columns:
        sinr_db = interf["SINR (dB)"].dropna()
        print("\n  SINR statistics (dB):")
        print(f"    mean   = {sinr_db.mean():.2f} dB")
        print(f"    min    = {sinr_db.min():.2f} dB")
        print(f"    max    = {sinr_db.max():.2f} dB")

        # Use the analysis utility to compute outage and throughput.
        bw = sim.cfg.max_Bandwidth_per_beam * 1e6  # MHz -> Hz
        outage = outage_probability(sinr_db, threshold_db=-5.0)
        avg_tp = mean_throughput(sinr_db, bw)
        cov = coverage_probability(sinr_db, threshold_db=-5.0)
        print(f"\n  Analysis (threshold = -5 dB, BW = {bw / 1e6:.0f} MHz):")
        print(f"    outage probability  = {outage:.2%}")
        print(f"    coverage probability = {cov:.2%}")
        print(f"    mean throughput     = {avg_tp / 1e6:.2f} Mbps")

    # --- Visibility summary -----------------------------------------------
    vis = results.visibility
    if len(vis) > 0:
        print(f"\n  Visibility events: {len(vis)} simultaneous-group(s)")
        if "duration_min" in vis.columns:
            print(f"    avg duration = {vis['duration_min'].mean():.1f} min")

    # --- Shadowing samples (demonstrates ShadowingFading usage) ----------
    chan = results.satellite_channel_time_series
    if len(chan) > 0 and "large scale shadowing" in chan.columns:
        sf_samples = chan["large scale shadowing"].dropna()
        if len(sf_samples) > 0:
            print(f"\n  ShadowingFading samples (via ShadowingLayer):")
            print(f"    count = {len(sf_samples)}")
            print(f"    mean  = {sf_samples.mean():.2f} dB")
            print(f"    std   = {sf_samples.std():.2f} dB")

    # --- Saturation / elevation distribution ------------------------------
    if "Elevation Angle (degree)" in p_rx.columns:
        elev = p_rx["Elevation Angle (degree)"]
        print(f"\n  Elevation angle distribution:")
        print(f"    mean = {elev.mean():.1f} deg")
        print(f"    min  = {elev.min():.1f} deg")
        print(f"    max  = {elev.max():.1f} deg")


def demonstrate_reconfiguration() -> None:
    """Show how to reconfigure the simulation without modifying core code.

    This demonstrates the *reconfigurable* nature of the orchestrator:
    by swapping the fading mode and carrier frequency, the entire
    simulation behaviour changes without touching any implementation file.
    """
    print_section("Reconfiguration demo: different fading mode")

    # Configuration A: 'compensated' fading at 2.5 GHz.
    sim_a = (NetworkSimulation(SimulationConfig(
        num_sat=48, num_planes=4, f=2.5e9, steps=2,
        fading_mode="compensated",
        max_ms=200,
        time_start=(2022, 9, 22, 0, 0, 0),
        time_end=(2022, 9, 22, 2, 0, 0),
    )).with_constellation(num_sat=48, num_planes=4)
     .with_ground_station(lat=53.110987, lon=8.851239)
     .with_fading(mode="compensated"))
    sim_a.run()

    # Configuration B: 'scaled' fading at 20 GHz (Ka-band).
    sim_b = (NetworkSimulation(SimulationConfig(
        num_sat=48, num_planes=4, f=20e9, steps=2,
        fading_mode="scaled",
        max_ms=200,
        time_start=(2022, 9, 22, 0, 0, 0),
        time_end=(2022, 9, 22, 2, 0, 0),
    )).with_constellation(num_sat=48, num_planes=4)
     .with_ground_station(lat=53.110987, lon=8.851239)
     .with_fading(mode="scaled", fc=20e9))
    sim_b.run()

    print(f"  Config A: f={sim_a.cfg.f / 1e9:.1f} GHz, "
          f"mode={sim_a.cfg.fading_mode}")
    print(f"  Config B: f={sim_b.cfg.f / 1e9:.1f} GHz, "
          f"mode={sim_b.cfg.fading_mode}")

    # Compare SNR from both runs.
    if len(sim_a.results.p_rx) > 0 and len(sim_b.results.p_rx) > 0:
        snr_a = sim_a.results.p_rx["SNR (dB)"]
        snr_b = sim_b.results.p_rx["SNR (dB)"]
        print(f"\n  SNR comparison:")
        print(f"    Config A (S-band):  mean = {snr_a.mean():.2f} dB")
        print(f"    Config B (Ka-band): mean = {snr_b.mean():.2f} dB")
        if snr_b.mean() > snr_a.mean():
            print("    -> Ka-band shows higher SNR (shorter wavelength, "
                  "less free-space path loss)")
        else:
            print("    -> S-band shows higher SNR (different atmospheric "
                  "attenuation at S-band)")


def demonstrate_custom_layer() -> None:
    """Show how to add a custom layer without modifying the orchestrator.

    A custom SimLayer can be appended via add_layer().  It will
    appear after the built-in layers in the simulation loop.
    """
    print_section("Custom layer demo")

    class ElevationLogger(SimLayer):
        """Simple layer that records the elevation angle per step."""
        name = "elevation_logger"

        def _configure(self, sim):
            super()._configure(sim)
            self._elevations = []

        def step(self, ctx):
            self._elevations.append(getattr(ctx, "elevation_angle", None))
            return {}

        def _build_results(self):
            pass

    layer = ElevationLogger()
    sim = NetworkSimulation(SimulationConfig(
        num_sat=48, num_planes=4, steps=2,
        max_ms=200,
        time_start=(2022, 9, 22, 0, 0, 0),
        time_end=(2022, 9, 22, 2, 0, 0),
    ))
    sim.add_layer(layer)
    sim.run()

    elevations = [e for e in layer._elevations if e is not None]
    print(f"  Registered layers: {[l.name for l in sim.layers]}")
    print(f"  Custom layer recorded {len(elevations)} elevation samples")
    if elevations:
        print(f"  range: {min(elevations):.1f} - {max(elevations):.1f} deg")


def demonstrate_new_layers() -> None:
    """Demonstrate the first batch of orchestrator extension layers.

    Shows how AtmosphericLossLayer and SatelliteCellGeomLayer can be
    plugged into the orchestrator via the fluent API without modifying
    the core simulation loop.
    """
    print_section("New layers: atmospheric loss + satellite cell geometry")

    sim = (NetworkSimulation(SimulationConfig(
        num_sat=48, num_planes=4, f=2.0e9, steps=2,
        max_ms=200,
        time_start=(2022, 9, 22, 0, 0, 0),
        time_end=(2022, 9, 22, 2, 0, 0),
    ))
     .with_constellation(num_sat=48, num_planes=4)
     .with_ground_station(lat=53.110987, lon=8.851239)
     .with_fading(mode="full")
     .with_atmospheric_loss(detailed=True)
     .with_satellite_cell_geom(radius_km=25.0))
    sim.run()

    print(f"  Registered layers: {[l.name for l in sim.layers]}")
    print(f"  cell_radius_km: {sim.cfg.cell_radius_km}")
    print(f"  detailed_atmospheric_loss: {sim.cfg.detailed_atmospheric_loss}")
    if sim.results is not None and len(sim.results.p_rx) > 0:
        print(f"  p_rx rows: {len(sim.results.p_rx)}")


def demonstrate_third_batch_layers() -> None:
    """Demonstrate the second batch of orchestrator extension layers.

    Shows how ConstellationLayer, SphereUtilLayer, and BaseFadingLayer
    (wrapping the standalone 3DANTS modules constellation.py,
    sphere_util.py, and fading_channel_sim.py) can be plugged into the
    orchestrator via the fluent API.
    """
    print_section("Third-batch layers: constellation + sphere_util + base_fading")

    sim = (NetworkSimulation(SimulationConfig(
        num_sat=48, num_planes=4, f=2.0e9, steps=2,
        max_ms=200,
        time_start=(2022, 9, 22, 0, 0, 0),
        time_end=(2022, 9, 22, 2, 0, 0),
    ))
     .with_constellation(num_sat=48, num_planes=4)
     .with_ground_station(lat=53.110987, lon=8.851239)
     .with_fading(mode="full")
     .with_constellation_layer()
     .with_sphere_util()
     .with_base_fading())
    sim.run()

    print(f"  Registered layers: {[l.name for l in sim.layers]}")
    if sim.results is not None and len(sim.results.p_rx) > 0:
        print(f"  p_rx rows: {len(sim.results.p_rx)}")


def demonstrate_czml_output() -> None:
    """Demonstrate CZML output for CesiumJS visualization.

    Runs a small simulation and writes the results to a .czml file
    that can be loaded into CesiumJS for 3D visualization of satellite
    trajectories, ground station, and coverage cells.
    """
    print_section("CZML output for CesiumJS")

    import tempfile
    output_path = os.path.join(tempfile.gettempdir(), "3dants_demo.czml")

    sim = (NetworkSimulation(SimulationConfig(
        num_sat=48, num_planes=4, f=2.0e9, steps=2,
        max_ms=200,
        time_start=(2022, 9, 22, 0, 0, 0),
        time_end=(2022, 9, 22, 2, 0, 0),
    ))
     .with_czml(output_path)
     .with_constellation(num_sat=48, num_planes=4)
     .with_ground_station(lat=53.110987, lon=8.851239)
     .with_fading(mode="full"))
    sim.run()

    print(f"  CZML file written to: {output_path}")
    if os.path.exists(output_path):
        import json
        entities = json.loads(open(output_path).read())
        print(f"  CZML entities: {len(entities)}")
    if sim.results is not None and len(sim.results.p_rx) > 0:
        print(f"  p_rx rows: {len(sim.results.p_rx)}")


def main():
    """Run the orchestrator demo end-to-end."""
    print_section("3DANTS Orchestrator Demo")
    print("  configure -> compose -> run -> inspect results")

    # Parse --steps and --verbose from argv.
    steps = 2
    verbose = False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--verbose":
            verbose = True
        elif args[i] == "--steps":
            i += 1
            if i < len(args):
                steps = int(args[i])
        elif args[i].startswith("--steps="):
            steps = int(args[i].split("=", 1)[1])
        i += 1

    # Step 1-7: Configure, compose, and run.
    sim = run_simulation(steps=steps, verbose=verbose)

    # Inspect the results.
    inspect_results(sim)

    # Demonstrate reconfiguration (different fading / frequency).
    demonstrate_reconfiguration()

    # Demonstrate first-batch extension layers.
    demonstrate_new_layers()

    # Demonstrate second-batch extension layers.
    demonstrate_third_batch_layers()

    # Demonstrate extensibility (custom layer).
    demonstrate_custom_layer()

    # Demonstrate CZML output for CesiumJS.
    demonstrate_czml_output()

    print_section("Demo complete")


if __name__ == "__main__":
    main()
