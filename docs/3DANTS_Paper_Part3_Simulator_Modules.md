# 3DANTS: An Open Source System Level Simulator for Unified 3D Networks

## Part 3: Simulator Functionality, Modules, and Engine Architecture

3DANTS is structured as a collection of three independent configuration modules—**Position and Mobility**, **Communication Channel**, and **Traffic**—which feed into a central **Simulator Engine** [19]. 

```
┌──────────────────────────────────────────────────────────┐
│                CONFIGURABLE INPUT MODULES                │
├───────────────────┬───────────────────┬──────────────────┤
│ Position/Mobility │  Comm Channel     │  Traffic Module  │
│  - Reference P_O  │  - Frequencies    │  - CBR Traffic   │
│  - LEO Walker     │  - Antenna Type   │  - Poisson       │
│  - HAPS/UAV/BS/UE │  - Noise Temp T_n │  - Bursty (On/Off)│
└─────────┬─────────┴─────────┬─────────┴─────────┬────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────┐
│                     SIMULATION ENGINE                    │
├──────────────────────────────────────────────────────────┤
│ Loops sequentially over time steps t_k = TTI:            │
│  1. Node Position & Local Frame Transformations          │
│  2. Channel Gain and Received Power Calculations         │
│  3. Dynamic Traffic and SINR Analysis                    │
└──────────────────────────────────────────────────────────┘
```

The simulator updates node coordinates and generates fading channels at every discrete **Transmission Time Interval (TTI)**, which must be equal to the packet retrieval time [19]. The TTI resolution is highly configurable, ranging from a maximum of $1\text{ s}$ down to a minimum of $1\ \mu\text{s}$ [19].

---

### I. Position and Mobility Module

This module constructs the physical layout and trajectories of nodes within the 3D network [19]. 

#### 1. Reference & Coordinates
A ground reference point $P_O$ at $(lat_0, lon_0)$ is selected on the surface of the **WGS-84 ellipsoid** [19]. Using an Earth-centered Global Coordinate System (GCS), designated as $\mathcal{G} = \{e_x^G, e_y^G, e_z^G\}$, any node $i$'s position is represented as a 3D coordinate $p_i^G \in \mathbb{R}^3$ [19, 20].

#### 2. Space Node Generation
LEO Walker constellations are modeled and propagated using the **Skyfield** library [20]. Users configure the constellation's geometry using four parameters [20]:
* $i$: Inclination angle between the orbital and equatorial planes [20].
* $t$: Total number of orbital planes [20].
* $p$: Number of satellites per plane [20].
* $f$: Phase separation (in-plane angular spacing) [20].

An Earth-fixed cell area $\mathcal{A}$ centers at $P_O$, with a beam diameter derived from 3GPP TR 38.821 (based on satellite altitude $h_{\text{sat}}$, frequency $f_c$, and antenna aperture size) [20].

#### 3. Air & Terrestrial Node Generation
* **Air Layer:** Users define the count of High Altitude Platform Stations ($N_{HAPS}$) and Low Altitude Platforms ($N_{UAV}$/drones) along with their respective operating altitudes [20].
* **Terrestrial Layer:** Traditional base stations ($N_{BS}$) are placed within the cell area $\mathcal{A}$ [20, 21]. To prevent overlapping coverage footprints, 3DANTS distributes the initial base station positions $p_i^G$ uniformly while enforcing a distance constraint [21]:
  $$\|p_i^G - p_j^G\| \ge 2r_{BS} \quad \forall \ i \neq j$$
* **User Equipment (UE):** Ground users are placed via a Homogeneous Poisson Point Process (HPPP) either in a 3D truncated cone (with height $h_{HAPS}$ and base $\mathcal{A}$) or distributed 2D within $\mathcal{A}$ [21]. UEs are assigned to $BS_j$ if they fall within its coverage radius [21]:
  $$\|p_{UE,i}^G - p_{BS,j}^G\| \le r_{BS}$$

---

### II. Communication Channel Module

This module configures the physical radio interfaces, bands, and antennas [21].

