# Aether-3D (formerly 3DANTS)
An Open Source System Level Simulator for Unified 3D Networks

# PLEASE NOTE!
This repository is currently under development. More examples and features will be added soon.
For further questions, feel free to contact: vakilifard@ant.uni-bremen.de
# 3DANTS
An Open Source System Level Simulator for Unified 3D Networks: Bringing Space segments (GEO and LEO satellites) with Air segmenst (HAPS and UAVs) to terrestrila network. 
Unified 3D networks will emerge in 6G by integrating Non Terrestrial Networks and in current use Terrestrial Networks in a unified way to bring seamless connectivity to different areas. A unified 3D network is formed of three layers of space, air, and terrestrial nodes, each of which has its own dynamic and channel properties, resulting in spatial-temporal evolution of each communication link. This repository presents an open source system level simulator named 3DANTS which enables us to define the desired 3D network and evaluate each link quality in forms of channel, beamforming, SINR and achievable data rate over specific area and time.
# Installation
The 3DANTS is Python based system level simulator which allows you by using its building blocks to create a 3D networks and simulate the desired nodes, such as GEO satellite, LEO satellites in Walker constellation, High ALtitude Platform Stations (HAPSs), UAVs and terrestrial nodes and Base stations. It has three functional block of:
Position and Mobility
Communication Channel 
Traffic 
and the main engine which runs over the amount of simulation time. 
The nneded libraries to be installed first are: 
1- Skyfield at : https://rhodesmill.org/skyfield/
2- sgp4.api at: https://pypi.org/project/sgp4/
3- Pandas dataframe at: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html

# Testing

The simulator includes a comprehensive numerical correctness test suite that
validates each 3GPP communication-channel model against known reference values
from 3GPP TR 38.811, TR 38.821, TR 38.901, ITU-R P.676, and the Al-Hourani
LAP-altitude paper.

## Test Files

| Test File | Scope |
|---|---|
| tests/test_3gpp_numerical.py | Numerical correctness for 3GPP channel models (48 tests) |
| tests/test_analysis_extended.py | Unit tests for the analysis sub-package (20 tests) |
| tests/test_simulation.py | Integration tests for the orchestrator (20 tests) |
| tests/test_LEO_satellite_fading_channel_modes.py | Fading channel mode tests |
| tests/test_accuracy_fixes.py | Accuracy and correctness tests |
| tests/test_all_classes.py | Full class instantiation tests |

## Running Tests

```bash
cd 3DANTS
python3 -m pytest tests/ -v
```

See `docs/PLAN_3GPP_NUMERICAL_TESTS.md` for the full test plan and
`docs/REPORT_3GPP_NUMERICAL_TESTS.md` for the detailed test report.

# Examples

- examples/3D_network_with_traffic.py - Full network-with-traffic simulation using the layer-based orchestrator.
- examples/orchestrator_demo.py - Reference demo showing the configure->compose->run->inspect workflow, including reconfiguration and custom-layer examples.
- Aether3D-Frontend/ - React + CesiumJS web application for 3D visualization of simulation results. See `Aether3D-Frontend/README.md` for details.

# Web Visualization: Aether3D-Frontend

The `Aether3D-Frontend/` directory contains a React + Vite + CesiumJS web
application that renders 3D visualizations of satellite simulations. It
supports CZML file loading, entity picking with channel-quality metrics,
layer toggles, and optional REST API integration.

```bash
cd Aether3D-Frontend
npm install          # install dependencies
npm run dev          # start development server at http://localhost:5173
npm run build        # production build to dist/
```

The frontend loads CZML files produced by the simulator's `CZMLWriter`
(`3DANTS/analysis/czml_writer.py`) and displays satellites, ground stations,
coverage cells, HAPS, and base stations on an interactive 3D globe.



# Citation
If you use the content of thios repository, we ask you kindly to either cite the repository by
@misc{git_hublink_3DANTS,author = {MohammadAmin Vakilifard and Carsten Bockelmann},title = {{3DANTS}},howpublished = {Available at \url{https://github.com/ant-uni-bremen/3DANTS}}}
or the paper uploaded in our website as:
@article{vakilifarddeep,
  title={Deep Learning Based Link Quality Prediction for Direct-to-Device LEO Communication Under Inter-Constellation Interference},
  author={Vakilifard, Mohammad Amin and Gautam, Pramesh and Bockelmann, Carsten and Dekorsy, Armin}
}
