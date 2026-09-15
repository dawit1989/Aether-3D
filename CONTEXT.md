# Aether-3D — Project Context

> This document provides comprehensive context for AI agents and contributors
> working on the Aether-3D codebase. For coding conventions and build commands,
> see [Aether-3D/AGENTS.md](Aether-3D/AGENTS.md).

---

## 1. What Is This Project?

**Aether-3D** (formerly **3DANTS**) is an open-source, **system-level simulator
for unified 3D networks** created by the Department of Communications
Engineering, University of Bremen, Germany. It models the interplay between:

| Segment | Nodes |
|---------|-------|
| **Space** | LEO Walker Delta constellations, GEO satellites |
| **Air** | HAPS (High-Altitude Platform Stations), UAVs / drones |
| **Terrestrial** | 5G / 6G base stations, mobile UEs |

The simulator evaluates **link quality** across coverage, channel fading,
beamforming, SINR, and achievable data rate over a given geographic area and
time window. It is the open reference implementation used to reproduce the
numerical results of
[3GPP TR 38.811](https://www.3gpp.org/dynareport/38811.htm) and related
NTN / direct-to-device studies.

> **Import convention:** The Python package directory is named `3DANTS` (starts
> with a digit). It **cannot** be imported with a plain `import` statement —
> all imports must use `importlib.import_module("3DANTS.module")`.

---

## 2. High-Level Architecture

The design is a **layer-based orchestrator**: `NetworkSimulation` is a thin,
generic loop that configures each `SimLayer` and calls `step()` per
millisecond, merging returned dict fragments into a shared `SimpleNamespace`
context.

```
                    ┌─────────────────────────┐
                    │    SimulationConfig      │
                    │   (mutable dataclass)    │
                    └────────────┬─────────────┘
                                 │ configures
                                 ▼
                    ┌─────────────────────────┐
                    │    NetworkSimulation     │◄── ComponentRegistry
                    │   (fluent orchestrator)  │    (name → SimLayer factory)
                    └────────────┬─────────────┘
                                 │ manages
                                 ▼
                     Layer Pipeline (List[SimLayer])
 ┌──────────┐ ┌────────┐ ┌───────────┐ ┌─────────┐ ┌──────┐ ┌─────────────┐ ┌──────────────┐
 │ Geometry │→│ Fading │→│ Shadowing │→│ Traffic │→│ HAPS │→│ BaseStation │→│ Interference │
 └──────────┘ └────────┘ └───────────┘ └─────────┘ └──────┘ └─────────────┘ └──────────────┘
                                 │
                                 ▼
                       SimulationResults
                       (6 DataFrames)
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        analysis/ package         CZMLWriter
     (SINR, throughput, CDF)   (CesiumJS 3D viz)
```

---

## 3. Package Layout

```
Aether-3D/                               # Repository root
├── CONTEXT.md                            # ← This file
├── README.md                             # User-facing documentation
├── Aether-3D/                            # Python package directory
│   ├── 3DANTS/                           # Core package (__version__ = "1.0.0")
│   │   ├── communication_channel/        # 12 modules — fading, shadowing, atmospheric, NTN
│   │   ├── position_and_mobility/        # 10 modules — LEO/GEO, HAPS, UAV, hex grid, PPP
│   │   ├── Traffic/                      # CBR, Poisson, Bursty traffic generators
│   │   ├── analysis/                     # 11 modules — SINR, throughput, coverage, CZML, registry
│   │   └── Engine/                       # Legacy monolithic simulation scripts
│   ├── examples/                         # Orchestrator demos, legacy scripts, CesiumJS viewer
│   │   ├── 3D_network_with_traffic.py    # ★ Main orchestrator implementation
│   │   ├── orchestrator_demo.py          # ★ Comprehensive reference demo
│   │   ├── czml_viewer.html              # Standalone CesiumJS viewer
│   │   └── serve_czml_viewer.py          # Local CORS HTTP server
│   ├── tests/                            # 9 test modules (~200 tests)
│   ├── docs/                             # Technical reports, test plans (10 files)
│   ├── Aether3D-Frontend/                # React + Vite + CesiumJS web frontend
│   ├── AGENTS.md                         # Coding conventions & build commands
│   └── requirements.txt                  # Python 3.12+ dependencies
├── docs/                                 # Symlinked / copied docs
├── .agents/skills/                       # 15 CesiumJS skills
└── optimal-lap-altitude-*.pdf            # Reference paper
```

---

## 4. Core Subpackages

### 4.1 `communication_channel/` — Channel Models

| Module | Key Class | Purpose |
|--------|-----------|---------|
| `satellite_comm_param.py` | `Satellite_communication_parameter` | 3GPP TR 38.821 S/Ka-band parameter catalog (EIRP, gain, beamwidth, bandwidth, G/T) |
| `rx_power_calc.py` | `Rx_power` | Link-budget engine: FSPL, antenna beam patterns (Bessel), noise floors, LoS probability, shadow fading lookup |
| `atmospheric_loss.py` | `Atmospheric_loss` | ITU-R P.676/P.840 gas, cloud, rain, tropospheric & ionospheric scintillation |
| `satellite_fading_channel.py` | `Satellite_Fading_channel` | Loo / 3GPP TR 38.811 Shadowed-Rician composite fading with 3 Doppler modes |
| `fading_channel_sim.py` | `FadingSimulation` | Base Jakes/Clarke Rayleigh/Rician fading simulator |
| `air_objects_class.py` | `Air` | Air-to-ground LoS, Al-Hourani pathloss, Rician K-factor, UAV-to-UAV channels |
| `air_2_ground_fading.py` | `Air_Fading_channel` | Segmented Jakes Rician + rank-matched Nakagami for air-to-ground links |
| `ntn_fading_channel_sim.py` | `FadingSimulation_Non_terrestrial` | NTN-specific satellite fading (3 Doppler modes, no chunking) |
| `frequency_selective.py` | `FrequencySelectiveFadingSimulation` | Wideband multipath / OFDM fading (subcarriers, delay spread, Cholesky PDP) |
| `gaussian_field.py` | `Guassian_Random_filed_generator` | 2D spatially correlated Gaussian random fields (gstools SRF) |
| `shadowing_temporally_correlated_AR.py` | `ShadowingFading` | AR(1) temporally correlated large-scale shadow fading |

**Key channel model (Shadowed-Rician composite):**
```
H[t] = H_Rician[t] + H_Nakagami[t] · exp(-j·2π·d·fc/c)
```

**Three Doppler modes** (affect temporal correlation, not marginal distribution):
- **`full`** — True orbital Doppler: fd = |v_LOS|·fc/c. Tc ≈ 5–7 µs at S-band.
- **`compensated`** — UE residual Doppler after satellite pre-compensation.
  Pedestrian 1.5 m/s → Tc ≈ 34 ms.
- **`scaled`** — Back-calculated from target coherence time via Clarke's
  formula: fD = 0.423 / Tc.

**AR(1) shadow fading:**
```
s₀ ~ N(0, σ²)
sₗ = φ·sₗ₋₁ + √(1-φ²)·gₗ,  φ = exp(-1/τ)
```
σ_SF from 3GPP TR 38.811 lookup tables (S-band / Ka-band, LoS / NLoS) as a
function of elevation angle.

---

### 4.2 `position_and_mobility/` — Orbital & Terrestrial Geometry

| Module | Key Class / Functions | Purpose |
|--------|----------------------|---------|
| `geo.py` | `LEO_GEO` | Walker constellation generation (SGP4/Skyfield), visibility events, elevation angle, orbital elements |
| `haps.py` | `HAPS_trajectory` | Circular stratospheric patrol trajectory (~20 km altitude) |
| `uav.py` | `Uav_trajectory` | Low-altitude UAV circular & random-walk mobility |
| `hexagon_grid.py` | `HexagonGrid` | WGS84 hexagonal cell beam planning (pyproj geodesic) |
| `terrestrial.py` | `terresterial_network` | BS placement (Poisson disk), UE PPP generation, 3GPP TR 38.901 pathloss, cross-tier interference |
| `ppp_scenario.py` | PPP functions | 3D truncated-cone PPP interference geometry |
| `satellite_cell_geom.py` | Hex geometry functions | Hexagonal beam footprint vertices & overlap rhombus |
| `sphere_util.py` | `generate_sphere_points` | Uniform sphere point distribution (inverse CDF) |
| `constellation.py` | Constellation runner | Walker constellation demo / scenario runner |

---

### 4.3 `Traffic/` — Packet Generation

| Model | Key Parameters |
|-------|---------------|
| **CBR** (Constant Bit Rate) | `packet_size`, `packet_rate` |
| **Poisson** | `avg_packet_rate`, `packet_size_mean`, `packet_size_std` |
| **Bursty** (ON/OFF) | `on_duration`, `off_duration`, `packet_rate_on`, `packet_size` |

All traffic models expose `generate_packets(duration)` and
`get_packets_at_time(current_time_ms)`.

---

### 4.4 `analysis/` — Post-Processing & Visualization

| Module | Key Exports | Purpose |
|--------|-------------|---------|
| `sinr.py` | `compute_sinr`, `outage_probability`, `sinr_summary` | SINR calculation & statistics |
| `throughput.py` | `spectral_efficiency`, `mean_throughput`, `throughput_cdf` | Shannon capacity analysis |
| `coverage.py` | `coverage_probability`, `coverage_vs_elevation` | Binned coverage across elevation angles |
| `interference.py` | `detect_interference`, `classify_interference` | Interference detection & multi-source labeling |
| `visibility.py` | `compute_simultaneous_visibility`, `visibility_summary` | Multi-satellite visibility windows |
| `cdf.py` | `empirical_cdf`, `plot_cdf` | Empirical distribution functions |
| `traffic.py` | `cbr`, `poisson`, `bursty`, `build_traffic_models` | Traffic trace factory functions |
| `czml_writer.py` | `CZMLWriter` | Full Cesium CZML export (orbits, links, tooltips, coverage footprints) |
| `plotting.py` | `plot_visibility_bars`, `plot_network_geometry`, `plot_interference_cdf` | Matplotlib visualization |
| `_registry.py` | `ComponentRegistry` | Plugin name → factory registry |

---

### 4.5 `Engine/` — Legacy Simulation Scripts

| Module | Purpose |
|--------|---------|
| `simulation.py` | Low-level simulation execution: orbital state vectors, coordinate frame transforms, trajectory time series |
| `LEO_constellation_and_flying_object_Trajectory.py` | Legacy monolithic constellation + trajectory calculation pipeline |

---

## 5. The Orchestrator

Defined in `examples/3D_network_with_traffic.py`, the orchestrator consists of
three main components:

### 5.1 `SimulationConfig` (dataclass, 45+ fields)

| Category | Key Parameters |
|----------|---------------|
| **Reproducibility** | `seed=42` |
| **Constellation** | `h_leo=600e3`, `inclination=60`, `num_sat=120`, `num_planes=10`, `phasing=1` |
| **RF** | `f=2.0e9` (S-band), `A_z=0.1 dB`, `G_max_Rx=4.0 dBi`, `noise_figure_db=7.0`, `temperature_k=298.15` |
| **Ground Station** | `gs_lat=53.110987`, `gs_lon=8.851239` (Bremen, Germany) |
| **Time Window** | `time_start=(2022,9,22,0,0,0)`, `time_end=(2022,9,22,18,0,0)` |
| **HAPS** | `haps_height=10 km`, `haps_velocity=25 km/h`, `haps_radius=6 km` |
| **Terrestrial** | `num_base_stations=3`, `bs_height=35 m`, `terrestrial_radius=20 km` |
| **Fading** | `fading_mode='full'`, `fading_batch_size=10000`, `fading_N=256` |
| **Traffic** | `haps_rate=10`, `bs_rates=(10,8,5)` pkts/ms |
| **Execution** | `steps=None`, `max_ms=None`, `verbose=False`, `czml_output_path=None` |
| **Extensions** | GEO, air objects, frequency-selective, PPP, Gaussian field, atmospheric loss, cell geometry flags |

### 5.2 `SimLayer` (ABC) — Layer Lifecycle

```
configure(sim)          ← called once per satellite pass
├── _configure(sim)     ← one-time setup (1st pass only, guarded by _built flag)
└── _configure_pass(sim)← per-pass state reset

begin_pass(sim)         ← before ms loop
step(ctx) → dict        ← per-millisecond (returned dict merged into shared context)
end_pass(sim)           ← after ms loop
```

### 5.3 Fluent `with_*()` API

Each method updates `self.cfg` or appends layers and returns `self` for chaining:

| Method | Configures |
|--------|-----------|
| `with_constellation(h_leo, num_sat, num_planes, inclination)` | Orbital parameters |
| `with_ground_station(lat, lon)` | Ground station location |
| `with_fading(mode, fc)` | Doppler mode & carrier frequency |
| `with_traffic(num_sat, haps_rate, bs_rates)` | Packet generation rates |
| `with_haps(height, velocity)` | HAPS altitude & speed |
| `with_base_stations(n)` | Number of terrestrial BSs |
| `with_uav(height, velocity)` | UAV kinematics |
| `with_geo(count, inclination)` | GEO satellite support |
| `with_air_objects(environment)` | Air-to-ground LoS layer |
| `with_freq_selective(num_subcarriers, delay_spread, num_taps)` | Wideband OFDM fading |
| `with_ppp(lam, radius)` | PPP interference modeling |
| `with_gaussian_field(variance, len_scale)` | Spatial shadowing correlation |
| `with_atmospheric_loss(detailed)` | ITU-R atmospheric loss |
| `with_satellite_cell_geom(radius_km)` | Hexagonal beam footprints |
| `with_czml(path)` | CZML export after run |
| `add_layer(layer)` | Custom SimLayer injection |

---

## 6. Default Layer Pipeline (7 layers)

| # | Layer | Name | Responsibility |
|---|-------|------|---------------|
| 1 | `GeometryLayer` | `geometry` | Walker constellation propagation, satellite position/velocity, elevation/azimuth angles, LoS probability, hexagonal beam grid, serving satellite selection (highest elevation) |
| 2 | `FadingLayer` | `fading` | Shadowed-Rician small-scale fading with 3 Doppler modes; re-batches fading samples every 1° elevation change |
| 3 | `ShadowingLayer` | `shadowing` | AR(1) temporally correlated large-scale shadow fading; re-evaluates every 5° elevation change |
| 4 | `TrafficLayer` | `traffic` | CBR/Poisson/Bursty packet generation for satellites, HAPS, BSs |
| 5 | `HAPSLayer` | `haps` | Circular HAPS trajectory, air-to-ground Rician fading & shadowing, HAPS interference |
| 6 | `BaseStationLayer` | `base_station` | 3 BSs with 3GPP TR 38.901 pathloss (LoS/NLoS ≤7 GHz), Rician fading, terrestrial interference |
| 7 | `InterferenceLayer` | `interference` | FSPL + atmospheric loss + beam roll-off → P_rx, thermal noise, SINR |

**SINR formula:**
```
SINR = P_rx_sat / (P_noise + I_HAPS + Σ I_BS_k)
```

---

## 7. Extension Layers (11 optional)

| Layer | Name | Purpose |
|-------|------|---------|
| `UAVLayer` | `uav` | Low-altitude UAV circular trajectories, UAV-to-GS interference |
| `GEOLayer` | `geo` | Geostationary satellite support via SGP4 |
| `AirObjectsLayer` | `air_objects` | Elevation-dependent air-to-ground LoS probabilities |
| `FrequencySelectiveLayer` | `freq_selective` | OFDM wideband multipath fading (subcarriers + delay spread) |
| `PPPInterferenceLayer` | `ppp` | Poisson Point Process spatial interference |
| `GaussianFieldLayer` | `gaussian_field` | 2D spatially correlated shadowing maps |
| `AtmosphericLossLayer` | `atmospheric_loss` | ITU-R P.676/P.840 gas/cloud/rain/scintillation |
| `SatelliteCellGeomLayer` | `satellite_cell_geom` | Hexagonal beam footprint geometry & overlap |
| `NTNFadingLayer` | `ntn_fading` | NTN-specific small-scale fading |
| `ConstellationLayer` | `constellation` | Legacy constellation parameters wrapper |
| `SphereUtilLayer` | `sphere_util` | Uniform sphere point generation |

---

## 8. Simulation Results

`sim.run()` produces a `SimulationResults` object with 6 DataFrames:

| DataFrame | Content |
|-----------|---------|
| `sat_position` | Satellite XYZ, velocity, GS distance, elevation, v_LOS |
| `sat_orbital_params` | Local coordinate angles (Θ_el, Θ_az from satellite; θ_el, θ_az from GS) |
| `satellite_channel_time_series` | Small-scale fading + large-scale shadowing samples |
| `p_rx` | Received power, FSPL, atmospheric loss, LoS probability, SNR |
| `interference` | Per-source interference (HAPS, BS₁–BS₃), desired signal, SINR |
| `visibility` | Multi-satellite visibility windows & durations |

---

## 9. Testing Infrastructure

**Framework:** `unittest.TestCase` executed via `pytest`. Heavy orbital
dependencies (skyfield, sgp4, sympy) are mocked for fast, isolated execution.

| Test File | Scope | Approx. Tests |
|-----------|-------|---------------|
| `test_3gpp_numerical.py` | 3GPP TR 38.811/38.821 numerical correctness | 48 |
| `test_simulation.py` | Orchestrator integration tests | 20 |
| `test_analysis_extended.py` | Analysis sub-package unit tests | 20 |
| `test_all_classes.py` | Full class instantiation coverage (8 subsystems) | ~40 |
| `test_accuracy_fixes.py` | Historical bug-fix regressions (9 classes) | ~20 |
| `test_analysis.py` | Core analysis utility tests | ~15 |
| `test_czml_writer.py` | CZML exporter validation (7 classes) | ~15 |
| `test_shadow_fading_ar1.py` | AR(1) shadow fading correlation & variance | ~10 |
| `test_LEO_satellite_fading_channel_modes.py` | Satellite fading Doppler modes & regression | ~10 |

```bash
cd Aether-3D
python -m pytest tests/ -v                         # Run all (~200 tests)
python -m pytest tests/test_3gpp_numerical.py -v    # 3GPP validation only
python -m pytest tests/test_simulation.py -v        # Orchestrator tests only
```

---

## 10. Frontend & Visualization

### CesiumJS CZML Viewer (legacy)
- `examples/czml_viewer.html` — Standalone browser viewer with bundled CesiumJS
- `examples/serve_czml_viewer.py` — Local CORS HTTP server
- `examples/sample.czml` — Sample CZML animation dataset

### Modern Frontend (`Aether3D-Frontend/`)
- **Stack:** React 18.3 + Vite 5.4 + CesiumJS 1.125
- **Commands:** `npm run dev` (localhost:5173), `npm run build`, `npm run lint`

### CesiumJS Skills (`.agents/skills/`)
15 specialized CesiumJS skill modules (locked via `skills-lock.json`) covering
viewer setup, camera control, entities, 3D tiles, imagery, terrain, primitives,
materials, custom shaders, time properties, spatial math, interaction/picking,
models/particles, and core utilities.

---

## 11. Documentation (`docs/`)

| Document | Content |
|----------|---------|
| Part 1 (Introduction) | Motivation for unified 3D NTN+TN networks |
| Part 2 (Channel Modeling) | Time-correlated channel formulation, AR(1) shadowing, Shadowed-Rician, Doppler |
| Part 3 (Simulator Modules) | Architecture of all modules, coordinate transforms, serving satellite selection |
| Part 4 (Simulation Results) | SINR CDFs, outage curves, coverage statistics |
| 3GPP TR 38.811 Report | Deep dive into NTN specs, S/Ka-band parameters, antenna patterns |
| Test Plan & Report | 48 numerical correctness tests — all passing |

---

## 12. Key Dependencies

```
skyfield >= 1.46      # Satellite position propagation
sgp4 >= 2.22          # SGP4 orbit propagation
numpy >= 1.24         # Core numerics
scipy >= 1.10         # Scientific computing
sympy >= 1.12         # Symbolic math
pandas >= 2.0         # Data management
pyproj >= 3.5         # Geodesic calculations
shapely >= 2.0        # Geometric operations
scikit-learn >= 1.2   # ML utilities
gstools >= 1.4        # Gaussian random field generation
matplotlib >= 3.7     # Plotting
pytest >= 7.0         # Testing
```

Python 3.12+ is recommended.

---

## 13. Extension Points

| Want to… | How |
|----------|-----|
| Add a new physical layer | Subclass `SimLayer`, implement `step(ctx) → dict`, register via `add_layer()` |
| Change constellation | `with_constellation(num_sat=48, num_planes=4, inclination=60)` |
| Switch frequency band | `SimulationConfig(f=20e9)` for Ka-band |
| Add atmospheric effects | `with_atmospheric_loss(detailed=True)` |
| Export 3D visualization | `with_czml("/path/to/output.czml")` → load in CesiumJS viewer |
| Add custom traffic | Create a `TrafficModel(model_type='CBR', ...)` and wire into `TrafficLayer` |
| Validate against 3GPP | Run `python -m pytest tests/test_3gpp_numerical.py -v` |
| Build a custom layer | See `examples/orchestrator_demo.py` for the `ElevationLogger` example |
