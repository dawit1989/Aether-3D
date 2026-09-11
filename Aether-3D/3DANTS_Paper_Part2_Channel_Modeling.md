# 3DANTS: An Open Source System Level Simulator for Unified 3D Networks

## Part 2: Non-Terrestrial Nodes' Temporally Correlated Channel Generation

3DANTS simulates temporally and spatially correlated fading channels for Non-Terrestrial (NT) nodes along their flight trajectory [6]. The channel generation process is based on the simplified approach in 3GPP TR 38.811, with modifications to reflect overflight dynamics due to node mobility, while all parameters adhere to standardization [6].

The **elevation angle** $\theta_{el}(t)$—defined by the NT-node or User Equipment (UE) trajectory—is the key parameter linking mobility to channel behavior [6]. This is especially critical for LEO satellites, where $\theta_{el}$ varies significantly due to orbital features [6].

---

### I. Mathematical Formulation of the Channel

The overall channel between NT-node $j$ and UE $i$ is modeled as [7]:

$$H_{total,ij}(t) = 10^{-L_{total,ij}(t)/10} \times S(t) \times h_{ssf}(t)$$

Where:
* $L_{total,ij}(t)$ is the total path loss in dB [7].
* $S(t)$ represents the slow large-scale shadowing (log-normal distribution) [7].
* $h_{ssf}(t)$ represents the fast small-scale fading (Shadowed Rician or simple Rice model) [7].

Line-of-Sight (LoS) or Non-Line-of-Sight (NLoS) conditions are determined dynamically by the environment type (urban, dense urban, suburban) and the elevation angle $\theta_{el}$ [7].

---

### II. Path Loss and Atmospheric Attenuation

Signal propagation through the Earth's atmosphere is subject to a variety of losses beyond simple geometric spreading [7]. The total path loss is expressed as [8]:

$$L_{total,ij}^{\text{dB}}(t) = FSPL_{\text{dB}}(t) + L_{atmospheric,\text{dB}}(t)$$

#### 1. Free Space Path Loss (FSPL)
The geometric path loss is defined by [8]:

$$FSPL(f_c, d_{ij}(t)) = 32.45 + 20 \log_{10}(f_c) + 20 \log_{10}(d_{ij}(t))$$

Where:
* $f_c$ is the carrier frequency in **GHz** [8].
* $d_{ij}(t)$ is the instantaneous distance between UE $i$ and NT-node $j$ in **meters** [8].

#### 2. Atmospheric Attenuation
Cumulative atmospheric loss accounts for multiple atmospheric physical phenomena [8]:

$$L_{atmospheric}(t) = L_{cloud} + L_{rain} + L_{gas} + L_{scintillation}$$

Each term is computed based on ITU models (e.g., Recommendation ITU-R P.840) as a function of carrier frequency $f_c$ and elevation angle $\theta_{el}(t)$ [8]. This includes tropospheric scintillation (for $f_c > 6$ GHz) and ionospheric scintillation (for $f_c < 3$ GHz) [8].

---

### III. Slow Large-Scale Shadow Fading

Large-scale shadow fading follows a zero-mean Gaussian distribution (in dB) with environment-dependent variance $\sigma_{SF}^2(\theta_{el}, f_c, \text{LoS/NLoS})$ [9]. 

While Terrestrial Networks (TNs) exhibit spatial correlation, Non-Terrestrial Networks (NTNs) require **temporal correlation modeling** due to predictable NT-node trajectories (e.g., LEO satellites) [9]. This temporal correlation arises from gradual $\theta_{el}$ variations under static ground obstacles [9].

To maintain statistical distribution consistency, 3DANTS constrains the elevation angle increments between consecutive simulation samples [9]:

$$1^\circ < \Delta\theta_{el}(t, t+\Delta t_L) < 5^\circ \quad \text{(for LEO constellations)}$$

Where $\Delta t_L$ is derived from the satellite orbital trajectory and expressed in terms of the Transmission Time Interval (TTI) [10]. For quasi-stationary nodes (GEO, HAPS), $\Delta t_L$ is defined based on their specific mobility patterns [10].

#### The Temporal Autocorrelation Model
The temporally correlated shadowing sequence $\{s_l\}_{l=0}^{L-1}$ (where $L = \Delta t_L / TTI$) is generated from an i.i.d. Gaussian sequence $s_l \sim \mathcal{N}(0, \sigma_{SF}^2(\theta_{el}(t_l)))$ using a recursive model with an exponentially decaying autocorrelation function [10]:

$$\rho(l) = \phi^{|l|} = e^{-|l|/\tau_s}$$

Where:
* $\phi := e^{-1/\tau_s}$ [10]
* $\tau_s > 0$ denotes the correlation time, which is the number of time steps needed for a $1^\circ$ change in elevation angle $\theta_{el}$ [10, 11].

The closed-form recursive solution is written as [11]:

