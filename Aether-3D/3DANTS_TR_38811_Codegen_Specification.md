# 3DANTS System-Level Simulator & 3GPP TR 38.811 Compliance Integration Specification

This document serves as a mathematically complete and structurally rigorous integration specification for a **coding agent** to implement or extend the **3DANTS** system-level simulator in strict compliance with the **3GPP TR 38.811 (Release 15) Non-Terrestrial Network (NTN)** channel and physical layer standards.

---

## 1. Unified 3D Network Coordinate Systems & Transformations

To model the physical interactions of space, air, and terrestrial nodes in a unified manner, the simulator must maintain a global frame of reference and dynamically compute local node-specific coordinate apertures [311, 314].

### 1.1 The Global Reference Frame ($\mathcal{G}$)
The global reference frame $\mathcal{G}$ is represented as an Earth-Centered Earth-Fixed (ECEF) coordinate system aligned with the **WGS-84 oblate spheroid model** [324]:
*   **Origin ($O$):** The center of mass of the Earth.
*   **$\mathbf{e}^{\mathcal{G}}_x$ Axis:** Passes through the intersection of the Prime (Greenwich) Meridian and the equatorial plane.
*   **$\mathbf{e}^{\mathcal{G}}_y$ Axis:** Lies in the equatorial plane, pointing $90^\circ$ East longitude.
*   **$\mathbf{e}^{\mathcal{G}}_z$ Axis:** Points along the Earth's rotational axis toward the geographic North Pole.

All node positions are tracked in this frame as Cartesian vectors:
$$\mathbf{p}^{\mathcal{G}}_i(t) = \left[x^{\mathcal{G}}_i(t), y^{\mathcal{G}}_i(t), z^{\mathcal{G}}_i(t)\right]^T \in \mathbb{R}^3$$

### 1.2 The Node Local Coordinate Frame ($\mathcal{L}_i$)
Each mobile node $i$ (e.g., LEO satellite, UAV, HAPS, or ground UE) is assigned a time-varying local reference frame $\mathcal{L}_i(t)$ representing its instantaneous antenna array orientation or boresight pointing vector [324, 328]:
*   **Basis Vectors:** $\{\mathbf{e}^{\mathcal{L}_i}_x(t), \mathbf{e}^{\mathcal{L}_i}_y(t), \mathbf{e}^{\mathcal{L}_i}_z(t)\}$
*   **Orientation Alignment:** Defined by a $3 \times 3$ orthogonal rotation matrix $\mathbf{\Psi}_{\mathcal{G}\to\mathcal{L}_i}(t) \in \mathbb{R}^{3 \times 3}$.

### 1.3 Coordinate Transformations & Angle Extraction
To compute path parameters such as local Angles of Arrival (AOA) and Angles of Departure (AOD) at time step $t_k$, the global position of a target transmitter $j$ must be translated and rotated into the receiver $i$'s local frame $\mathcal{L}_i(t_k)$ [328]:

$$\mathbf{p}^{\mathcal{L}_i}_j(t_k) = \mathbf{\Psi}_{\mathcal{G}\to\mathcal{L}_i}(t_k) \left( \mathbf{p}^{\mathcal{G}}_j(t_k) - \mathbf{p}^{\mathcal{G}}_i(t_k) \right)$$

Let the transformed local Cartesian position be $\mathbf{p}^{\mathcal{L}_i}_j(t_k) = [x, y, z]^T$. The spherical parameters—**slant range ($d_{ij}$)**, **local elevation angle ($\theta^{\mathcal{L}_i}_{el,ij}$)**, and **local azimuth angle ($\phi^{\mathcal{L}_i}_{az,ij}$)**—are extracted using:

$$\begin{aligned}
d_{ij}(t_k) &= \|\mathbf{p}^{\mathcal{G}}_i(t_k) - \mathbf{p}^{\mathcal{G}}_j(t_k)\|_2 \\
\theta^{\mathcal{L}_i}_{el,ij}(t_k) &= \operatorname{arctan2}\left( z, \sqrt{x^2 + y^2} \right) \\
\phi^{\mathcal{L}_i}_{az,ij}(t_k) &= \operatorname{arctan2}(y, x)
\end{aligned}$$

---

## 2. 3GPP TR 38.811 Reference Scenarios & Constants

Your engine must define and expose the standard reference scenarios below to configure simulation loops:

### 2.1 Standard Deployment Lookup Map (Table 5.1-1 Reference)
```python
DEPLOYMENTS = {
    "D1_GEO_VSAT": {
        "orbit_type": "GEO",
        "altitude_km": 35786.0,
        "dl_freq_hz": 19.7e9,  # Ka-band Downlink
        "ul_freq_hz": 29.5e9,  # Ka-band Uplink
        "beam_type": "Earth-fixed",
        "bandwidth_hz": 800e6,
        "terminal_type": "VSAT",
        "min_elevation_deg": 10.0
    },
    "D2_GEO_Handheld": {
        "orbit_type": "GEO",
        "altitude_km": 35786.0,
        "dl_freq_hz": 2.185e9,  # S-band Downlink
        "ul_freq_hz": 1.995e9,  # S-band Uplink
        "beam_type": "Earth-fixed",
        "bandwidth_hz": 20e6,
        "terminal_type": "Handheld_Class_3",
        "min_elevation_deg": 10.0
    },
    "D3_LEO_Handheld": {
        "orbit_type": "LEO",
        "altitude_km": 600.0,   # Minimum pessimistic altitude
        "dl_freq_hz": 2.185e9,  # S-band
        "ul_freq_hz": 1.995e9,
        "beam_type": "Moving",
        "bandwidth_hz": 20e6,
        "terminal_type": "Handheld_Class_3",
        "min_elevation_deg": 10.0
    },
    "D4_LEO_VSAT": {
        "orbit_type": "LEO",
        "altitude_km": 600.0,
        "dl_freq_hz": 19.7e9,  # Ka-band
        "ul_freq_hz": 29.5e9,
        "beam_type": "Earth-fixed",
        "bandwidth_hz": 800e6,
        "terminal_type": "VSAT",
        "min_elevation_deg": 10.0
    },
    "D5_HAPS": {
        "orbit_type": "HAPS",
        "altitude_km": 20.0,
        "dl_freq_hz": 2.1e9,    # Flexible S-band or mmWave
        "ul_freq_hz": 2.1e9,
        "beam_type": "Earth-fixed",
        "bandwidth_hz": 80e6,   # up to 80MHz mobile, 1800MHz fixed
        "terminal_type": "Handheld_Class_3",
        "min_elevation_deg": 5.0
    }
}
```

### 2.2 Standard Slant Range Geometry validation [89]
When computing path delays, validate the outputs of the coordinate transformation engine against the theoretical geometry of a spherical Earth ($R_E = 6371.0\text{ km}$):
$$d(\alpha) = \sqrt{R_E^2 \sin^2\alpha + h_0^2 + 2h_0R_E} - R_E \sin\alpha$$
where $h_0$ is platform altitude and $\alpha$ is elevation angle [89].

---

## 3. Propagation Loss & Gaseous Channel Models

The total path loss ($PL$) over the trans-stratospheric or spaceborne link must be accumulated as [90]:
$$PL = PL_b + PL_g + PL_s + PL_e$$

### 3.1 Basic Path Loss ($PL_b$)
The basic path loss is computed as [89, 90]:
$$PL_b = FSPL(d_{ij}, f_c) + CL(\theta_{el}, f_c, \text{env}) + SF$$

*   **Free Space Path Loss (FSPL):**
    $$FSPL(d_{ij}, f_c) = 32.45 + 20\log_{10}(f_c) + 20\log_{10}(d_{ij})$$
    *(where $d_{ij}$ is the distance in meters, and $f_c$ is carrier frequency in GHz)* [89].
*   **Clutter Loss ($CL$):** Non-zero for Non-Line-of-Sight (NLOS) conditions, derived directly from 3GPP TR 38.811 lookup tables based on the elevation angle ($\theta_{el}$) [90].

### 3.2 Atmospheric Gas Attenuation ($PL_g$)
Calculated from zenith attenuation ($A_{\text{zenith}}$) using the ITU-R P.676 model, scaled by elevation [91, 92]:
$$PL_g(f, \theta_{el}) = \frac{A_{\text{zenith}}(f)}{\sin(\theta_{el})}$$

### 3.3 Scintillation ($PL_s$)
*   **Ionospheric Scintillation (f < 6 GHz):**
    Computes amplitude fluctuations $A_{IS}$ based on the scintillation index $S_4$ [95]:
    $$P_{\text{fluc}} = 27.5 S_4^{1.26} \implies A_{IS} = \frac{P_{\text{fluc}}}{\sqrt{2}}$$
*   **Tropospheric Scintillation (f > 6 GHz):**
    Derived using ITU-R P.618, implementing Toulouse reference CDF curves for Ka-band links [97, 98].

---

## 4. Temporally Correlated Shadow Fading Engine

To model overflight shadowing transitions smoothly instead of utilizing static terrestrial spatial correlation models, implement the **3DANTS exponential recursive decay autocorrelation engine** [317, 318].

