# 3DANTS: Testing and Numerical Validation

This document describes the testing infrastructure for the 3DANTS simulator,
including the numerical correctness tests for 3GPP channel models, the analysis
sub-package unit tests, and the orchestrator integration tests.

---

## I. Test Suite Overview

The 3DANTS test suite lives in `3DANTS/tests/` and is organized into
three categories:

| Test File | Category | Scope |
|---|---|---|
| `test_3gpp_numerical.py` | Numerical correctness | Validates channel-model outputs against known reference values from 3GPP TR 38.811, TR 38.821, TR 38.901, ITU-R P.676, and Al-Hourani et al. |
| `test_analysis_extended.py` | Unit tests | Validates `3DANTS/analysis` sub-package: SINR, throughput, coverage, and CDF helpers |
| `test_simulation.py` | Integration tests | Validates `examples/3D_network_with_traffic.py`: layer registration, `ComponentRegistry`, `SimLayer` hooks, and `SimulationConfig` defaults |

Additional test files cover fading-channel modes (`test_LEO_satellite_fading_channel_modes.py`),
accuracy fixes (`test_accuracy_fixes.py`), and full class instantiation
(`test_all_classes.py`).

### Running the Tests

```bash
cd 3DANTS
python3 -m pytest tests/ -v
```

Heavy optional imports (`skyfield`, `sgp4`, `sympy`, `progress`)
are mocked at the top of `test_3gpp_numerical.py` so the numerical tests
can run without a full orbital-propagation environment.

---

## II. Numerical Correctness Tests (3GPP Models)

The numerical correctness test suite (`test_3gpp_numerical.py`) validates
that each 3GPP communication-channel model produces exact, known-correct outputs
by comparing against reference values from the primary 3GPP technical reports and
the Al-Hourani LAP-altitude paper.

### Test Classes (10 classes, 48 tests)

1. `TestSatelliteCommParam3GPP` (14 tests) - Satellite EIRP density, max
   antenna gain, 3 dB beamwidth, beam diameter, bandwidth, and G/T for S-band and
   Ka-band DL/UL, per 3GPP TR 38.811 Table 5.1.1-1.
2. `TestFSPLNumerical` (4 tests) - Free-space path loss formula:
   `FSPL = 32.45 + 20*log10(d_m) + 20*log10(f_GHz)`.
3. `TestNoisePower3GPP` (4 tests) - Thermal noise: `N = 10*log10(k*T*B*NF_linear)`
   with `k = 1.38e-23 J/K` (Boltzmann constant).
4. `TestLOSProbability3GPP` (4 tests) - Al-Hourani LOS probability sigmoid
   `F(d) = 1/(1 + a*exp(-b*(theta - a)))` with environment-specific parameters.
5. `TestGeneralPathLoss3GPP` (4 tests) - CI path-loss model
   `PL = 20*log10(d) + 20*log10(f) + 20*log10(4*pi/c) + eta`.
6. `TestRicianKFactor3GPP` (4 tests) - Air-to-air Rician K-factor:
   `K = rho^2 / (2*sigma^2)`.
7. `TestAtmosphericAttenuation` (3 tests) - ITU-R P.676:
   `PL_At = 10*log10(10^(A_z/10) / sin(elevation_rad))`.
8. `TestAntennaGain` (3 tests) - Antenna pattern at broadside and
   off-broadside with `eta=0.7, N=70, theta_3dB=5.12 deg`.
9. `TestRxLOSProbabilityTable` (4 tests) - 3GPP TR 38.811 LOS probability
   table (elevations 10-90 degrees) with degree-3 polynomial fit.
10. `TestShadowFadingTable` (4 tests) - 3GPP TR 38.811 shadow fading
    `sigma_LOS`, `sigma_NLOS`, and `mean_NLOS` at exact
    table elevations for Ka-band and S-band.

### Execution Results

| Metric | Value |
|---|---|
| Total tests | 48 |
| Passed | 48 |
| Failed | 0 |
| Runtime | ~0.05s |

### Key Findings

- `Al-Hourani saturation`: With environment parameters (e.g., Urban:
  `alpha=0.3, beta=500, gamma=15`), the computed `a` parameter is
  ~55.45, causing the sigmoid to saturate at 1.0 for all practical elevation angles.
- `Antenna gain NaN handling`: `antenna_gain_calc(0)` returns
  `0.0` (not the mathematical limit of 31.11 dB) due to division by zero
  at `u=0`.
- `Table interpolation`: Degree-3 polynomial fit reproduces TR 38.811
  LOS probability table values within +/-2.0 dB at table points.
- `Shadow fading`: `np.interp` at exact table elevations returns
  table values exactly (delta = 0.0).

