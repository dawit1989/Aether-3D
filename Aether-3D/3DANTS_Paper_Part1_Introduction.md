# 3DANTS: An Open Source System Level Simulator for Unified 3D Networks

## Part 1: Introduction and Architectural Vision

### Abstract
Unified 3D networks will emerge in 6G by integrating Non-Terrestrial Networks (NTNs) and Terrestrial Networks (TNs) in a unified way to bring seamless connectivity to different areas [1]. A unified 3D network is formed of three layers: space, air, and terrestrial nodes [1]. Each layer has its own unique dynamics and channel properties, resulting in a complex spatial-temporal evolution of each communication link [1]. 

This documentation provides an in-depth breakdown of **3DANTS**, an open-source, modular system-level simulator developed in Python [1, 5]. 3DANTS enables researchers to define custom 3D network topologies and evaluate physical link quality in terms of:
* Channel conditions [1]
* Beamforming performance [1]
* Signal-to-Interference-plus-Noise Ratio (SINR) [1]
* Achievable data rates over specific areas and time durations [1]

By incorporating accurate orbital positioning, temporally correlated channels, and dynamic traffic patterns, 3DANTS supports complex inter-layer and intra-layer interference scenarios [1].

---

### I. The Necessity of Unified 3D Networks in 6G

In the upcoming 6G era, conventional Terrestrial Networks (TNs) alone cannot fulfill the exponential demand for permanent, ubiquitous connectivity [2]. Physical and geographical barriers (such as oceans, deserts, and mountainous terrain) along with natural disasters frequently put terrestrial base stations in a state of failure or make their deployment economically non-viable [2]. 

Non-Terrestrial Networks (NTNs) offer a robust answer to these challenges by providing:
1. **Ubiquitous Coverage:** Bridging the digital divide in rural and remote regions [2].
2. **Resilience:** Acting as backup infrastructure to support terrestrial networks during outages or disaster-recovery scenarios [2].

A unified 3D network integrates both NTN and TN infrastructures over an area by creating a multi-layered node architecture where space, air, and ground nodes can act as base stations [2]. 

```
                          ▲  [Space Layer]
                          │  GEO, MEO, LEO Satellites
                          │
     Vertical Dimension   │  [Air Layer]
        of 6G Networks     │  HAPS, LAPs, UAVs, Drones
                          │
                          │  [Terrestrial Layer]
                          ▼  Traditional LTE / 5G NR
```

#### The Three Structural Layers:
* **Space Layer:** Consists of satellites operational in Geostationary Earth Orbits (GEO), Medium Earth Orbits (MEO), and Low Earth Orbits (LEO) [3]. LEO constellations are of particularly high interest and shape the backbone of modern NTNs [3].
* **Air Layer:** Comprises High Altitude Platforms (HAPs), including airships and High Altitude Platform Stations (HAPSs), and Low Altitude Platforms (LAPs) such as Unmanned Aerial Vehicles (UAVs) and drones [3].
* **Terrestrial Layer:** Contains traditional Long Term Evolution (LTE) and 5G New Radio (NR) networks [4].

---

### II. The Simulation Challenge

Unified 3D networks involve complex interactions across all three vertical layers [4]. Evaluating these networks requires an accurate understanding and mathematical modeling of:
* **Node Mobility:** Especially for fast-flying objects such as LEO satellites and HAPS [4].
* **Dynamic Channel Conditions:** Capturing atmospheric losses, shadowing, and multi-path fading [4].
* **Traffic Patterns:** Modeling how varying network loads affect instantaneous interference [4].

Historically, different network layers were studied in isolation [4]. However, in an integrated 3D architecture, the space, air, and terrestrial layers are no longer isolated [4]. Inter-layer interference can significantly degrade communication links [4]. 

3DANTS is specifically designed to address this gap [5]. It is a Python-based, open-source, modular system-level simulator that integrates all three layers under a single, unified physical-link evaluation framework [5]. Unlike other existing simulators (which often omit satellite integration or are closed-source), 3DANTS provides a comprehensive environment that models the specific mobility, orbital trajectories, and channel characteristics of each layer [5].