* **Frequency Bands:** Supports both the **S-band** (downlink: 2.17–2.20 GHz, uplink: 1.98–2.01 GHz) and the **Ka-band** (downlink: 19.7–21.2 GHz, uplink: 29.5–30.0 GHz) in accordance with 3GPP TR 38.821 [21].
* **Environments:** Incorporates channel characteristics tailored to Suburban, Urban, and Dense-urban scenarios [21].
* **Antenna Options:**
  1. *Omni-directional Antenna:* Users set static transmitter gain $G_{TX}$ and receiver gain $G_{RX}$ [22].
  2. *Very Small Aperture Terminal (VSAT):* Implements circular aperture reflector antennas [22].
  3. *Antenna Arrays:* Models multi-antenna structures. The position of each $m$-th antenna element relative to the node's center $p_i^G$ is defined by a coordinate vector $r_m = [dx_{A,m}, dy_{A,m}]^T$ [22]. This allows the simulator to calculate steering vectors for beamforming [22].
* **Noise:** The noise temperature $T_{noise}$ is defined to calculate the cumulative noise power $P_N$ [22].

---

### III. Traffic Module

To capture the true dynamic nature of network interference, the Traffic Module generates individual packet arrival patterns $\mathcal{T}_j$ for each transmitter $j$ using three different models [23]:

1. **Continuous Bit Rate (CBR):** Generates packets at a constant rate $v_j$ packets/second with a fixed size $\zeta_j$ bytes [23]. This yields deterministic inter-packet arrival times $\Delta t_j = 1/v_j$ seconds, following the sequence $t_n = n \cdot \Delta t_j$ [23].
2. **Poisson Traffic:** Packets are generated stochastically with inter-arrival times following an exponential distribution [23]:
   $$f_{T_j}(t) = \lambda_j e^{-\lambda_j t} \quad (t \ge 0)$$
   Packet sizes are selected from a normal distribution [24]:
   $$\zeta_j \sim \mathcal{N}(\mu_j, \sigma_j^2)$$
3. **Bursty Traffic:** Jumps between "On" and "Off" states to model bursty, high-intensity traffic [24]. During the "On" state of duration $T_{On,j}$, packets are generated at rate $r_{On,j}$ with size $\zeta_j$ [24]. During the "Off" state of duration $T_{Off,j}$, no packets are created [24].

---

### IV. Simulator Engine

The Simulation Engine coordinates the temporal evolution of the nodes across discrete steps $t_k$ [24]. For LEO satellites, the time steps span the visibility window over the reference point $P_O$ [25]:

$$t_k = t_{rise,q} + k \cdot \Delta t, \quad k \in \{0, 1, \dots, K_s\}$$

Where $\Delta t = TTI$ and $K_s = \lfloor(t_{set,s} - t_{rise,q})/\Delta t\rfloor$ [25]. For GEO satellites, which are continuously visible, the steps span from simulation start to end [25].

#### Sequential Engine Execution Steps:

##### 1. Position Update & Local Coordinate Transforms
At each step, LEO satellites are sorted by their rise times [25]. For mutually visible satellites, the engine employs the **highest-elevation logic** to select the active serving satellite $q^*$ [25, 26]:

$$q^* = \text{argmax}_q \theta_{G,el,q}$$

All nodes then update their global coordinates $p_i^G(t_k)$ according to their trajectory models [26]. 

A major contribution of 3DANTS is the dynamic calculation of **local coordinate frames** $L_i$ to establish relative orientations [26]. A local frame is defined by its origin $r_i \in \mathbb{R}^3$ and a rotation matrix $\Psi^{G \to L_i} \in \mathbb{R}^{3 \times 3}$ [26]. The position of a target node $j$ is transformed into $i$'s local frame via [26]:

$$p_j^{L_i} = \Psi^{G \to L_i}(p_j^G - r_i)$$

The transformed Cartesian coordinate $p_j^{L_i} = (x_j^{L_i}, y_j^{L_i}, z_j^{L_i})$ is converted to local spherical coordinates [26]:
* **Distance:** $d_{ij} = \|p_i^G - p_j^G\|$ [26]
* **Local Elevation Angle:** $\theta_{el,ij}^{L_i} = \arctan2\left(z_j^{L_i}, \sqrt{(x_j^{L_i})^2 + (y_j^{L_i})^2}\right)$ [26]
* **Local Azimuth Angle:** $\phi_{az,ij}^{L_i} = \arctan2(y_j^{L_i}, x_j^{L_i})$ [26]