### 4.1 Recursive Correlated Gaussian Generator
For each overflight step $l$ representing a dynamic elevation angle step, the shadowing sequence $s_l$ is derived from an i.i.d. zero-mean Gaussian sequence using a first-order autoregressive process [318]:

$$s_l = \phi(l) s_{l-1} + \sqrt{1 - \phi(l)^2} w_l$$

where:
*   $w_l \sim \mathcal{N}\left(0, \sigma^2_{SF}(\theta_{el}(t_l))\right)$ represents the target standard deviation at the current elevation angle [318].
*   $\phi(l) = e^{-1/\tau_s}$ is the temporal correlation coefficient [318].
*   $\tau_s = \Delta t_L / \text{TTI}$ is the correlation time in time steps required for an elevation angle increment of $1^\circ$ to $5^\circ$ over LEO overflight trajectories [318].

---

## 5. LMS S-Band Flat Fast Fading (Shadowed Rician / Abdi Model)

For link-level evaluations in the S-band, flat fast fading is generated using the **Shadowed Rician (Abdi) distribution**, representing combined line-of-sight (LOS) shadowing and diffuse scattering [320, 321]:

### 5.1 Fading Envelope PDF
The probability density function (PDF) of the flat channel gain envelope $\gamma(t) = |h(t)|$ is [321]:

$$f_{\Gamma}(\gamma) = \left( \frac{2b_0 m}{2b_0 m + \Omega} \right)^m \frac{\gamma}{b_0} \exp\left( -\frac{\gamma^2}{2b_0} \right) \cdot {_1F_1}\left( m, 1, \frac{\Omega \gamma^2}{2b_0(2b_0 m + \Omega)} \right), \quad \gamma \ge 0$$

where:
*   $2b_0$: Average power of the multipath scatter component [321].
*   $m$: Nakagami-m parameter representing the severity of shadowing on the LOS component [321, 322].
*   $\Omega$: Average power of the coherent LOS component [322].
*   ${_1F_1}(a, b, x)$: Confluent hypergeometric function of the first kind [322].

### 5.2 Elevation-Dependent Polynomial Parameter Equations
The channel parameters are dynamically updated as cubic polynomials of the platform elevation angle $\theta_{el}$ in degrees [322]:

$$\begin{aligned}
b_0(\theta_{el}) &= -4.7943 \times 10^{-8} \theta_{el}^3 + 5.5784 \times 10^{-6} \theta_{el}^2 - 2.1344 \times 10^{-4} \theta_{el} + 3.2710 \times 10^{-2} \\
m(\theta_{el}) &= \phantom{-}6.3739 \times 10^{-5} \theta_{el}^3 + 5.8533 \times 10^{-4} \theta_{el}^2 - 1.5973 \times 10^{-1} \theta_{el} + 3.5156 \\
\Omega(\theta_{el}) &= \phantom{-}1.4428 \times 10^{-5} \theta_{el}^3 - 2.3798 \times 10^{-3} \theta_{el}^2 + 1.2702 \times 10^{-1} \theta_{el} - 1.4864
\end{aligned}$$

---

## 6. MIMO Polarization Coupling & Faraday Rotation

For dual-polarized MIMO channels traversing the trans-ionospheric segment, your physical link engine must apply **Faraday rotation** to model polarization plane twisting [234, 235].

### 6.1 Matrix Post-Multiplication
To generate the $2 \times 2$ polar antenna channel matrix $\mathbf{H}_{u,s,n,m}(t_k)$ for the $m$-th path in the $n$-th cluster, post-multiply the base spatial matrix by the Faraday rotation matrix $\mathbf{F}_r$ [234, 235]:

$$\mathbf{H}^{\text{NLOS}}_{u,s,n,m}(t) = \mathbf{H}_{\text{base}}(t) \cdot \mathbf{F}_r$$

### 6.2 Matrix Construction
$$\mathbf{F}_r = \begin{bmatrix} \cos(\psi) & \sin(\psi) \\ \sin(\psi) & \cos(\psi) \end{bmatrix}$$

$$\psi = \frac{108}{f_c^2} \text{ degrees}$$
where $f_c$ is the carrier frequency in GHz [237].

---

## 7. Timing Advance & HARQ Sizing Thresholds

Non-terrestrial propagation distances impose extreme round-trip times (RTTs) that exhaust traditional terrestrial physical layer buffers. Your link synchronization module must enforce the minimum required parallel HARQ processes ($N_{\text{HARQ, min}}$) [268]:

