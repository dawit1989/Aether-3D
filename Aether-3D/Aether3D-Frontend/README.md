# Aether3D-Frontend

React + Vite + CesiumJS web application for 3D visualization of satellite
simulation data produced by the [Aether-3D](https://github.com/aether-3d) satellite
simulator (formerly known as 3DANTS).

## Features

- **3D Globe Rendering** — Full CesiumJS viewer with OpenStreetMap imagery,
  terrain, timeline, and animation controls.
- **CZML File Loading** — Drag-and-drop or file-upload CZML files generated
  by the Aether-3D simulator's `CZMLWriter`.
- **Entity Visualization** — Satellites (`Sat_<N>`), ground stations,
  coverage cells (`coverage_sat_<N>`), HAPS, and base stations.
- **Channel-Quality Metrics** — SINR, SNR, received power, distance, and
  elevation coloring on entities. Click any entity to inspect its metrics.
- **Layer Toggles** — Independently show/hide satellites, coverage cells,
  ground stations, and orbit paths.
- **API Integration** — Optional REST API connection for fetching live
  simulation results from an Aether-3D backend.
- **Timeline Clock** — Cesium timeline synced from CZML clock packets for
  time-dynamic visualization.

## Prerequisites

- Node.js >= 20
- npm >= 10

## Installation

```bash
cd Aether3D-Frontend
npm install
```

## Development

```bash
npm run dev
```

Then open `http://localhost:5173` in your browser.

### Available Scripts

| Command         | Description                          |
| --------------- | ------------------------------------ |
| `npm run dev`   | Start the Vite development server     |
| `npm run build` | Production build (outputs to `dist/`) |
| `npm run preview` | Preview the production build       |
| `npm run lint`  | Run ESLint with auto-fix              |
| `npm run format`| Format code with Prettier             |
| `npm run host`  | Start dev server on all interfaces    |

## CZML Format

The Aether-3D simulator's `CZMLWriter` (`3DANTS/analysis/czml_writer.py`)
produces CZML documents with the following entity ID patterns:

| ID Pattern       | Entity Type    |
| ---------------- | -------------- |
| `Sat_<N>`        | Satellite       |
| `ground_station` | Ground station  |
| `coverage_sat_<N>` | Coverage cell |
| `haps_<N>`       | HAPS            |
| `bs_<N>`        | Base station    |

Each entity may carry a `properties` block with channel-quality metrics:

| Property Key       | Description                    |
| ------------------ | ------------------------------ |
| `meanPRx`          | Mean received power (dBW)      |
| `SNR (dB)`         | Signal-to-noise ratio (dB)     |
| `SINR (dB)`        | Signal-to-interference-plus-noise ratio (dB) |
| `Distance (km)`    | Distance from satellite to user (km) |
| `Theta_el_sat_see_vsat` | Elevation angle (degrees) |
| `Theta_az_sat_see_vsat` | Azimuth angle (degrees)    |

## API Endpoints

When an Aether-3D backend is running, the frontend can fetch live simulation
data. Configure the API endpoint in the status bar.

| Endpoint                  | Method | Description                |
| ------------------------- | ------ | -------------------------- |
| `/api/status`             | GET    | Server health check        |
| `/api/simulations`        | GET    | List recent simulation runs |
| `/api/czml/<id>`          | GET    | CZML data for a run        |
| `/api/metrics/<id>`       | GET    | Channel-quality metrics    |

## Project Structure

```
Aether3D-Frontend/
├── public/
│   └── assets/
│       └── icon.svg
├── src/
│   ├── components/
│   │   ├── CesiumGlobe.jsx        # 3D globe with CZML loading & entity picking
│   │   ├── ControlPanel.jsx        # Layer toggles & visualization options
│   │   ├── FileUploader.jsx        # Drag-drop CZML loader & API integration
│   │   ├── MetricsDashboard.jsx    # Selected-entity metrics & summary stats
│   │   └── StatusBar.jsx           # Top bar with file info & API endpoint
│   ├── hooks/
│   │   └── useApi.jsx              # API context provider & client hooks
│   ├── utils/
│   │   ├── czmlUtils.js            # CZML parsing, classification, metrics
│   │   └── vizUtils.js             # Color mapping & metric formatting
│   ├── App.jsx                     # Root component (layout & state)
│   ├── App.css                     # Global layout styles
│   ├── main.jsx                    # React entry point
│   └── index.css                   # Base styles
├── index.html
├── vite.config.js                  # Vite config with Cesium aliases
├── eslint.config.js
├── .prettierrc
├── .gitignore
└── package.json
```

## Tech Stack

- **React** 18.3.1 — UI framework
- **Vite** 5.4.0 — Build tool & dev server
- **Cesium** 1.125.0 — 3D globe & geospatial visualization
- **ESLint** 8.57.1 — Linter
- **Prettier** 3.3.3 — Code formatter

## License

See the main [Aether-3D repository](../README.md) for license information.