##### 2. Channel Gain Calculation
Using the calculated local angles, the channel gains $H_{total,ij}$ are updated [27]. Antenna array steering vectors $a_i(\theta_{el,ij}^{L_i}, \phi_{az,ij}^{L_i})$ and VSAT gains $G_{RX,i}(\theta_{el,ij}^{L_i})$ are recalculated [27]. 

The total received power is computed as [27]:

$$P_{RX,ij}(t_k) = P_{TX,j} \frac{G_{TX,j} G_{RX,i}(t_k)}{10^{L_{total,ij}(t_k)/10}} |h_{ssf}(t_k)|^2 S(t_k)$$

This received power is used to compute the instant Signal-to-Noise Ratio (SNR) [28]:

$$SNR_{ij}(t_k) = \frac{P_{RX,ij}(t_k)}{N_i(t_k)}$$

##### 3. Dynamic Interference and SINR Calculation
For a receiver $i$ paired with active transmitter $j$, the simulator assesses the interference caused by other active transmitters $\nu \neq j$ [28]. The transmitter activity state $\delta_\nu(t_k) \in \{0, 1\}$ is determined by the Traffic Module [28, 29]. 

If the desired transmitter is active ($\delta_j(t_k) = 1$), the engine calculates the **Signal-to-Interference-plus-Noise Ratio (SINR)** [29]:

$$SINR_{ij}(t_k) = \frac{P_{RX,ij}(t_k)}{\sum_{\nu \in J \setminus \{j\}} \delta_\nu(t_k) P_{Int,i\nu}(t_k) + N_i(t_k)}$$

---

### V. Comparison to Other Simulation Frameworks

3DANTS fills a critical gap in the existing system-level simulation landscape. The table below compares 3DANTS against other widely known frameworks [34]:

| Feature / Simulator | 5G Vienna [34] | SNS-3 [34] | MATLAB® [34] | **3DANTS (Ours)** [34] |
| :--- | :--- | :--- | :--- | :--- |
| **Satellite Support** | No [34] | GEO Only [34] | GEO & LEO (Limited) [34] | **GEO & LEO (Unlimited)** [34] |
| **LEO Constellations**| No [34] | No [34] | Yes (Limited) [34] | **Yes (Unlimited Scale)** [34] |
| **Aerial Nodes** | UAVs [34] | Possible [34] | Possible [34] | **HAPS & UAVs** [34] |
| **Terrestrial Layer** | Yes [34] | Yes [34] | Yes [34] | **Yes (Standard Compliant)** [34] |
| **Channel Model** | 3GPP 38.901 [34] | 3GPP 38.811 [34] | 3GPP TR 38.811 [34] | **3GPP TR 38.811 (Full)** [34] |
| **Fading Models** | Large-scale only [34] | Large-scale + Weather [34] | Large-scale [34] | **Large-scale + Weather + Flat Small-scale** [34] |
| **Language & License**| Open Source (MATLAB req.) [34] | Open Source (C++) [34] | Commercial [34] | **Open Source (Python)** [34] |

---

## VI. Testing and Numerical Validation

The 3DANTS simulator includes a comprehensive numerical correctness test suite
that validates each 3GPP channel model against known reference values from
3GPP TR 38.811, TR 38.821, TR 38.901, ITU-R P.676, and the Al-Hourani LAP
altitude paper.

### Test Categories

- Numerical correctness (48 tests): Validates exact formula outputs from
  satellite parameters, FSPL, noise power, LOS probability, path loss,
  Rician K-factor, atmospheric attenuation, antenna gain, and 3GPP tables.
- Analysis sub-package (20 tests): Validates SINR, throughput, coverage,
  and CDF helpers.
- Orchestrator integration (20 tests): Validates the fluent layer-based
  simulation architecture, ComponentRegistry, and SimLayer hooks.

### Reference Documents

1. 3GPP TR 38.811 v15.2.0 (2018) - NR support for non-terrestrial networks
2. 3GPP TR 38.821 v16.1.0 (2020) - Solutions for NR to support NTN
3. 3GPP TR 38.901 v18.0.0 (2024) - Channel model for 0.5-100 GHz
4. ITU-R P.676-13 (2023) - Attenuation due to atmospheric gases and water vapour
5. Al-Hourani et al. (2014) - Optimal LAP altitude for maximum coverage

See docs/PLAN_3GPP_NUMERICAL_TESTS.md for the full test plan and
docs/REPORT_3GPP_NUMERICAL_TESTS.md for the detailed test report.