$$N_{\text{HARQ, min}} \ge \frac{T_{\text{HARQ}}}{T_{\text{slot}}}$$

### 7.1 Buffer and Process Constraints (TR 38.811 Section 7.3.3.1.1)
The simulator must restrict parallel processes and feedback queues according to the logical limits below:

| Link Scenario | Max Target RTT ($T_{\text{HARQ}}$) | Standard Subcarrier Spacing | Minimum Required Processes |
| :--- | :--- | :--- | :--- |
| **Terrestrial Reference** | $16\text{ ms}$ | $15\text{ kHz}$ | **16** |
| **LEO Orbit (600 km)** | $50\text{ ms}$ | $15\text{ kHz}$ | **50** |
| **MEO Orbit (10,000 km)** | $180\text{ ms}$ | $15\text{ kHz}$ | **180** |
| **GEO Orbit (35,786 km)** | $600\text{ ms}$ | $15\text{ kHz}$ | **600** |

---

## 8. Link-Level Calibration Reference: NTN-CDL-C LOS Profile

To calibrate and benchmark your link evaluations, the code must support the standardized **3GPP NTN-CDL-C** channel model at the default reference elevation of $50^\circ$ [244]:

```python
NTN_CDL_C_REFERENCE_50_DEG = {
    "reference_elevation_deg": 50.0,
    "clusters": [
        {
            "id": 1,
            "type": "Specular(LOS path)",
            "normalized_delay": 0.0,
            "power_db": -0.394,
            "AOD": 0.0, "AOA": -180.0, "ZOD": 140.0, "ZOA": 40.0
        },
        {
            "id": 1,
            "type": "Laplacian(LOS diffuse)",
            "normalized_delay": 0.0,
            "power_db": -10.618,
            "AOD": 0.0, "AOA": -180.0, "ZOD": 140.0, "ZOA": 40.0
        },
        {
            "id": 2,
            "type": "Laplacian(NLOS cluster)",
            "normalized_delay": 14.8124,
            "power_db": -23.373,
            "AOD": 0.0, "AOA": -75.9, "ZOD": 140.0, "ZOA": 87.1
        }
    ],
    "scaling_coefficients": {
        "cASD": 0.0, "cASA": 11.0, "cZSD": 0.0, "cZSA": 7.0, "XPR_db": 16.0
    }
}
```

---

## 9. Dynamic Interference (SINR) Evaluation

The physical layer simulator engine must evaluate the signal-to-interference-plus-noise ratio ($SINR$) for each link $i \to j$ at time step $t_k$ according to the dynamic activity state ($\delta_\nu$) dictated by the traffic patterns (CBR, Poisson, or Bursty) [329]:

$$SINR_{ij}(t_k) = \frac{P_{\text{RX}, ij}(t_k)}{\sum_{\nu \in J \setminus \{j\}} \delta_\nu(t_k) P_{\text{Int}, i\nu}(t_k) + N_i(t_k)}$$

where:
*   $\delta_\nu(t_k) \in \{0, 1\}$ represents the activity state of interferer $\nu$ [329].
*   $P_{\text{Int}, i\nu}(t_k)$ is the received interference power from node $\nu$ at node $i$ [329].
*   $N_i(t_k)$ is the receiver noise power computed from thermal noise temperature $T_{\text{noise}}$ [326, 329].

---

## 10. Numerical Validation and Testing

The 3DANTS code generation specification is validated against known 3GPP
reference values. The numerical correctness test suite (tests/test_3gpp_numerical.py)
validates each channel model formula against tables in 3GPP TR 38.811
(Table 5.1.1-1: satellite EIRP, antenna gain, beamwidth, bandwidth, G/T),
3GPP TR 38.821, ITU-R P.676 (atmospheric attenuation), and the Al-Hourani
et al. LOS probability and CI path loss models.

### Reference Documents

1. 3GPP TR 38.811 v15.2.0 (2018) - NR support for non-terrestrial networks
2. 3GPP TR 38.821 v16.1.0 (2020) - Solutions for NR to support NTN
3. 3GPP TR 38.901 v18.0.0 (2024) - Channel model for 0.5-100 GHz
4. ITU-R P.676-13 (2023) - Attenuation due to atmospheric gases and water vapour
5. Al-Hourani et al. (2014) - Optimal LAP altitude for maximum coverage

### Test Artifacts

- docs/PLAN_3GPP_NUMERICAL_TESTS.md - Full test plan
- docs/REPORT_3GPP_NUMERICAL_TESTS.md - Detailed test report
- docs/3DANTS_Testing_and_Numerical_Validation.md - Test suite overview
