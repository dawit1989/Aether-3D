# Plan: Numerical Correctness Tests for 3GPP Models

## Objective

Create tests/test_3gpp_numerical.py -- a comprehensive test suite that validates
the numerical correctness of the 3GPP communication-channel models against known
reference values from 3GPP TR 38.811 / 38.821. These tests pin down exact
formula outputs (not just range/monotonicity checks) so regressions are caught
immediately.

## Scope

### In Scope
1. Satellite_communication_parameter.parameters() -- exact EIRP density, max gain,
   3 dB beamwidth, beam diameter, bandwidth, and G/T values for S/Ka-band DL/UL.
2. Air.LoS_calculator() -- exact Al-Hourani sigmoid LOS probability values.
3. Air.general_pathloss_calculator() -- exact LoS/NLoS path loss for known inputs.
4. Air.air2air_K_calculator() -- exact Rician K-factor formula.
5. Rx_power.FSPl_only() -- exact free-space path loss.
6. Rx_power.Noise_power_with_NoiseFigure() -- exact noise power N = kTB * NF.
7. Rx_power.atmospheric_att() -- exact atmospheric attenuation.
8. Rx_power.antenna_gain_calc() -- exact antenna gain at broadside.
9. Rx_power.LOS_prob_calc() -- exact 3GPP table-derived LOS probability.

### Out of Scope (Explicitly)
- rician_fading_accurate signature mismatch in test_accuracy_fixes.py
  (4 pre-existing errors -- does not block this plan).
- Skyfield/SGP4 orbital propagation (mocked as in existing tests).
- Any changes to production source files.

## Reference Values

### Satellite Parameters (3GPP TR 38.811 Table 5.1.1-1)

| Band | Direction | EIRP density (dBW/MHz) | Max gain (dBi) | 3 dB beamwidth (deg) | Beam dia (km) | Bandwidth (MHz) |
|------|-----------|------------------------|-----------------|----------------------|---------------|------------------|
| S    | DL        | 34                     | 30              | 4.4127               | 50            | 30               |
| Ka   | DL        | 40                     | 38.5            | 1.7647               | 20            | 400              |
| S    | UL        | --                     | --              | --                   | --            | G/T = 1.1 dB/K   |
| Ka   | UL        | --                     | --              | --                   | --            | G/T = 13 dB/K    |

### FSPL Formula

  FSPL = 32.45 + 20*log10(d_m) + 20*log10(f_GHz)
       = 20*log10(4*pi*d*f / c)

Test case: f = 2.5 GHz, d = 100 km (d_m = 100000)
  Code formula: 32.45 + 20*log10(100000) + 20*log10(2.5) = 140.41 dB
  Exact: 20*log10(4*pi*100000*2.5e9 / 3e8) = 140.40 dB

### Noise Power (3GPP: kTB * NF)

  N = k * T * B * NF_linear    (linear)
  N_dB = 10*log10(k * T * B * NF_linear)

Test case: k = 1.38e-23, T = 290 K, B = 30 MHz, NF = 7 dB
  NF_linear = 10^(0.7) = 5.0119
  P_thermal = 1.38e-23 * 290 * 30e6 = 1.2006e-13 W
  P_noise = 10*log10(5.0119 * 1.2006e-13) = -122.21 dBW

### LOS Probability (Al-Hourani)

Environment-specific alpha/beta/gamma:
  Suburban:     alpha=0.1, beta=750, gamma=8
  Urban:        alpha=0.3, beta=500, gamma=15
  DenseUrban:   alpha=0.5, beta=300, gamma=20
  HighriseUrban:alpha=0.5, beta=300, gamma=50

  Prob_LoS = 1 / (1 + a * exp(-b * (elevation_rad - a)))

Note: With these environment parameters, a ~ 15-73 (large), so the
sigmoid saturates at 1.0 for all practical elevation angles.
Test: Urban at 45 deg ~= 1.0 (within 1e-6).
Test: Suburban at 90 deg = 0.9999 (slightly below 1.0).
Test: probability is monotonically decreasing with elevation for Suburban.

### General Path Loss (Al-Hourani CI Model)

  PL = 20*log10(d_m) + 20*log10(f_Hz) + 20*log10(4*pi/c) + eta

| Environment   | eta_LoS | eta_NLoS |
|---------------|---------|----------|
| Suburban      | 0.1     | 21       |
| Urban         | 1       | 20       |
| Denseurban    | 1.6     | 23       |
| Highriseurban | 2.3     | 34       |

Test case: Urban, d=2 km (d_m=2000), f=2.5 GHz
  PL_LoS = 66.02 + 187.96 + (-147.56) + 1 = 107.42 dB
  PL_NLoS = 66.02 + 187.96 + (-147.56) + 20 = 126.42 dB

### Air-to-Air Rician K-Factor

  sigma = 212.3 * |h1 - h2|^(-2.221) + 1.289
  K = rho_direct^2 / (2 * sigma^2)

Test case: h1=100, h2=200, rho=0.5
  |h1-h2| = 100
  100^(-2.221) = 3.614e-5
  sigma = 212.3 * 3.614e-5 + 1.289 = 1.2967
  K = 0.25 / (2 * 1.2967^2) = 0.25 / 3.363 = 0.0743

### Atmospheric Attenuation (ITU-R P.676)

  PL_At = 10*log10(10^(A_z/10) / sin(elevation_rad))