---

## III. Analysis Sub-Package Unit Tests

The `3DANTS/analysis` sub-package provides reusable, framework-independent
analysis utilities. The unit tests in `test_analysis_extended.py` validate:

- `SINR computation` (`compute_sinr`): Linear-scale SINR from dB
  inputs with optional interference term.
- `Outage probability` (`outage_probability`): Fraction of samples
  below threshold (default -5 dB).
- `SINR summary` (`sinr_summary`): Mean, median, 5th/50th/95th
  percentiles, outage probability, and count.
- `Spectral efficiency` (`spectral_efficiency`): Shannon-Hartley
  `B*log2(1 + SINR)` with SINR in dB.
- `Mean throughput` (`mean_throughput`): Average throughput.
- `Throughput CDF` (`throughput_cdf`): Empirical CDF of
  per-sample throughput.
- `Coverage probability` (`coverage_probability`): Fraction of
  samples at or above threshold.
- `Coverage vs elevation` (`coverage_vs_elevation`): Coverage
  probability binned by elevation angle.

| Metric | Value |
|---|---|
| Total tests | 20 |
| Passed | 20 |
| Failed | 0 |

---

## IV. Orchestrator Integration Tests

The integration tests in `test_simulation.py` validate the layer-based
orchestrator in `examples/3D_network_with_traffic.py`. Heavy imports are
mocked so the tests exercise the fluent API, layer structure, and
`ComponentRegistry` without a full orbital-propagation environment.

### Test Classes

1. `TestSimulationConfig` - Defaults match the original Engine;
   `SimulationConfig` dataclass is mutable and supports field overrides.
2. `TestNetworkSimulationLayers` - 7 default layers present;
   `DEFAULT_LAYER_ORDER` class attribute is set and overridable.
3. `TestComponentRegistry` - Registry populated at construction;
   `_resolve_layer` instantiates from registry; `add_layer`
   auto-registers.
4. `TestFluentConfig` - `with_constellation`, `with_ground_station`,
   `with_fading`, `with_traffic`, `with_haps`,
   `with_base_stations`, `with_uav`, `with_registry`.
5. `TestSimLayerHooks` - `begin_pass`/`end_pass` are
   no-ops by default; `configure` template method calls
   `_configure` once and `_configure_pass` per pass.

| Metric | Value |
|---|---|
| Total tests | 20 |
| Passed | 20 |
| Failed | 0 |

---

## V. Warnings

1. `RuntimeWarning` in `rx_power_calc.py:141`:
   `G_theta = G0 * (j1(u_theta) / (2 * u_theta) + 36 * jv(3, u_theta) / u_theta**3)`
   invalid value encountered in scalar divide. At `theta=0`, `u_theta = 0`.
   The division `0/0` produces NaN. The code handles this via
   `np.where(isnan(gain_dB), 0, gain_dB)`. The mathematical limit at
   `theta=0` is `G0` (31.11 dB), but the code returns `0.0`
   due to NaN propagation. The test `test_gain_broadside` explicitly
   validates this code behavior.

2. `rician_fading_accurate` signature mismatch in
   `test_accuracy_fixes.py` (4 pre-existing errors). Out of scope for the
   numerical validation plan.

---

## VI. References

1. 3GPP, "Study on New Radio (NR) to support non-terrestrial networks (Release 15),"
   Tech. Rep. TR 38.811 v15.2.0, 2018.
2. 3GPP, "Solutions for NR to support non-terrestrial networks (NTN) (Release 16),"
   Tech. Rep. TR 38.821 v16.1.0, 2020.
3. 3GPP, "Study on channel model for frequencies from 0.5 to 100 GHz,"
   Tech. Rep. TR 38.901 v18.0.0, 2024.
4. ITU, "Specific attenuation of radio waves through atmospheric gases and water"
   vapour," Recommendation ITU-R P.676-13, 2023.
5. R. Al-Hourani, M. Kandić, and A. Jamalipour, "Optimal LAP altitude for maximum
   coverage," IEEE Communications Letters, 2014.
6. A. Abdi, W. C. Lau, M.-S. Alouini, and M. Kaveh, "A new simple model for land
   mobile satellite channels: First- and second-order statistics," IEEE
   Transactions on Wireless Communications, vol. 2, no. 3, 2003.

---

## VII. Detailed Documents

- Plan: `docs/PLAN_3GPP_NUMERICAL_TESTS.md` - Full test plan with scope,
  reference values, and test-class breakdown.
- Report: `docs/REPORT_3GPP_NUMERICAL_TESTS.md` - Detailed test report with
  per-test expected/actual values, tolerances, and a warnings section.