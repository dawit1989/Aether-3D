# 3GPP TR 38.811 (Release 15) Technical Specification Report: NR Support for Non-Terrestrial Networks (NTN)

---

## 1. Reference Deployment Scenarios and Platform Characteristics

3GPP TR 38.811 down-selects five primary deployment scenarios to evaluate 5G New Radio (NR) performance across spaceborne and airborne non-terrestrial layers [97]. These scenarios balance the tradeoffs between frequency bands (S-band vs. Ka-band), platform orbits, and terminal capabilities [98, 99].

### Table 1.1: 3GPP NTN Reference Scenario Matrix

| Scenario Attribute | Deployment-D1 | Deployment-D2 | Deployment-D3 | Deployment-D4 | Deployment-D5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Orbit & Altitude** | GEO (35,786 km) | GEO (35,786 km) | LEO (600 - 1500 km) | LEO (600 - 1500 km) | HAPS (8 - 50 km) |
| **Carrier Frequency** | Ka-band (20/30 GHz) | S-band (2 GHz) | S-band (2 GHz) | Ka-band (20/30 GHz) | S/Ka-band (below/above 6 GHz) |
| **Beam Pattern** | Earth-Fixed | Earth-Fixed | Moving / Steerable | Earth-Fixed | Earth-Fixed |
| **Duplexing Mode** | FDD | FDD | FDD | FDD | FDD |
| **Channel Bandwidth** | Up to $2 \times 800\text{ MHz}$ | Up to $2 \times 20\text{ MHz}$ | Up to $2 \times 20\text{ MHz}$ | Up to $2 \times 800\text{ MHz}$ | Up to $2 \times 80\text{ MHz}$ (mobile)<br>Up to $2 \times 1800\text{ MHz}$ (fixed) |
| **Terminal Type** | VSAT (Indirect access) | Handheld / IoT (Direct) | Handheld / IoT (Direct) | VSAT (Indirect access) | Mixed (Handheld & VSAT) |
| **Terminal Power Class** | 33 dBm (2W) | 23 dBm (200mW) | 23 dBm (200mW) | 33 dBm (2W) | Mixed |
| **Terminal Mobility** | Up to 1000 km/h | Up to 1000 km/h | Up to 1000 km/h | Up to 1000 km/h | Up to 500 km/h |

---

## 2. Slant Range and Propagation Delay Geometry

### 2.1. Slant Range Formulation
The physical line-of-sight distance (slant range) $d$ between a ground-based terminal and a satellite/HAPS platform orbiting at an altitude $h_0$ above a spherical Earth with radius $R_E \approx 6371\text{ km}$ is calculated as a function of the local elevation angle $\alpha$ [158, 169]:

$$d = \sqrt{R_E^2 \sin^2 \alpha + h_0^2 + 2 h_0 R_E} - R_E \sin \alpha$$

```
                   Satellite / HAPS (h0)
                        o
                       /|
                      / |
                  d  /  |
                    /   |
                   /    |
                  /     |
                 o------|---------------- horizon
             Terminal   |
               (RE)     |
                 \      |
                  \     |
                   \    |
                    \   |
                     \  |
                      \ |
                       \|
                        o Center of Earth (O)
```

### 2.2. Standardized Propagation and Round-Trip Delay Profiles
Using the speed of light $c \approx 2.99792 \times 10^8\text{ m/s}$ over the calculated slant range, 3GPP defines the baseline propagation and Round-Trip Time (RTT) delay metrics (at $10^\circ$ terminal elevation) [135, 136]:

*   **GEO Satellites ($h_0 = 35,786\text{ km}$):**
    *   *Bent-pipe Payload (Double Hop Gateway-Satellite-UE):* One-way delay $T_{propagation} = 272.37\text{ ms}$, leading to a network loop RTT of **$544.75\text{ ms}$** [118].
    *   *Regenerative Payload (Single Hop UE-Satellite):* One-way delay $T_{propagation} = 135.28\text{ ms}$, leading to an on-board processed RTT of **$270.57\text{ ms}$** [118].
*   **LEO Satellites ($h_0 = 600\text{ km}$):**
    *   *Bent-pipe Payload (Double Hop):* One-way delay $T_{propagation} = 14.20\text{ ms}$, RTT of **$28.41\text{ ms}$** [136].
    *   *Regenerative Payload (Single Hop):* One-way delay $T_{propagation} = 6.44\text{ ms}$, RTT of **$12.88\text{ ms}$** [136].
*   **HAPS Platforms ($h_0 = 20\text{ km}$):**
    *   One-way delay $T_{propagation} = 1.52\text{ ms}$, RTT of **$3.05\text{ ms}$** [132].

