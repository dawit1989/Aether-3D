import React from 'react';
import {
  Switch,
  Divider,
  Text,
  Select,
} from '@fluentui/react-components';
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
      <Text weight="semibold" size={300} className="section-title">
        Layer Visibility
      </Text>
      <div className="toggle-group">
        <Switch
          checked={showSatellites}
          onChange={(e, data) => onShowSatellitesChange(data.checked)}
          label="Satellites & HAPS"
        />
        <Switch
          checked={showCoverage}
          onChange={(e, data) => onShowCoverageChange(data.checked)}
          label="Coverage Cells"
        />
        <Switch
          checked={showGroundStations}
          onChange={(e, data) => onShowGroundStationsChange(data.checked)}
          label="Ground / Base Stations"
        />
        <Switch
          checked={showOrbits}
          onChange={(e, data) => onShowOrbitsChange(data.checked)}
          label="Orbital Paths"
        />
      </div>

      <Divider className="panel-divider" />

      <Text weight="semibold" size={300} className="section-title">
        Environment
      </Text>
      <div className="select-group">
        <div className="select-item">
          <label htmlFor="base-map-select">Base Map:</label>
          <Select
            id="base-map-select"
            value={baseMap}
            onChange={(e, data) => onBaseMapChange(data.value)}
          >
            <option value="osm">OpenStreetMap</option>
            <option value="cartodb">CartoDB Positron</option>
            <option value="arcgis">ArcGIS World Imagery</option>
            <option value="none">Bare Globe (None)</option>
          </Select>
        </div>

        <div className="select-item">
          <label htmlFor="terrain-select">Terrain Model:</label>
          <Select
            id="terrain-select"
            value={terrainMode}
            onChange={(e, data) => onTerrainModeChange(data.value)}
          >
            <option value="ellipsoid">WGS84 Ellipsoid (Flat)</option>
            <option value="srtm">Cesium World Terrain</option>
          </Select>
        </div>
      </div>
    </div>
  );
}