$$s_l = \phi^l s_0 + \sqrt{1 - \phi^2} \sum_{m=1}^{l} s_m \phi^{l-m}$$

The probability density function (PDF) of the resulting shadowing sequence is given by [11]:

$$p_s(s) = \frac{1}{\sqrt{(2\pi)^L \det(R_s)}} \exp\left(-\frac{1}{2} s^T R_s^{-1} s\right)$$

Where $R_s$ is the covariance matrix with elements defined as [12]:

$$[R_s]_{m,n} = \phi^{|m-n|} \cdot \sigma_{SF}^2(\theta_{el})$$

---

### IV. Fast Small-Scale Fading

For flat, fast small-scale fading, 3DANTS implements the **Shadowed Rician fading model**, which is applicable exclusively to the **S-band** [13].

The low-pass equivalent of the instantaneous complex channel gain is given by [13]:

$$h_{ssf}(t) = A(t) + z(t)e^{j\beta_0}$$

Where:
* $A(t) = a(t)e^{j\alpha(t)}$ models the time-varying multipath scatter component, with $a(t) \sim \text{Rayleigh}(2b_0)$ as the fading amplitude and $\alpha(t) \sim \mathcal{U}[0, 2\pi)$ as the random phase [13].
* $z(t)$ represents the slowly varying Line-of-Sight (LoS) term, whose envelope follows a Nakagami-$m$ distribution [13].
* $\beta_0$ is the deterministic phase of the LoS path [13].

#### Probability Density Function of Envelope
The PDF of the channel gain envelope $\gamma(t) = |h_{ssf}(t)|$ is formulated as [14]:

$$f_{\Gamma}(\gamma) = \left(\frac{2b_0 m}{2b_0 m + \Omega}\right)^m \frac{\gamma}{b_0} e^{-\frac{\gamma^2}{2b_0}} {}_1F_1\left(m, 1, \frac{\Omega\gamma^2}{2b_0(2b_0 m + \Omega)}\right) \quad (\gamma \ge 0)$$

Where:
* $2b_0 = \mathbb{E}[|A(t)|^2]$ is the average scatter power [14].
* $m > 0$ is the Nakagami-m parameter [14, 15].
* $\Omega = \mathbb{E}[|z(t)|^2]$ is the average LoS power [15].
* ${}_1F_1(\cdot)$ is the confluent hypergeometric function [15].

#### Empirical Elevation Angle Dependence
The channel parameters $b_0$, $m$, and $\Omega$ are empirically modeled as cubic functions of the elevation angle $\theta_{el}$ (in degrees) [15]:

$$b_0(\theta_{el}) = -4.7943 \times 10^{-8} \theta_{el}^3 + 5.5784 \times 10^{-6} \theta_{el}^2 - 2.1344 \times 10^{-4} \theta_{el} + 3.2710 \times 10^{-2}$$

$$m(\theta_{el}) = 6.3739 \times 10^{-5} \theta_{el}^3 + 5.8533 \times 10^{-4} \theta_{el}^2 - 1.5973 \times 10^{-1} \theta_{el} + 3.5156$$

$$\Omega(\theta_{el}) = 1.4428 \times 10^{-5} \theta_{el}^3 - 2.3798 \times 10^{-3} \theta_{el}^2 + 1.2702 \times 10^{-1} \theta_{el} - 1.4864$$

These parameters dynamically integrate with the trajectory of the NT-node [15].

#### Temporal Correlation & Doppler Shift
To generate temporally correlated samples of $\gamma(t)$, 3DANTS generates a Rayleigh time series for $A(t)$ with a maximum Doppler shift of $f_{\text{scatter,Doppler}}(t)$, and a second Rayleigh time series representing the slower fading of the LoS ray with $f_{\text{LoS,Doppler}} \ll f_{\text{scatter,Doppler}}$ [16].

For isotropic scattering, the autocorrelation function is [17]:

$$R_{\gamma}(\tau) = J_0(2\pi f_{\text{scatter,Doppler}} \tau)$$

Where $J_0(\cdot)$ is the zero-order Bessel function of the first kind [17]. For LEO satellites, the maximum scatter Doppler shift is mathematically calculated as [17]:

$$f_{\text{scatter,Doppler}} = \frac{v_{\text{sat}}}{c} \cdot \frac{R_{\text{Earth}}}{R_{\text{Earth}} + h_{\text{sat}}} \cos\theta_{el} \cdot f_c$$

For instance, at $S$-band with $\theta_{el} = 20^\circ$, $v_{\text{sat}} = 7.3 \text{ km/s}$, and $h_{\text{sat}} = 600 \text{ km}$, the Doppler shift reaches a significant **48 kHz** [17].

Correlated fading sequences $\{h_u\}_{u=0}^{U-1}$ are generated over $U$ consecutive TTIs where the change in elevation angle remains negligible ($\Delta\theta_{el} < 1^\circ$) [17]. For HAPS and GEO platforms, where trajectories are more stable, $U$ can be predetermined [17].