### 2.3. Differential Beam Delay
The differential propagation delay $\Delta T$ describes the delay spread experienced across the physical footprint of a single satellite beam [110]:

$$\Delta T = \frac{d_{Edge} - d_{Nadir}}{c}$$

This differential delay determines the length of the guard windows required during random access [442, 443]. For a standard LEO satellite at $600\text{ km}$ altitude, the maximum one-way differential delay is **$4.44\text{ ms}$**, which represents a significant fraction ($67\%$) of the maximum single-hop delay [137, 138]. For GEO platforms, the differential delay reaches up to **$16\text{ ms}$** [119].

---

## 3. Doppler Shift and Variation Rate Dynamics

### 3.1. General Doppler Shift Equation
The Doppler frequency shift $\Delta F$ caused by relative radial velocity $V$ between the transmitter and receiver operating at nominal carrier frequency $F_0$ is defined as [114]:

$$\Delta F = F_0 \frac{V}{c} \cos(\theta)$$

Where $\theta$ represents the angle between the velocity vector of the platform/terminal and the direction of wave propagation [114].

### 3.2. Geometrical Dynamic Doppler Shift Model
For non-geostationary satellites moving rapidly on a circular orbit, the Doppler shift $f_d(t)$ as a function of time can be analytically derived using Cartesian vectors in the y-z plane [146, 147]:

$$f_d(t) = \frac{f_0}{c} \cdot \frac{\mathbf{d}(t)}{|\mathbf{d}(t)|} \cdot \frac{\partial \mathbf{x}_{SAT}(t)}{\partial t}$$

Where:
*   The satellite position vector $\mathbf{x}_{SAT}(t)$ is [147]:
    $$\mathbf{x}_{SAT}(t) = \left[ 0, \ (R_E + h) \sin(\omega_{SAT} t), \ (R_E + h) \cos(\omega_{SAT} t) \right]$$
*   The relative distance vector $\mathbf{d}(t)$ to a stationary ground terminal is [147]:
    $$\mathbf{d}(t) = \left[ 0, \ (R_E + h) \cos(\omega_{SAT} t), \ (R_E + h) \sin(\omega_{SAT} t) - R_E \right]$$
*   The satellite angular orbital velocity $\omega_{SAT}$ is defined by Kepler's third law [147, 149]:
    $$\omega_{SAT} = \sqrt{\frac{G M_E}{(R_E + h)^3}}$$
    *(With $G$ representing the gravitational constant and $M_E$ representing the Earth mass)* [149].

This closed-form formulation simplifies to [149]:

$$f_d(t) = \omega_{SAT} \frac{f_0}{c} R_E \cos\left[ \theta_{el}(t) \right]$$

### 3.3. Standardized Max Doppler Shifts and Drift Rates
For a standard LEO satellite at $600\text{ km}$ altitude ($V \approx 7.56\text{ km/s}$), the physical Doppler variations are summarized below [148, 152]:

*   **S-Band ($2.0\text{ GHz}$):**
    *   Max Doppler Shift: **$\pm 48\text{ kHz}$**
    *   Max Doppler Variation Rate: **$-544\text{ Hz/s}$**
*   **Ka-Band Downlink ($20.0\text{ GHz}$):**
    *   Max Doppler Shift: **$\pm 480\text{ kHz}$**
    *   Max Doppler Variation Rate: **$-5.44\text{ kHz/s}$**
*   **Ka-Band Uplink ($30.0\text{ GHz}$):**
    *   Max Doppler Shift: **$\pm 720\text{ kHz}$**
    *   Max Doppler Variation Rate: **$-8.16\text{ kHz/s}$**

---

## 4. Large-Scale Path Loss and Atmospheric Models

The signal path between the spaceborne platform and the user terminal is modeled as a cumulative series of distinct propagation and environmental attenuation coefficients [168]:

$$PL = PL_b + PL_g + PL_s + PL_e$$

Where:
*   $PL_b$ is the basic path loss (including free space path loss, clutter, and shadow fading) [168].
*   $PL_g$ is the attenuation due to atmospheric gases [168].
*   $PL_s$ is the attenuation due to ionospheric or tropospheric scintillation [168].
*   $PL_e$ is the building entry loss (BEL) [168].

### 4.1. Free Space Path Loss (FSPL)
The basic free-space loss over distance $d$ (meters) and carrier frequency $f_c$ (GHz) is represented as [169]:

$$FSPL(d, f_c) = 32.45 + 20 \log_{10}(f_c) + 20 \log_{10}(d)$$

