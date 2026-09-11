# 3DANTS & 3GPP TR 38.811 (Release 15) Technical Mapping Specification

This document provides a highly detailed, mathematically rigorous mapping specification that details how the **3DANTS system-level simulator** implements, adapts, and extends the channel modeling, deployment scenarios, and physical propagation parameters defined in the **3GPP TR 38.811 (Release 15)** technical report for non-terrestrial networks (NTN).

---

## 1. Reference Deployment Scenarios Mapping

3GPP TR 38.811 defines five core reference scenarios (D1 through D5) that span different orbits, frequency bands, and terminal types [8, 54]. The 3DANTS simulator is designed with a modular architecture to support all five scenarios natively through parameterized configurations in its **Position and Mobility** and **Communication Channel** modules [321, 338, 340].

### Scenario Parameters Comparison Table

| Attribute | 3GPP TR 38.811 Reference [55, 58] | 3DANTS Simulator Implementation [339, 340, 351] |
| :--- | :--- | :--- |
| **Orbit & Altitude** | GEO (35,786 km), LEO (600 km - 1,500 km), MEO (10,000 km), HAPS (8 km - 50 km) | Unlimited Walker constellations (LEO/MEO) via Skyfield, GEO, HAPS, and UAVs. |
| **Carrier Frequency** | S-band (2 GHz DL/UL) and Ka-band (20 GHz DL / 30 GHz UL) | Explicit support for S-band (2.17-2.2 GHz DL, 1.98-2.01 GHz UL) and Ka-band (19.7-21.2 GHz DL, 29.5-30.0 GHz UL). |
| **Beam Pattern** | Earth-fixed or Earth-moving (Beam footprints: 5 km to 1000 km in diameter) | Dynamic 3D beam footprints and beam power tapering based on antenna aperture and elevation angle. |
| **Duplexing Mode** | FDD | Frequency Division Duplexing (FDD) is the default duplexing scheme. |
| **Channel Bandwidth** | Up to $2 \times 20\text{ MHz}$ (S-band), up to $2 \times 800\text{ MHz}$ (Ka-band) | Fully configurable channel bandwidths; supports wideband or narrow flat-fading SISO/MIMO links. |
| **Terminal Types** | Handheld Class 3 (23 dBm TX), VSAT (33 dBm TX), and moving platforms | Configurable Transmit Power ($P_{TX}$), Antenna Gain ($G_{TX}, G_{RX}$), and Noise Figure ($NF$). |

---

## 2. Slant Range Geometry & Coordinate Systems

To model propagation delays and dynamic path loss, both TR 38.811 and 3DANTS utilize 3D coordinate transformations to compute the distance and angles between moving satellites and ground terminals [81, 338].

### 3GPP Spherical Slant Range Model
TR 38.811 computes the line-of-sight distance (slant range $d$) over a simplified spherical Earth of radius $R_E = 6371\text{ km}$ as a function of the satellite elevation angle $\alpha$ and altitude $h_0$ [87, 88]:

$$d(\alpha) = \sqrt{R_E^2 \sin^2\alpha + h_0^2 + 2h_0R_E} - R_E \sin\alpha$$

### 3DANTS Ellipsoidal Coordinate Model
Rather than a perfect sphere, 3DANTS models the Earth using the **WGS-84 oblate spheroid model** to calculate satellite orbits, line-of-sight visibility, and exact distance vectors [338]. 

The absolute coordinates are tracked in the **Earth-Centered Earth-Fixed (ECEF) Global Coordinate System** (GCS) $\mathcal{G}$ with basis vectors $\{e_x^{\mathcal{G}}, e_y^{\mathcal{G}}, e_z^{\mathcal{G}}\}$ [338, 345]. At each Transmission Time Interval ($t_k$), 3DANTS computes a **local frame** $\mathcal{L}_i$ for a node at position $r_i$ using a rotation matrix $\Psi^{\mathcal{G} \to \mathcal{L}_i}$ [345]:

$$p^{\mathcal{L}_i}_j = \Psi^{\mathcal{G} \to \mathcal{L}_i} \left( p^{\mathcal{G}}_j(t_k) - r^{\mathcal{G}}_i(t_k) \right)$$

From this transformed position $p^{\mathcal{L}_i}_j = (x_j^{\mathcal{L}_i}, y_j^{\mathcal{L}_i}, z_j^{\mathcal{L}_i})$, the local spherical coordinates—distance ($d_{ij}$), local elevation angle ($\theta_{el}$), and local azimuth angle ($\phi_{az}$)—are computed exactly [345]:

$$d_{ij}(t_k) = \| p^{\mathcal{G}}_i(t_k) - p^{\mathcal{G}}_j(t_k) \|$$

$$\theta_{el}(t_k) = \arctan2\left(z_j^{\mathcal{L}_i}, \sqrt{(x_j^{\mathcal{L}_i})^2 + (y_j^{\mathcal{L}_i})^2}\right)$$

