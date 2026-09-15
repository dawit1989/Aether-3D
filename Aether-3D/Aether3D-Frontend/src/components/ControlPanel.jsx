import React from 'react';
import './ControlPanel.css';

/**
 * ControlPanel — layer visibility toggles and visualization options.
 *
 * @param {Object} props
 * @param {boolean} props.showSatellites
 * @param {Function} props.onShowSatellitesChange
 * @param {boolean} props.showCoverage
 * @param {Function} props.onShowCoverageChange
 * @param {boolean} props.showGroundStations
 * @param {Function} props.onShowGroundStationsChange
 * @param {boolean} props.showOrbits
 * @param {Function} props.onShowOrbitsChange
 */
export default function ControlPanel({
  showSatellites,
  onShowSatellitesChange,
  showCoverage,
  onShowCoverageChange,
  showGroundStations,
  onShowGroundStationsChange,
  showOrbits,
  onShowOrbitsChange,
}) {
  return (
    <div className="control-panel">
      <h3 className="section-title">Layers</h3>

      <div className="toggle-group">
        <ToggleRow
          label="Satellites"
          description="LEO / GEO satellite models and positions"
          checked={showSatellites}
          onChange={onShowSatellitesChange}
          icon="🛰️"
        />
        <ToggleRow
          label="Coverage Cells"
          description="Hexagonal / circular coverage footprints"
          checked={showCoverage}
          onChange={onShowCoverageChange}
          icon="🔵"
        />
        <ToggleRow
          label="Ground Stations"
          description="Terrestrial network base stations"
          checked={showGroundStations}
          onChange={onShowGroundStationsChange}
          icon="📡"
        />
        <ToggleRow
          label="Orbit Paths"
          description="Historical trajectory lines"
          checked={showOrbits}
          onChange={onShowOrbitsChange}
          icon="🌀"
        />
      </div>

      <h3 className="section-title">Visualization</h3>
      <div className="viz-options">
        <div className="viz-option">
          <label className="viz-label">Terrain</label>
          <select className="viz-select" defaultValue="srtm">
            <option value="srtm">SRTM 3D</option>
            <option value="ellipsoid">Ellipsoid</option>
            <option value="none">None</option>
          </select>
        </div>
        <div className="viz-option">
          <label className="viz-label">Base Map</label>
          <select className="viz-select" defaultValue="osm">
            <option value="osm">OpenStreetMap</option>
            <option value="bing">Bing Aerial</option>
            <option value="none">None</option>
          </select>
        </div>
      </div>
    </div>
  );
}

/**
 * Reusable toggle row with label, description, and checkbox.
 */
function ToggleRow({ label, description, checked, onChange, icon }) {
  return (
    <div className="toggle-row">
      <div className="toggle-label">
        <span className="toggle-icon">{icon}</span>
        <div className="toggle-text">
          <span className="toggle-name">{label}</span>
          <span className="toggle-desc">{description}</span>
        </div>
      </div>
      <label className="switch">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span className="slider" />
      </label>
    </div>
  );
}