### 4.2. Basic Path Loss with Shadowing and Clutter
Incorporating land-mobile satellite (LMS) clutter loss ($CL$) and log-normal shadow fading ($SF$) [171]:

$$PL_b = FSPL(d, f_c) + CL(\alpha, f_c) + SF$$

Where $SF \sim \mathcal{N}(0, \sigma_{SF}^2)$ is a zero-mean Gaussian distribution in dB scale [170, 171]. Clutter loss ($CL$) is set to $0\text{ dB}$ under line-of-sight (LOS) conditions [171].

### 4.3. Building Entry Loss (BEL)
The building entry loss distribution is modeled as a combination of two distinct log-normal distributions to reflect traditional vs. thermally efficient (metallized glass, foil-backed panels) construction types [175, 178]:

$$L_{BEL}(P) = 10 \log_{10} \left( 10^{0.1 A(P)} + 10^{0.1 B(P)} + 10^{0.1 C} \right)\text{ dB}$$

Where:
*   $A(P) = F^{-1}(P) \sigma_1 + \mu_1$ [179]
*   $B(P) = F^{-1}(P) \sigma_2 + \mu_2$ [179]
*   $C = -3.0$ [179]
*   $F^{-1}(P)$ is the inverse cumulative normal distribution as a function of the probability $P$ [179].

The parameters scale dynamically with carrier frequency $f$ (GHz) and path elevation angle $\theta$ [179]:

$$\mu_1 = L_h + L_e$$
$$\mu_2 = w + x \log_{10}(f)$$
$$\sigma_1 = u + v \log_{10}(f)$$
$$\sigma_2 = y + z \log_{10}(f)$$

With the horizontal baseline loss $L_h$ and elevation angle correction $L_e$ defined as [179]:

$$L_h = r + s \log_{10}(f) + t \left( \log_{10}(f) \right)^2$$
$$L_e = 0.212 |\theta|$$

### Table 4.1: Building Entry Loss Coefficients

| Building Type | $r$ | $s$ | $t$ | $u$ | $v$ | $w$ | $x$ | $y$ | $z$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Traditional** | 12.64 | 3.72 | 0.96 | 9.6 | 2.0 | 9.1 | -3.0 | 4.5 | -2.0 |
| **Thermally-Efficient** | 28.19 | -3.00 | 8.48 | 13.5 | 3.8 | 27.8 | -2.9 | 9.4 | -2.1 |

### 4.4. Atmospheric Gas Absorption
Zenith gas attenuation $A_{zenith}(f)$ (evaluated using ITU-R P.676 recommendations for dry air pressure $p = 1013.25\text{ hPa}$, temperature $T = 288.15\text{ K}$, and water vapor density $\rho = 7.5\text{ g/m}^3$) is projected to elevation angle $\alpha$ [182, 183]:

$$PL_A(\alpha, f) = \frac{A_{zenith}(f)}{\sin(\alpha)}$$

### 4.5. Scintillation Loss Models

#### 4.5.1. Ionospheric Scintillation (Below 6 GHz)
To characterize amplitude fluctuations (convective plasma processes), the amplitude scintillation index $S_4$ is defined [187, 189]:

$$S_4 = \sqrt{\frac{\langle I^2 \rangle - \langle I \rangle^2}{\langle I \rangle^2}}$$

Where $I$ is signal intensity and $\langle \cdot \rangle$ denotes time-averaging over $60\text{ s}$ [187].
The index scales with carrier frequency according to [190]:

$$S_{4, f_2} = S_{4, f_1} \left( \frac{f_2}{f_1} \right)^{-1.5}$$

Under the equatorial Gigahertz Scintillation Model, the equivalent link loss $A_{IS}$ is calculated from the peak-to-peak amplitude fluctuation $P_{fluc}$ [193, 195]:

$$A_{IS} = \frac{P_{fluc}}{\sqrt{2}}$$
$$P_{fluc} = 27.5 \left( S_4 \right)^{1.26}$$

#### 4.5.2. Tropospheric Scintillation (Above 6 GHz)
Tropospheric scintillation is driven by sudden refractive index variations (temperature, water vapor, pressure) [198]. The scintillation fading depth $SPL$ is modeled as a function of the elevation angle and carrier frequency, scaling proportionally with carrier frequency (unlike ionospheric scintillation) [198]. Standardized reference values at $20\text{ GHz}$ for Toulouse, France define $SPL$ at $99\%$ link availability [201, 202]:

$$SPL_{10^\circ} = 1.08\text{ dB}, \quad SPL_{30^\circ} = 0.30\text{ dB}, \quad SPL_{90^\circ} = 0.12\text{ dB}$$

---

