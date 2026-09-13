# Aether-3D (formerly 3DANTS)

An open-source system-level simulator for unified 3D networks.

Aether-3D (formerly **3DANTS**) brings together the **space** segment (GEO and LEO satellites), the **air** segment (HAPS and UAVs), and the **terrestrial** network into a single unified 3D network framework. Unified 3D networks are expected to emerge in 6G by tightly integrating Non-Terrestrial Networks with Terrestrial Networks to provide seamless connectivity across diverse areas. Each layer — space, air, and terrestrial — has its own dynamics and channel properties, producing spatial-temporal evolution of every communication link.

This simulator lets you define a 3D network and evaluate link quality across coverage, channel, beamforming, SINR, and achievable data rate over a given area and time window. It is the open reference implementation used to reproduce the numerical results of [3GPP TR 38.811](https://www.3gpp.org/dynareport/38811.htm) and related direct-to-device / non-terrestrial-network studies.

## Features

- **Position & Mobility** — LEO Walker constellations, GEO satellites, HAPS, UAVs, terrestrial base stations, and PPP interference scenarios.
- **Communication Channel** — Air-to-ground fading, atmospheric loss, frequency-selective and shadowing channel models, plus RX-power and satellite-communication-parameter computation.
- **Traffic** — Configurable traffic models for the unified network layers.
- **Simulation Engine** — A layer-based orchestrator (configure -> compose -> run -> inspect) that drives the simulation over the desired time horizon and produces SINR / throughput / coverage / interference analysis.

## Getting Started

1. Install dependencies:
   - [Skyfield](https://rhodesmill.org/skyfield/)
   - [sgp4](https://pypi.org/project/sgp4/)
   - [pandas](https://pandas.pydata.org/)
2. Run an example (from the `Aether-3D` package directory):
   ```bash
   python3 examples/3D_network_with_traffic.py
   ```
3. Try the orchestrator demo:
   ```bash
   python3 examples/orchestrator_demo.py
   ```

## Project Layout

```
Aether-3D/        # Main project package and source
docs/             # Technical reports and test plans
```

See `Aether-3D/README.md` for the full in-package documentation.

## Testing

```bash
cd Aether-3D
python3 -m pytest tests/ -v
```

## Citation

If you use Aether-3D, please cite:

```bibtex
@misc{Aether3D,
  author = {Mohammad Amin Vakilifard and Carsten Bockelmann},
  title = {{Aether-3D: An Open Source System Level Simulator for Unified 3D Networks}},
  howpublished = {\url{https://github.com/ant-uni-bremen/Aether-3D}}
}
```