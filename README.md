# Aether-3D (formerly 3DANTS)

An open-source **system-level simulator for unified 3D networks**.

Aether-3D (formerly **3DANTS**) brings together the **space** segment (GEO and LEO
satellites), the **air** segment (HAPS and UAVs), and the **terrestrial** network into
a single unified 3D network framework. Unified 3D networks are expected to emerge in
6G by tightly integrating Non-Terrestrial Networks (NTN) with Terrestrial Networks to
provide seamless connectivity across diverse areas. Each layer — space, air, and
terrestrial — has its own dynamics and channel properties, producing spatial-temporal
evolution of every communication link.

This simulator lets you define a 3D network and evaluate link quality across
**coverage**, **channel**, **beamforming**, **SINR**, and **achievable data rate**
over a given area and time window. It is the open reference implementation used to
reproduce the numerical results of
[3GPP TR 38.811](https://www.3gpp.org/dynareport/38811.htm) and related
direct-to-device / non-terrestrial-network studies.

Created by the **Department of Communications Engineering, University of Bremen,
Germany**.
[GitHub repository](https://github.com/ant-uni-bremen/Aether-3D)

---

## Features

- **Position & Mobility** — LEO Walker Delta constellations, GEO satellites, HAPS,
  UAVs, terrestrial base stations, and PPP interference scenarios. Orbital
  propagation via SGP4 / Skyfield with full classical orbital-element derivation.
- **Communication Channel** — Shadowed-Rician small-scale fading (3GPP TR 38.811
  Loo model) with three Doppler modes (full, compensated, scaled); AR(1)
  temporally-correlated large-scale shadow fading; frequency-selective fading;
  atmospheric attenuation (ITU-R P.676, P.840, etc.); air-to-ground pathloss;
  Gaussian random field spatial correlation; RX-power and satellite
  communication-parameter computation.
- **Traffic** — Configurable CBR, Poisson, and Bursty (ON/OFF) traffic models
  for satellites, HAPS, and base stations.
- **Simulation Engine** — A layer-based orchestrator (configure → compose → run →
  inspect) that drives the simulation over the desired time horizon and produces
  SINR / throughput / coverage / interference analysis.
- **Analysis** — Reusable, framework-independent utilities for SINR computation,
  outage probability, throughput, coverage probability, empirical CDFs,
  visibility-overlap analysis, interference classification, and CZML output
  for CesiumJS 3D visualization.
- **Testing** — Comprehensive numerical correctness test suite validating each
  3GPP channel model against known reference values from 3GPP TR 38.811,
  TR 38.821, TR 38.901, ITU-R P.676, and the Al-Hourani LAP-altitude paper.

---

## Architecture

Aether-3D is organized around a **layer-based orchestrator** architecture. The
simulation behaviour is split into independent `SimLayer` subclasses, each
responsible for one functional block. The orchestrator (`NetworkSimulation`) is
a thin, generic loop that merely configures each layer and calls `step()` per
millisecond, merging the returned fragments into a shared context.

### Project Layout

```
Aether-3D (repo root)
├── README.md                         This file
├── Aether-3D/                        # Python package directory
│   ├── 3DANTS/                       # Main package (starts with digit → uses importlib)
│   │   ├── communication_channel/    # Fading, shadowing, atmospheric loss, RX power
│   │   ├── position_and_mobility/    # LEO/GEO, HAPS, UAV, terrestrial, cell geometry
│   │   ├── Traffic/                  # Traffic models (CBR, Poisson, Bursty)
│   │   ├── analysis/                 # SINR, throughput, coverage, CDF, visibility, CZML
│   │   └── Engine/                   # Legacy monolithic simulation scripts
│   ├── examples/                     # Orchestrator demo + network-with-traffic example
│   ├── tests/                        # Comprehensive test suite
│   ├── docs/                         # Technical reports and test plans
│   ├── AGENTS.md                     # Repository guidelines
│   ├── requirements.txt              # Python dependencies
│   └── README.md                     # In-package documentation
├── docs/                             # Symlinked or copied docs
├── optimal-lap-altitude-for-maximum-coverage-cxwkq883q5.pdf  # Reference paper
```

### The Orchestrator

The main entry point is `Aether-3D/examples/3D_network_with_traffic.py`. It
implements:

- **`SimulationConfig`** — A single dataclass with 100+ fields covering all
  constellation, transmission, channel, traffic, execution, and extension-layer
  parameters.
- **`SimLayer`** (ABC) — Base class for simulation layers. Each layer has
  `configure()`, `_configure()` (one-time setup), `_configure_pass()` (per-pass
  setup), `begin_pass()`/`end_pass()`, and `step(ctx)` (called per millisecond,
  returns a dict fragment merged into the shared context).
- **`NetworkSimulation`** — The fluent orchestrator. Provides `with_*()` methods
  (`with_constellation()`, `with_ground_station()`, `with_fading()`,
  `with_traffic()`, `with_haps()`, `with_base_stations()`, `with_czml()`, etc.)
  that return `self` for chaining. Custom layers can be added via
  `add_layer()`.

#### Default Layer Order

| # | Layer | Name | Responsibility |
|---|-------|------|----------------|
| 1 | `GeometryLayer` | `geometry` | Constellation, satellite position, visibility, orbital elements, elevation/azimuth angles |
| 2 | `FadingLayer` | `fading` | Shadowed-Rician small-scale fading with Doppler modes |
| 3 | `ShadowingLayer` | `shadowing` | AR(1) large-scale shadow fading |
| 4 | `TrafficLayer` | `traffic` | Packet generation for satellites, HAPS, BSs |
| 5 | `HAPSLayer` | `haps` | HAPS trajectory, fading, shadowing, interference |
| 6 | `BaseStationLayer` | `base_station` | BS positions, pathloss, Rician fading, interference |
| 7 | `InterferenceLayer` | `interference` | FSPL, atmospheric loss, SINR computation |

#### Extension Layers (optional, add via `with_*()` methods)

| Layer | Wraps | Purpose |
|-------|-------|---------|
| `GEOLayer` | `LEO_GEO.GEO()` | GEO satellite support |
| `AirObjectsLayer` | `Air` class | Air-to-ground LoS/pathloss |
| `FrequencySelectiveLayer` | `FrequencySelectiveFadingSimulation` | Frequency-selective fading (subcarriers + delay spread) |
| `PPPInterferenceLayer` | — | Poisson point process interference from HAPS terminals |
| `GaussianFieldLayer` | `gstools` SRF | Spatial channel correlation |
| `AtmosphericLossLayer` | `Atmospheric_loss` | ITU-R cloud/rain/gas/scintillation models |
| `SatelliteCellGeomLayer` | `satellite_cell_geom.py` | Hexagonal cell footprints |
| `NTNFadingLayer` | `FadingSimulation_Non_terrestrial` | NTN-specific small-scale fading |
| `ConstellationLayer` | `constellation.py` | Legacy constellation creation |
| `SphereUtilLayer` | `sphere_util.py` | Uniform sphere point distribution |
| `BaseFadingLayer` | `FadingSimulation` | Base fading simulation |

> **Note:** The Python package directory is named `3DANTS` (starts with a digit),
> so it cannot be imported with a plain `import` statement. All imports use
> `importlib.import_module("3DANTS.module")`.

### Channel Models

**Shadowed-Rician Composite Fading** (3GPP TR 38.811 Loo model):
```
H[t] = H_Rician[t] + H_Nakagami[t] · exp(-j·2π·d·fc/c)
```
- `H_Rician`: Temporally-correlated Jakes/Clarke model (sum of N sinusoids)
- `H_Nakagami`: Nakagami-m envelope (Gamma-distributed), rank-matched to a
  slow-varying Rayleigh reference for temporal structure
- Distribution parameters (b₀, m, Ω, K) from 3GPP TR 38.811 elevation-angle
  polynomial fits

**Three Doppler Modes** (affect temporal correlation only, not marginal distribution):
- **`full`** — True orbital Doppler: `fd = |v_LOS|·fc/c`. Tc ≈ 5–7 µs at S-band.
- **`compensated`** — UE residual Doppler after satellite pre-compensation.
  Pedestrian 1.5 m/s → Tc ≈ 34 ms.
- **`scaled`** — Back-calculated from target coherence time via Clarke's formula.

**AR(1) Shadow Fading** (3GPP TR 38.811):
```
s₀ ~ N(0, σ²)
sₗ = φ·sₗ₋₁ + √(1-φ²)·gₗ,  φ = exp(-1/τ)
```
σ_SF from 3GPP lookup tables (S-band / Ka-band, LoS / NLoS) as a function of
elevation angle.

**Atmospheric Attenuation** (ITU-R models):
Cloud (P.840-3), rain, gas (oxygen + water vapor), tropospheric scintillation,
and ionospheric scintillation.

---

## Installation

### Dependencies

All dependencies are listed in `Aether-3D/requirements.txt`:

```bash
pip install -r Aether-3D/requirements.txt
```

Key dependencies: skyfield, sgp4, numpy, scipy, sympy, pandas, pyproj, shapely,
scikit-learn, gstools, matplotlib, progress, pytest.

Python 3.12+ is recommended.

---

## Quick Start

### Run the orchestrator demo

```bash
cd Aether-3D
python examples/orchestrator_demo.py             # small run
python examples/orchestrator_demo.py --steps 5    # more passes
python examples/orchestrator_demo.py --verbose    # per-ms progress
```

### Run the full network-with-traffic simulation

```bash
cd Aether-3D
python examples/3D_network_with_traffic.py --steps 10 --verbose
```

### Reconfigure via the fluent API

```python
from importlib import import_module
_sim = import_module("3D_network_with_traffic")
NetworkSimulation = _sim.NetworkSimulation
SimulationConfig = _sim.SimulationConfig

sim = (NetworkSimulation(SimulationConfig(
    num_sat=48, num_planes=4, f=2.5e9, steps=10,
    time_start=(2022, 9, 22, 0, 0, 0),
    time_end=(2022, 9, 22, 0, 30, 0),
))
 .with_constellation(num_sat=48, num_planes=4, inclination=60)
 .with_ground_station(lat=53.110987, lon=8.851239)
 .with_fading(mode="compensated")
 .with_traffic(num_sat=40, haps_rate=10, bs_rates=(10, 8, 5))
 .with_haps(height=10.0, velocity=25.0)
 .with_base_stations(n=3)
 .with_czml("/tmp/3dants.czml"))

sim.run()
results = sim.results
print(results.p_rx[["P_rx_at_User (dBW)", "SNR (dB)", "SINR (dB)"]])
```

---

## Analysis

The `3DANTS.analysis` sub-package provides reusable, framework-independent utilities:

```python
from importlib import import_module
_analysis = import_module("3DANTS.analysis")

# SINR
sinr = _analysis.compute_sinr(p_rx_db, noise_power_db, interference_db)
summary = _analysis.sinr_summary(df, column="SINR (dB)")
outage = _analysis.outage_probability(sinr_db, threshold_db=-5.0)

# Throughput (Shannon-Hartley: B·log2(1+SINR))
avg_tp = _analysis.mean_throughput(sinr_db, bandwidth_hz)
cov = _analysis.coverage_probability(sinr_db, threshold_db=-5.0)

# Visibility
vis = _analysis.compute_simultaneous_visibility(df, t_start, t_end)
summary = _analysis.visibility_summary(df)

# Traffic
models = _analysis.build_traffic_models(duration_s=3600, num_sat=120)

# CZML for CesiumJS
writer = _analysis.CZMLWriter(results)
writer.write("output.czml")
```

---

## Testing

The test suite validates numerical correctness against 3GPP standards and
reference papers:

```bash
cd Aether-3D
python3 -m pytest tests/ -v
```

| Test File | Scope | Tests |
|---|---|---|
| `test_3gpp_numerical.py` | 3GPP channel model numerical correctness | 48 |
| `test_analysis_extended.py` | Analysis sub-package unit tests | 20 |
| `test_simulation.py` | Orchestrator integration tests | 20 |
| `test_LEO_satellite_fading_channel_modes.py` | Fading channel mode tests | — |
| `test_accuracy_fixes.py` | Bug-fix validation (rank-matching, phase) | — |
| `test_all_classes.py` | Full class instantiation tests | — |
| `test_czml_writer.py` | CZML output validation | — |

See `docs/PLAN_3GPP_NUMERICAL_TESTS.md` for the full test plan and
`docs/REPORT_3GPP_NUMERICAL_TESTS.md` for the detailed test report.

---

## Citation

If you use Aether-3D, please cite:

```bibtex
@misc{Aether3D,
  author = {Mohammad Amin Vakilifard and Carsten Bockelmann},
  title = {{Aether-3D: An Open Source System Level Simulator for Unified 3D Networks}},
  howpublished = {\url{https://github.com/ant-uni-bremen/Aether-3D}}
}
```

Or the associated paper:

```bibtex
@article{vakilifarddeep,
  title={Deep Learning Based Link Quality Prediction for Direct-to-Device LEO Communication Under Inter-Constellation Interference},
  author={Vakilifard, Mohammad Amin and Gautam, Pramesh and Bockelmann, Carsten and Dekorsy, Armin}
}
```