$$\phi_{az}(t_k) = \arctan2\left(y_j^{\mathcal{L}_i}, x_j^{\mathcal{L}_i}\right)$$

This local frame conversion is 3DANTS' core mathematical engine for calculating directional antenna gains ($G_{RX}(\theta_{el})$), array steering vectors ($a_i(\theta_{el}, \phi_{az})$), and elevation-dependent path loss [345, 346].

---

## 3. Propagation & Path Loss Modeling

Both 3GPP TR 38.811 and 3DANTS compile path loss as a combination of free space attenuation and cumulative atmospheric losses [48, 327]:

$$L_{\text{total}, ij\text{, dB}}(t) = FSPL_{\text{dB}}(t) + L_{\text{atmospheric, dB}}(t) + L_{\text{BEL, dB}}(t)$$

### A. Free Space Path Loss (FSPL)
The basic FSPL is modeled identically in both frameworks as [48, 327]:

$$FSPL_{\text{dB}}(t) = 32.45 + 20\log_{10}(f_c) + 20\log_{10}(d_{ij}(t))$$

Where $f_c$ is the carrier frequency in GHz and $d_{ij}(t)$ is the distance in meters.

### B. Atmospheric Attenuation ($L_{\text{atmospheric}}$)
3DANTS implements the physical propagation impairments from TR 38.811 and ITU-R recommendations [327, 355]:

$$L_{\text{atmospheric}}(t) = L_{\text{cloud}} + L_{\text{rain}} + L_{\text{gas}} + L_{\text{scintillation}}$$

*   **Gaseous Attenuation ($L_{\text{gas}}$):** Calculated based on ITU-R P.676 recommendations, accounting for dry air pressure and water-vapour density [91, 327].
*   **Rain & Cloud Attenuation ($L_{\text{rain}}, L_{\text{cloud}}$):** Handled statistically in both frameworks using the ITU-R P.618 (Rain) and P.840 (Cloud) CDFs [93, 103, 327, 355].
*   **Scintillation ($L_{\text{scintillation}}$):**
    *   *Ionospheric (S-band, $f_c < 3\text{ GHz}$):* Caused by F-region plasma irregularities, modeled using the Gigahertz Scintillation Model (GISM) [94, 97, 327]. It is characterized by the Amplitude Scintillation Index ($S_4$) and scales with frequency as $f_c^{-1.5}$ [94, 95].
    *   *Tropospheric (Ka-band, $f_c > 6\text{ GHz}$):* Caused by refractive index variations from temperature and water vapor [102, 327]. Attenuation values are drawn from ITU-R P.618 cumulative distributions, scaling up with frequency and down with elevation angle [102, 103].

---

## 4. Large-Scale Shadow Fading with Temporal Correlation

While standard 3GPP models rely on static spatial correlation distances for terrestrial cells, non-terrestrial links involve high-speed satellite overflights that require **temporal correlation** modeling due to the predictable trajectories of the satellites [328].

### 3DANTS Recursive Shadow Fading Generation
To model shadow fading along a node's flight trajectory, 3DANTS applies a zero-mean Gaussian distribution in dB with an elevation-dependent variance $\sigma^2_{SF}(\theta_{el}, f_c, \text{LoS/NLoS})$ derived from the tables in TR 38.811 [88, 328].

The temporal correlation is modeled recursively using an exponential decaying autocorrelation function [329]:

$$s_l = \phi^l s_0 + \sqrt{1 - \phi^2} \sum_{m=1}^l s_m \phi^{l-m}$$

Where:
*   $\phi := e^{-1/\tau_s}$ is the correlation coefficient [329].
*   $\tau_s > 0$ is the correlation time, representing the number of time steps (TTIs) required for a $1^\circ$ change in the elevation angle $\theta_{el}$ along the orbital trajectory [329].
*   $s_m \sim \mathcal{N}(0, \sigma^2_{SF}(\theta_{el}(t_m)))$ is an independent and identically distributed Gaussian sequence [329].

This approach guarantees that the generated sequence maintains distribution consistency while smoothly evolving according to the changing elevation angle of the satellite [328, 331].

---

## 5. Fast Small-Scale Fading Model

For narrowband S-band links, 3DANTS implements flat fast small-scale fading modeled as a **Shadowed Rician distribution** (Abdi model) [332].

### The Shadowed Rician Complex Envelope
The low-pass equivalent of the instantaneous complex channel gain is given by [332]:

$$h_{ssf}(t) = A(t) + z(t) e^{j\beta_0}$$

Where:
*   $A(t) = a(t)e^{j\alpha(t)}$ is the multipath scatter component, with $a(t) \sim \text{Rayleigh}(2b_0)$ and random phase $\alpha(t) \sim \mathcal{U}[0, 2\pi)$ [332].
*   $z(t)$ is the Line-of-Sight (LoS) amplitude term modeled by a Nakagami-$m$ distribution with average power $\Omega = \mathbb{E}[|z(t)|^2]$ [332, 333, 334].
*   $\beta_0$ is the deterministic phase of the LoS path [332].

