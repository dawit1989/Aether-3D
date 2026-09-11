# 3DANTS: An Open Source System Level Simulator for Unified 3D Networks

## Part 4: Case Studies, Simulation Results, and Conclusions

To validate the high-fidelity capabilities of 3DANTS, the authors provided three diverse, comprehensive simulation scenarios focusing on constellation visibility, spatial signal distribution, and multi-layer interference analysis [30].

---

### I. Scenario 1: LEO Walker Constellation Visibility

The visibility duration of a massive LEO satellite constellation over a specific ground target is analyzed [30].

#### 1. Simulation Parameters
* **LEO Walker Constellation ($W$):** Defined by inclination $i = 60^\circ$, total satellites $N_{\text{sat}} = 120$, orbital planes $N_{\text{planes}} = 10$, phase separation $f = 1$, and altitude $h_{\text{sat}} = 600\text{ km}$ [30].
* **Ground Reference Point ($P_O$):** Located at the coordinates of the University of Bremen: $\text{Latitude} = 53.11^\circ\text{ N}$, $\text{Longitude} = 8.85^\circ\text{ E}$ [30].

#### 2. Key Findings
* 3DANTS utilizes the Skyfield library and SGP4 propagation to calculate the precise overflight windows of all 120 satellites [19, 20].
* The simulation tracks the rising and setting times for each node as they pass over $P_O$ [19].
* The resulting visibility duration plot (equivalent to the paper's Fig. 6) reveals distinct periodic patterns in overflight windows, allowing researchers to evaluate handover and connectivity continuity profiles [30, 31].

---

### II. Scenario 2: Spatial Distribution of SINR in S-Band

This case study maps the spatially averaged SINR over a regional area served by a LEO satellite and a Geostationary (GEO) satellite sharing S-band frequencies [31, 32].

#### 1. Simulation Parameters
* **Cell Geometry:** A LEO cell centered at $P_O$ with radius $r_{\text{CellLEO}} = 50\text{ km}$, and a co-located, overlapping GEO cell with radius $r_{\text{CellGEO}} = 250\text{ km}$ [31, 32].
* **Spatial Resolution:** The target evaluation area $\mathcal{A}$ is discretized into 1,000 spatial coordinate points [31, 32].
* **Fading Constraints:** Only satellites passing within a low-elevation window ($20^\circ < \theta_{el} < 40^\circ$) are considered, as propagation through long atmospheric slant paths results in severe fading losses [32].
* **Traffic Pattern:** Both satellite layers utilize bursty traffic patterns with active "On" durations $T_{On} = 1\text{ s}$, packet generation rate $r_{On} = 20\text{ packets/s}$, inactive "Off" durations $T_{Off} = 2\text{ s}$, and fixed packet sizes $\zeta = 1000\text{ bytes}$ [32].
* **Beam Power Tapering:** Realistically models antenna beam profiles using exponential power attenuation [32, 33]:
  $$P_{RX}(p) = P_{RX}^{P_O} \exp\left(-\beta \|p - P_O\|^2\right)$$
  Where the spatial decay parameter $\beta$ is computed using the $3\text{-dB}$ beam boundaries [33]:
  $$\beta = \frac{2\ln 2}{r_b^2} \quad \text{with} \quad \begin{cases} r_b^{\text{LEO}} = 50\text{ km} \\ r_b^{\text{GEO}} = 250\text{ km} \end{cases}$$

#### 2. Key Findings
* The resulting spatial map demonstrates concentric degradation of SINR as user devices move away from the boresight center $P_O$, combined with temporal drops when bursty traffic from the overlapping GEO beam is active [32, 33].

---

### III. Scenario 3: Multi-Layer Interference & Outage Analysis

This scenario evaluates the cumulative impact of inter-layer interference on a moving user terminal served by the LEO constellation $W$ [33].

#### 1. Simulation Parameters
* **The Victim Receiver:** A ground UE equipped with an Omni-directional antenna, moving randomly within area $\mathcal{A}$ at a velocity of $5\text{ km/h}$ [33].
* **The Desired Link:** Served by the LEO Walker constellation $W$ in the S-band under a Continuous Bit Rate (CBR) traffic pattern ($\zeta = 1000\text{ bytes}$, $v = 10\text{ packets/s}$) [33].
* **Active Interfering Nodes:**
  * **Air Layer (HAPS):** Operates at altitude $h_{\text{HAPS}} = 10\text{ km}$, following a circular trajectory of radius $r_{\text{HAPS}} = 6\text{ km}$ at a speed of $v_{\text{HAPS}} = 25\text{ km/h}$ [33]. It transmits using a Poisson traffic pattern with average arrival rate $\lambda_{\text{HAPS}} = 10$ packets/s [33, 35].
  * **Terrestrial Layer (Base Stations):** Three ground base stations (BS1, BS2, BS3) with cell radii $r_{\text{BS}} = 20\text{ km}$ are stochastically distributed across area $\mathcal{A}$ via a Binomial point process [33]. They transmit Poisson traffic with arrival rates $\lambda_{\text{BS1}} = 10$, $\lambda_{\text{BS2}} = 8$, and $\lambda_{\text{BS3}} = 5$ packets/s [35].
  * **Interfering Packet Sizes:** Modulated via a Gaussian distribution: $\zeta_{\nu} \sim \mathcal{N}(1000, 200)$ bytes [35].
* **Simulation Resolution:** Executed for $100,000$ consecutive TTIs, where each TTI represents $1\text{ ms}$ of network time [35].

#### 2. Quantitative Outage Analysis (ECDF)
The Empirical Cumulative Density Function (ECDF) of the received SINR is computed to isolate the source of outages [35, 38]:

```
    ECDF
    1.0 ┼────────────────────────────────────/───
        │                                   /
    0.8 ┼───────────────/                  / 
        │              /  HAPS            /  BS3 
    0.6 ┼─────────────/  Outage          /  Outage
        │            /                  /
    0.4 ┼───────────/                  /  No Interf.
        │          /                  /  (SNR Curve)
    0.2 ┼─────────/                  /  ┌─────────┐
        │        /                  /   │  /      │
    0.0 ┼───────/──────────────────/────┴─────────┴─
       ─┼───────┬────────┬────────┬────────┬────────
       -60     -40      -20       0       20    SINR [dB]
```

##### Critical Observations:
1. **The HAPS Bottleneck:** The HAPS node causes the most devastating outages to the LEO-serving UE, shifting the SINR ECDF curves significantly to the left [35, 38]. This is mathematically driven by the lower altitude of the HAPS platform relative to the satellites, which results in immensely higher received interference power [35, 36]:
   $$P_{RX,\text{HAPS}} \gg P_{RX,W}$$
2. **Terrestrial base station Interference:** Terrestrial base stations also cause significant, localized outages [35, 36]. Specifically, **BS3** is shown to cause a more severe outage profile than BS1 or BS2, despite having a lower average packet arrival rate ($\lambda = 5$) [35, 36]. This is because the random walk trajectory of the UE happens to cross and spend more duration inside BS3's coverage footprint [36].
3. **The Interference Paradigm:** These results underscore that vertical layers cannot be modeled independently [4]. Dynamic, cross-layer interference prediction and cancellation are non-negotiable requirements for unified 3D architectures [36].

---

### IV. Conclusions

The paper presents **3DANTS** as a robust, open-source system-level simulator written in Python to meet the demanding requirements of unified 3D networks in the 6G era [1, 36].

The primary technical contributions of 3DANTS include [36]:
1. **Trajector-Dependent Channels:** Implementing temporally and spatially correlated channel fading models that evolve along the actual flight trajectories of space and air platforms [36].
2. **Multi-Layer Mobility Modeling:** Accurately calculating complex vertical orbital mechanics and relative 3D coordinate frames under standard WGS-84 coordinates [19, 36].

#### Future Work
Future versions of 3DANTS will expand upon current capabilities to address:
* Active handover management protocols between vertical layers [Previous Conversation].
* Advanced multi-beam coordination and massive MIMO beamforming models [Previous Conversation, 144].
* Enhanced interference cancellation algorithms to resolve inter-layer bottlenecks [36].

---

### V. References

1. G. Geraci, D. López-Pérez, M. Benzaghta, and S. Chatzinotas, "Integrating terrestrial and non-terrestrial networks: 3D opportunities and challenges," *IEEE Communications Magazine*, 2022 [37].
2. M. Vakilifard and C. Bockelmann, "3DANTS," Repository available at: [https://github.com/ant-uni-bremen/3DANTS](https://github.com/ant-uni-bremen/3DANTS) [37].
3. 3GPP, "Study on New Radio (NR) to support non-terrestrial networks (Release 15)," *Tech. Rep. TR 38.811 v15.2.0*, 2018 [37].
4. ITU, "Attenuation due to clouds and fog," *Recommendation ITU-R P.840-3*, 2013 [38].
5. 3GPP, "Study on channel model for frequencies from 0.5 to 100 GHz," *Tech. Rep. TR 38.901 v18.0.0*, 2024 [38].
6. M. Deserno, "How to generate exponentially correlated gaussian random numbers," *Department of Chemistry and Biochemistry UCLA*, 2002 [39].
7. A. Abdi, W. C. Lau, M.-S. Alouini, and M. Kaveh, "A new simple model for land mobile satellite channels: First- and second-order statistics," *IEEE Transactions on Wireless Communications*, vol. 2, no. 3, 2003 [39].
8. P. Ivaniš, V. Blagojević, and G. T. Đorđević, "The method of generating shadowed ricean fading with desired statistical properties," *IEEE INFOTEH-JAHORINA*, 2023 [39].
9. C. Xiao, Y. R. Zheng, and N. C. Beaulieu, "Novel sum-of-sinusoids simulation models for rayleigh and rician fading channels," *IEEE Transactions on Wireless Communications*, vol. 5, no. 12, 2006 [40].
10. J. Brent, "Skyfield: A python library for astronomy," GitHub Repository, 2021 [40].
11. 3GPP, "Solutions for NR to support non-terrestrial networks (NTN) (Release 16)," *Tech. Rep. TR 38.821 v16.1.0*, 2020 [40].
12. M. Röper, B. Matthiesen, D. Wübben, P. Popovski, and A. Dekorsy, "Beamspace MIMO for satellite swarms," *IEEE WCNC*, 2022 [40].
13. Magister Solutions Ltd., "Satellite network simulator 3 (sns3)," [http://www.sns3.org/](http://www.sns3.org/), 2020 [41].
14. MathWorks, "wirelessnetworksimulator: Communications toolbox wireless network simulation library," MATLAB Documentation, 2025 [41].
15. Technische Universität Wien, "Vienna 5g system level simulator," [http://www.tc.tuwien.ac.at/vccs/](http://www.tc.tuwien.ac.at/vccs/), 2018 [41].