## 5. Statistical Fast Fading Models

### 5.1. Narrowband Flat Fading: ITU Two-State Model
When the channel bandwidth is lower than the coherence bandwidth ($B_c = \frac{1}{10 \tau_{rms}}$) [203], the channel reduces to a single-tap statistical fading process [164, 206]. Fading is modeled using a semi-Markov good-to-bad state transition process with local Loo distributed envelopes [206].

The Good (G) and Bad (B) state duration statistics are modeled using log-normal distributions [208]:

$$\langle dur \rangle_{G,B} = \exp\left( \mu_{G,B} + \frac{\sigma_{G,B}^2}{2} \right) \cdot \frac{1 - \text{erf}\left( \frac{\log(dur_{min, G,B}) - (\mu_{G,B} + \sigma_{G,B}^2)}{\sigma_{G,B} \sqrt{2}} \right)}{1 - \text{erf}\left( \frac{\log(dur_{min,G,B}) - \mu_{G,B}}{\sigma_{G,B} \sqrt{2}} \right)}$$

Inside each state, the probability density function (PDF) of the Loo envelope distribution $p_{Loo}(x)$ is the sum of a log-normally distributed direct line-of-sight component $a$ and a Rayleigh-distributed diffuse multipath component [206, 215]:

$$p_{Loo}(x) = \frac{8.686 x}{\sigma_{Ai} \sqrt{2\pi}} \int_0^\infty \frac{1}{a} \exp\left( - \frac{(20 \log_{10}(a) - M_{Ai})^2}{2 \sigma_{Ai}^2} - \frac{x^2 + a^2}{2 \sigma_i^2} \right) I_0\left( \frac{x a}{\sigma_i^2} \right) da$$

Where:
*   $M_{Ai}$ is the mean power of the direct signal [213].
*   $\sigma_{Ai}$ is the standard deviation of the direct signal [213].
*   $2\sigma_i^2$ is the mean power of the diffuse multipath component, with $MP_i = 10 \log_{10}(2\sigma_i^2)$ [215].
*   $I_0(\cdot)$ is the modified Bessel function of the first kind and zero-th order.

### 5.2. Geometry-Based Stochastic Channel Modeling (GSCM)
For frequency-selective channels, 3GPP TR 38.811 adapts the TR 38.901 model [217]. The delay spread ($DS$), azimuth spread of arrival ($ASA$), and zenith spread of arrival ($ZSA$) are modeled as elevation-dependent parameters. Due to the extreme distance of satellites, the angular departure spreads ($ASD$ and $ZSD$) are set to zero [227, 353]:

$$\mu_{lgASD} = -\infty, \quad \mu_{lgZSD} = -\infty, \quad \sigma_{lgASD} = 0, \quad \sigma_{lgZSD} = 0$$

### 5.3. Faraday Polarization Rotation
For trans-ionospheric links above the ionosphere, Faraday rotation rotates the incoming electromagnetic polarization plane [349]. The channel coefficient matrix $\mathbf{H}_{u,s,n,m}(t)$ for the $m$-th path of the $n$-th cluster is post-multiplied by the polarization rotation matrix $\mathbf{F}_r$ [349, 350]:

$$\mathbf{F}_r = \begin{bmatrix} \cos(\psi_{n,m}) & \sin(\psi_{n,m}) \\ -\sin(\psi_{n,m}) & \cos(\psi_{n,m}) \end{bmatrix}$$

The rotation angle $\psi$ (degrees) is calculated using the central carrier frequency $f_c$ (GHz) [352]:

$$\psi = \frac{108}{f_c^2}$$

### 5.4. Dynamic CDL/TDL Angular Scaling
When executing link-level simulations using Cluster Delay Line (CDL) models, cluster Zenith Angles of Arrival (ZOA) are scaled to match the target elevation angle $\alpha_{desired}$ relative to a reference elevation $\alpha_{model} = 50^\circ$ [354, 355]:

$$\theta_{n, ZOA, scaled} = \frac{ZSA_{desired}}{ZSA_{model}} \left( \theta_{n, ZOA, model} - \mu_{ZOA, model} \right) + \mu_{ZOA, desired} - \Delta \alpha$$

Where $\Delta \alpha = \alpha_{desired} - \alpha_{model}$ [356].

---

## 6. Physical and Higher-Layer Impact Analysis

### 6.1. Parallel HARQ Process Scaling
The long propagation delays over non-terrestrial links drastically alter the timeline of Hybrid Automatic Repeat Request (HARQ) processes [425, 426]. To avoid stalling the uplink transmission pipeline, the minimum required number of parallel HARQ processes ($N_{HARQ, min}$) scales with the Round-Trip Time $T_{HARQ}$ and slot duration $T_{slot}$ [428]:

$$N_{HARQ, min} \ge \frac{T_{HARQ}}{T_{slot}}$$

### Table 6.1: Parallel HARQ Stalling Thresholds (15 kHz SCS / 1 ms slot)

| Platform | $T_{HARQ}$ | $N_{HARQ, min}$ Processes | UE Memory Feasibility (Rel-15) |
| :--- | :--- | :--- | :--- |
| **Terrestrial** | $16\text{ ms}$ | 16 | Fully Feasible (Sufficient) |
| **LEO Orbit** | $50\text{ ms}$ | 50 | Feasible (Requires HARQ protocol extension) |
| **MEO Orbit** | $180\text{ ms}$ | 180 | Critical (Impacts UE buffers and TBS) |
| **GEO Orbit** | $600\text{ ms}$ | 600 | Impractical (Requires HARQ deactivation) |

### 6.2. Timing Advance (TA) Step Sizing
Due to high Doppler drift rates (up to $\dot{f}_{Doppler} \approx -8.16\text{ kHz/s}$ in Ka-band LEO uplink), timing advance tracking must occur at high frequency [148, 413]. The transmission frame offset $T_{TA}$ is calculated using index $I_{TA}$ and basic timing units $T_c$ [409]:

$$T_{TA} = \left( I_{TA} \cdot 16 \cdot 64 \cdot 2^{-\mu} \right) T_c$$

For standard configurations, the required update rates to track LEO orbital motion drift ($35\ \mu\text{s/s}$) are [412, 413]:

$$\text{Update Rate}_{15\text{ kHz SCS}} \approx 10\text{ updates/sec}$$
$$\text{Update Rate}_{120\text{ kHz SCS}} \approx 80\text{ updates/sec}$$

---

## 7. Numerical Validation and Testing

The 3DANTS simulator includes a comprehensive numerical correctness test suite
that validates each 3GPP communication-channel model against known reference
values. The tests pin down exact formula outputs so regressions are caught
immediately.

### 7.1 Test Artifacts

| Document | Description |
|---|---|
| `docs/PLAN_3GPP_NUMERICAL_TESTS.md` | Test plan with scope, reference values, and test-class breakdown |
| `docs/REPORT_3GPP_NUMERICAL_TESTS.md` | Detailed test report with per-test expected/actual values |
| `docs/3DANTS_Testing_and_Numerical_Validation.md` | Overview of the full test suite (numerical, analysis, integration) |

### 7.2 Reference Standards

The numerical validation validates against the following standards and papers:

1. `**3GPP TR 38.811**` — NR support for non-terrestrial networks
   (Release 15). Satellite EIRP, antenna gain, beamwidth, bandwidth, and G/T
   parameters (Table 5.1.1-1), LOS probability tables, and shadow fading tables.
2. `**3GPP TR 38.821**` — Solutions for NR to support non-terrestrial
   networks (NTN) (Release 16).
3. `**3GPP TR 38.901**` — Study on channel model for frequencies from
   0.5 to 100 GHz.
4. `**ITU-R P.676**` — Attenuation due to atmospheric gases and water
   vapour.
5. `**Al-Hourani et al.**` — Optimal LAP altitude for maximum coverage
   (LOS probability and CI path loss models).
6. `**Abdi et al.**` — A new simple model for land mobile satellite
   channels (Rician K-factor).

### 7.3 Test Execution

```bash
cd 3DANTS
python3 -m pytest tests/ -v
```

All 48 numerical tests pass, along with 20 analysis unit tests and 20
orchestrator integration tests.

### 7.4 Validated Models

- `Satellite_communication_parameter.parameters()` — EIRP density,
  max gain, 3 dB beamwidth, beam diameter, bandwidth, G/T (TR 38.811 Table
  5.1.1-1).
- `Air.LoS_calculator()` — Al-Hourani sigmoid LOS probability.
- `Air.general_pathloss_calculator()` — CI path loss model.
- `Air.air2air_K_calculator()` — Air-to-air Rician K-factor.
- `Rx_power.FSPl_only()` — Free-space path loss formula.
- `Rx_power.Noise_power_with_NoiseFigure()` — Thermal noise N = kTB.
- `Rx_power.atmospheric_att()` — ITU-R P.676 atmospheric loss.
- `Rx_power.antenna_gain_calc()` — Antenna gain pattern.
- `Rx_power.LOS_prob_calc()` — 3GPP table-based LOS probability.
- `Rx_power.SF_LOS_calc()` — 3GPP TR 38.811 shadow fading tables.