The probability density function (PDF) of the gain envelope $\gamma(t) = |h_{ssf}(t)|$ is formulated as [333]:

$$f_{\Gamma}(\gamma) = \left( \frac{2b_0 m}{2b_0 m + \Omega} \right)^m \frac{\gamma}{b_0} e^{-\frac{\gamma^2}{2b_0}} {}_1F_1\left(m, 1, \frac{\Omega \gamma^2}{2b_0(2b_0 m + \Omega)}\right), \quad \gamma \ge 0$$

Where ${}_1F_1(\cdot)$ is the confluent hypergeometric function [333, 334].

### Dynamic Elevation-Dependent Channel Parameters
3DANTS links the fading statistics directly to the dynamic elevation angle $\theta_{el}(t)$ (in degrees) using the empirical cubic polynomials specified in the literature [334]:

$$b_0(\theta_{el}) = -4.7943 \times 10^{-8}\theta_{el}^3 + 5.5784 \times 10^{-6}\theta_{el}^2 - 2.1344 \times 10^{-4}\theta_{el} + 3.2710 \times 10^{-2}$$

$$m(\theta_{el}) = 6.3739 \times 10^{-5}\theta_{el}^3 + 5.8533 \times 10^{-4}\theta_{el}^2 - 1.5973 \times 10^{-1}\theta_{el} + 3.5156$$

$$\Omega(\theta_{el}) = 1.4428 \times 10^{-5}\theta_{el}^3 - 2.3798 \times 10^{-3}\theta_{el}^2 + 1.2702 \times 10^{-1}\theta_{el} - 1.4864$$

These polynomials capture the physical transition from heavy shadowing at low elevation angles (small $m$ and $\Omega$) to light shadowing at high elevation angles (large $m$ and $\Omega$) [333].

---

## 6. Doppler Shift Dynamics

Due to the extreme relative velocities of LEO satellites ($v_{sat} \approx 7.56\text{ km/s}$ at $600\text{ km}$), Doppler modeling is a critical component of 3DANTS [72, 336].

### LEO Scatter Doppler Model
The maximum Doppler shift of the diffuse scattering component around the terminal is calculated dynamically based on the satellite's altitude ($h_{sat}$) and local elevation angle ($\theta_{el}$) [116, 336]:

$$f_{\text{scatterDoppler}} = \frac{v_{sat}}{c} \cdot \frac{R_{\text{Earth}}}{R_{\text{Earth}} + h_{sat}} \cos\theta_{el} \cdot f_c$$

This Doppler shift reaches up to **48 kHz** at S-band (2 GHz) for a 600 km LEO satellite, causing rapid phase rotations that are modeled dynamically in 3DANTS' channel coefficient generation [336].

### Multi-Vector Phase Rotation
For multi-cluster fast fading, 3DANTS implements the general phase rotation due to the combined movement of the transmitter and receiver [243]:

$$\phi_{\text{Doppler}}(t) = \exp \left( j2\pi \int_{t_0}^t \frac{\hat{r}_{rx,n,m}^\top(t) \cdot v_{rx}(t)}{\lambda_0} dt \right) \cdot \exp \left( j2\pi \int_{t_0}^t \frac{\hat{r}_{tx,n,m}^\top(t) \cdot v_{sat}(t)}{\lambda_0} dt \right)$$

This guarantees that the phase shifts of individual rays evolve consistently with the flight trajectories of the nodes [243, 244].

---

## 7. MIMO & Faraday Rotation

For spaceborne links operating above the ionosphere, electromagnetic waves experience **Faraday Rotation**—a rotation of the signal polarization plane as it passes through the ionized medium in the Earth's magnetic field [245].

3DANTS integrates this effect by post-multiplying the generated polar channel coefficients of each path by the Faraday rotation matrix $F_r$ [245, 246]:

$$F_r = \begin{bmatrix} \cos\psi & \sin\psi \\ \sin\psi & \cos\psi \end{bmatrix}$$

The rotation angle $\psi$ (in degrees) is calculated based on the carrier frequency $f_c$ (in GHz) as [245, 248]:

$$\psi = \frac{108}{f_c^2}$$

This ensures that polarization mismatch and cross-polarization discrimination (XPR) are modeled with high standard compliance [245, 246].

---

## References

The following reference documents are used for numerical validation of the
3DANTS mapping specification:

1. 3GPP TR 38.811 v15.2.0 (2018) - NR support for non-terrestrial networks
2. 3GPP TR 38.821 v16.1.0 (2020) - Solutions for NR to support NTN
3. 3GPP TR 38.901 v18.0.0 (2024) - Channel model for 0.5-100 GHz
4. ITU-R P.676-13 (2023) - Attenuation due to atmospheric gases and water vapour
5. Al-Hourani et al. (2014) - Optimal LAP altitude for maximum coverage

See docs/3DANTS_Testing_and_Numerical_Validation.md for the full test suite
documentation and docs/PLAN_3GPP_NUMERICAL_TESTS.md for the test plan.
