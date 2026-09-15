import React from 'react';
import './ControlPanel.css';

export default function ControlPanel({
  showSatellites,
  onShowSatellitesChange,
  showCoverage,
  onShowCoverageChange,
  showGroundStations,
  onShowGroundStationsChange,
  showOrbits,
  onShowOrbitsChange,
  terrainMode,
  onTerrainModeChange,
  baseMap,
  onBaseMapChange,
}) {
  return (
    <div className="control-panel">
      <h3 className="section-title">Layer Visibility</h3>
      <div className="toggle-group">
        <label className="toggle-item">
          <input
            type="checkbox"
            checked={showSatellites}
            onChange={(e) => onShowSatellitesChange(e.target.checked)}
          />
          <span className="toggle-label">Satellites & HAPS</span>
        </label>

        <label className="toggle-item">
          <input
            type="checkbox"
            checked={showCoverage}
            onChange={(e) => onShowCoverageChange(e.target.checked)}
          />
          <span className="toggle-label">Coverage Cells</span>
        </label>

        <label className="toggle-item">
          <input
            type="checkbox"
            checked={showGroundStations}
            onChange={(e) => onShowGroundStationsChange(e.target.checked)}
          />
          <span className="toggle-label">Ground / Base Stations</span>
        </label>

        <label className="toggle-item">
          <input
            type="checkbox"
            checked={showOrbits}
            onChange={(e) => onShowOrbitsChange(e.target.checked)}
          />
          <span className="toggle-label">Orbital Paths</span>
        </label>
      </div>

      <h3 className="section-title margin-top">Environment</h3>
      <div className="select-group">
        <div className="select-item">
          <label htmlFor="base-map-select">Base Map:</label>
          <select
            id="base-map-select"
            value={baseMap}
            onChange={(e) => onBaseMapChange(e.target.value)}
          >
            <option value="osm">OpenStreetMap</option>
            <option value="cartodb">CartoDB Positron</option>
            <option value="arcgis">ArcGIS World Imagery</option>
            <option value="none">Bare Globe (None)</option>
          </select>
        </div>

        <div className="select-item">
          <label htmlFor="terrain-select">Terrain Model:</label>
          <select
            id="terrain-select"
            value={terrainMode}
            onChange={(e) => onTerrainModeChange(e.target.value)}
          >
            <option value="ellipsoid">WGS84 Ellipsoid (Flat)</option>
            <option value="srtm">Cesium World Terrain</option>
          </select>
        </div>
      </div>
    </div>
  );
}