Test case: A_z=1 dB, elevation=30 deg
  10^(0.1) = 1.2589, sin(30 deg) = 0.5
  PL_At = 10*log10(1.2589 / 0.5) = 10*log10(2.5179) = 4.01 dB

### Antenna Gain

  eta=0.7, N=70, theta_3dB=5.12 deg
  G0 = (eta * N^2 * pi^2) / theta_3dB^2
  u(theta) = 2.07123 * sin(theta_rad) / sin(theta_3dB_rad)
  G(theta) = G0 * (j1(u)/(2*u) + 36*jv(3,u)/u^3)

Test case: theta=0 deg (u=0, use L Hopital limits)
  G0 = (0.7 * 4900 * pi^2) / 5.12^2 = 1291.38
  G(0) = G0 * (1/4 + 3/4) = G0 * 1.0 = 1291.38
  gain_dB = 10*log10(1291.38) = 31.11 dB

### 3GPP Table-based LOS Probability (Rx_power.LOS_prob_calc)

Table elevations: [10, 20, 30, 40, 50, 60, 70, 80, 90]

| Elev | Dense_Urban | Urban | Sub_Urban |
|------|-------------|-------|-----------|
| 10   | 28.2        | 24.6  | 78.2      |
| 20   | 33.1        | 38.6  | 86.9      |
| 30   | 39.8        | 49.3  | 91.9      |
| 40   | 46.8        | 61.3  | 92.9      |
| 50   | 53.7        | 72.6  | 93.5      |
| 60   | 61.2        | 80.5  | 94.0      |
| 70   | 73.8        | 91.9  | 94.9      |
| 80   | 82.0        | 96.8  | 95.2      |
| 90   | 98.1        | 99.2  | 99.8      |

Polynomial fit (degree 3) should reproduce within +/- 1.5 dB at table points.


### Shadow Fading Lookup Tables (3GPP TR 38.811)

SF_LOS_calc uses 3GPP TR 38.811 table values for sigma_LOS, sigma_NLOS, and
mean_NLOS at each 10-degree elevation bin. The polynomial/linear interpolation
should reproduce these table values at the exact elevation points.

Ka-band:
  y_los  (sigma_LOS):   [1.9, 1.6, 1.9, 2.3, 2.7, 3.1, 3.0, 3.6, 0.4]
  y_nlos (sigma_NLOS):  [10.7, 10.0, 11.2, 11.6, 11.8, 10.8, 10.8, 10.8, 10.8]
  cl_nlos (mean_NLOS):  [29.5, 24.6, 21.9, 20.0, 18.7, 17.8, 17.2, 16.9, 16.8]

S-band:
  y_los  (sigma_LOS):   [1.79, 1.14, 1.14, 0.92, 1.42, 1.56, 0.85, 0.72, 0.72]
  y_nlos (sigma_NLOS):  [8.93, 9.08, 8.78, 10.25, 10.56, 10.74, 10.17, 11.52, 11.52]
  cl_nlos (mean_NLOS):  [19.52, 18.17, 18.42, 18.28, 18.63, 17.68, 16.50, 16.30, 16.30]

Table elevations: [10, 20, 30, 40, 50, 60, 70, 80, 90]

Test: At exact table elevations, np.interp should return the table values.

### Rician Factor from Elevation Angle

  K0_lin = 10^(K0_db/10)
  K_pi_half_lin = 10^(K_pi_half_db/10)
  a3 = K0_lin
  b3 = (2/pi) * ln(K_pi_half_lin / K0_lin)
  K = a3 * exp(b3 * deg2rad(elevation_angle))

Test case: K0=-10 dB, K_pi/2=10 dB, elevation=45 deg
  K0_lin = 0.1, K_pi_half_lin = 10
  a3 = 0.1
  b3 = (2/pi) * ln(100) = 2.933
  K = 0.1 * exp(2.933 * 0.7854) = 0.1 * 9.914 = 0.991

## Test File: tests/test_3gpp_numerical.py

### Header and Imports
- Mock heavy imports: skyfield, sgp4, sympy, progress
- sys.path.insert for 3DANTS/Communication channel
- Import Satellite_communication_parameter, Air, Rx_power

### Test Classes (10 classes, ~44 tests)

1. TestSatelliteCommParam3GPP (12 tests) -- exact satellite parameter values
2. TestFSPLNumerical (4 tests) -- FSPL formula correctness
3. TestNoisePower3GPP (4 tests) -- noise power N=kTB*NF
4. TestLOSProbability3GPP (5 tests) -- Al-Hourani LOS probability
5. TestGeneralPathLoss3GPP (4 tests) -- general path loss CI model
6. TestRicianKFactor3GPP (4 tests) -- Rician K-factor formula
7. TestAtmosphericAttenuation (3 tests) -- atmospheric attenuation
8. TestAntennaGain (3 tests) -- antenna gain at broadside
9. TestRxLOSProbabilityTable (4 tests) -- 3GPP table-based LOS probability
10. TestShadowFadingTable (4 tests) -- 3GPP TR 38.811 shadow fading tables

### Main Block

if __name__ == "__main__":
    unittest.main(verbosity=2)

## Execution

  cd 3DANTS
  python tests/test_3gpp_numerical.py -v

## File Encoding
UTF-8 without BOM (consistent with all existing test files)
