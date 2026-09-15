# Aether3D-Frontend — System & Functional Requirements Specification

## 1. Overview
`Aether3D-Frontend` is a web-based 3D visualization platform built with **React** and **CesiumJS** for the **Aether-3D (5G/6G Multi-Orbit System Level Satellite Simulator)**. It ingests CZML (Cesium Language) datasets emitted by the simulation engine and presents real-time 3D orbital dynamics, ground/aerial topology, coverage areas, and RF channel quality metrics.

---

## 2. Core Functional Requirements

### 2.1 3D Globe & Map Rendering
- **Globe Engine**: CesiumJS 3D Globe viewer with WebGL 2 rendering enabled.
- **Tokenless Open Imagery**: Default imagery provider must use **OpenStreetMap** (`https://tile.openstreetmap.org/`) initialized via `baseLayer` constructor options to operate without requiring a commercial Cesium Ion access token.
- **Base Map Provider Switching**: Support runtime base map swapping between:
  1. OpenStreetMap (`osm`)
  2. CartoDB Positron (`cartodb`)
  3. ArcGIS World Imagery (`arcgis`)
  4. Bare Ellipsoid / None (`none`)
- **Terrain Provider Switching**: Support terrain model swapping between:
  1. Ellipsoid / Flat (`ellipsoid`)
  2. SRTM / Cesium World Terrain (`srtm`)
- **WebGL Context Lifecycle**: Clean unmounting using `viewer.destroy()` to prevent memory leaks in single-page application re-renders.

### 2.2 Interactive Globe Inspection
- **Hover Tooltip Overlay**: `MOUSE_MOVE` handler tracking hovered entities, displaying floating tooltip with:
  - Entity Name / ID
  - Entity Category (Satellite, Ground Station, HAPS, Base Station, Coverage)
  - Key RF Channel Quality Metrics (SINR, SNR, Distance, Elevation Angle)
- **Entity Selection**: `LEFT_CLICK` handler picking target entities and propagating selection to the top-level app state to populate the metrics dashboard.

### 2.3 CZML Protocol & Entity Classification
- CZML parser must classify entities based on ID naming conventions from the `Aether-3D` simulator:
  - `Sat_<N>` / `satellite*` ➔ **Satellite**
  - `ground_station*` ➔ **Ground Station**
  - `coverage_sat_<N>` ➔ **Coverage Cell**
  - `haps_<N>` ➔ **HAPS (High Altitude Platform Station)**
  - `bs_<N>` ➔ **Base Station**
- **Layer Visibility Toggles**:
  - Satellites & HAPS (Show/Hide)
  - Coverage Cells (Show/Hide)
  - Ground Stations & Base Stations (Show/Hide)
  - Orbital Trajectories / Paths (Show/Hide)

### 2.4 File Ingestion & Sample Dataset
- **File Uploader**: Support local `.czml` and `.json` drag-and-drop or file selector loading.
- **Validation**: Validate that CZML payload is a valid array containing packet IDs before attempting globe injection.
- **One-Click Sample Data**: "Load Sample Data" button loading `/sample.czml` containing:
  - 2 LEO Satellites (`Sat_0`, `Sat_1`)
  - 1 GEO Satellite (`Sat_GEO`)
  - 1 Ground Station (`ground_station_0`)
  - 1 HAPS (`haps_0`)
  - 1 Base Station (`bs_0`)
  - 2 Coverage Cells (`coverage_sat_0`, `coverage_sat_1`)
  - RF Channel metrics (`SINR`, `SNR`, `Distance`, `meanPRx`, `Theta_el_sat_see_vsat`)

### 2.5 Metrics & Data Visualization Dashboard
- **Collapsible Drawer UI**: Bottom drawer panel with header click toggle (260px expanded, 36px collapsed) and SVG expand/collapse chevron indicator.
- **Histogram Component**: Pure SVG 10-bin frequency distribution histogram visualizing metric ranges across active entities.
- **Summary Metrics Table**: Display Mean, Min, Max values alongside category entity counts.

### 2.6 Status Bar & API Hook Integration
- **Status Bar**: Header bar displaying file name, active entity counts, connection status indicator, and backend API endpoint input (`http://localhost:8000`).
- **ApiProvider Context**: React context provider managing connection health check polling and simulation API execution requests.

---

## 3. Technical & Architecture Requirements

### 3.1 Technology Stack
- **Framework**: React 18.x (Functional Components + Hooks)
- **3D Globe Engine**: CesiumJS 1.145+
- **Build System**: Vite 8.x (Rolldown engine)
- **Asset Pipeline**: `vite-plugin-static-copy` copying Cesium `Workers/`, `Assets/`, `Widgets/`, `ThirdParty/` to dist
- **Code Quality**: ESLint 9.x (Flat Config), Prettier

### 3.2 Styling System
- Dark Theme CSS (`#0b0b14` background, `#141420` sidebar, `#0f0f18` header/dashboard)
- Custom Cesium widget dark overrides (`CesiumDarkTheme.css`)
- Responsive flexbox layout (handles viewport resizing and collapsing panels)
