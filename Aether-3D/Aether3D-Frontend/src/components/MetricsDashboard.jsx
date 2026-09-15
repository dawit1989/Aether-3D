import React, { useMemo } from 'react';
import {
  classifyEntity,
  EntityType,
  getEntitiesByType,
  extractEntityMetrics,
  entitySummary,
} from '@utils/czmlUtils.js';
import './MetricsDashboard.css';

/**
 * MetricsDashboard — display channel-quality metrics for the
 * selected entity and an overview of all loaded simulation data.
 *
 * @param {Object} props
 * @param {Object|null} props.selectedEntity - Currently picked entity.
 * @param {Array|null} props.czmlData - Loaded CZML array.
 * @param {string} props.czmlFileName - Name of the loaded file.
 */
export default function MetricsDashboard({ selectedEntity, czmlData, czmlFileName }) {
  const overview = useMemo(() => {
    if (!czmlData || !Array.isArray(czmlData)) return null;

    const satellites = getEntitiesByType(czmlData, EntityType.SATELLITE);
    const coverage = getEntitiesByType(czmlData, EntityType.COVERAGE);
    const groundStations = getEntitiesByType(czmlData, EntityType.GROUND_STATION);
    const haps = getEntitiesByType(czmlData, EntityType.HAPS);
    const baseStations = getEntitiesByType(czmlData, EntityType.BASE_STATION);

    // Gather all metrics for statistics.
    const allMetrics = [];
    for (const packet of czmlData) {
      if (!packet || !packet.id) continue;
      const metrics = extractEntityMetrics(packet);
      if (Object.keys(metrics).length > 0) {
        allMetrics.push({ id: packet.id, name: packet.name, metrics });
      }
    }

    return {
      satellites,
      coverage,
      groundStations,
      haps,
      baseStations,
      allMetrics,
    };
  }, [czmlData]);

  const selectedMetrics = useMemo(() => {
    if (!selectedEntity) return null;
    return selectedEntity.metrics;
  }, [selectedEntity]);

  const renderMetricRow = (label, value, unit = '') => {
    if (value === undefined || value === null || Number.isNaN(value)) {
      return null;
    }
    const num = typeof value === 'number';
    return (
      <div className="metric-row">
        <span className="metric-label">{label}</span>
        <span className="metric-value">
          {num ? value.toFixed(2) : value}
          {unit && ` ${unit}`}
        </span>
      </div>
    );
  };

  const renderSINRTrend = () => {
    if (!overview || !overview.allMetrics) return null;
    const sinrValues = overview.allMetrics
      .map((m) => m.metrics['SINR (dB)'])
      .filter((v) => typeof v === 'number');
    if (sinrValues.length === 0) return null;

    const min = Math.min(...sinrValues);
    const max = Math.max(...sinrValues);
    const mean = sinrValues.reduce((a, b) => a + b, 0) / sinrValues.length;

    return (
      <div className="metric-chart">
        <div className="chart-bar">
          <div
            className="bar-fill mean"
            style={{ height: `${((mean - min) / (max - min || 1)) * 100}%` }}
            title={`Mean: ${mean.toFixed(1)} dB`}
          />
          <div
            className="bar-fill min"
            style={{ height: `${((min - min) / (max - min || 1)) * 100}%` }}
            title={`Min: ${min.toFixed(1)} dB`}
          />
          <div
            className="bar-fill max"
            style={{ height: `${((max - min) / (max - min || 1)) * 100}%` }}
            title={`Max: ${max.toFixed(1)} dB`}
          />
        </div>
        <div className="chart-stats">
          <span>SINR: min {min.toFixed(1)} / mean {mean.toFixed(1)} / max {max.toFixed(1)} dB</span>
        </div>
      </div>
    );
  };

  const renderPRxTrend = () => {
    if (!overview || !overview.allMetrics) return null;
    const pwrValues = overview.allMetrics
      .map((m) => m.metrics['meanPRx'])
      .filter((v) => typeof v === 'number');
    if (pwrValues.length === 0) return null;

    const min = Math.min(...pwrValues);
    const max = Math.max(...pwrValues);
    const mean = pwrValues.reduce((a, b) => a + b, 0) / pwrValues.length;

    return (
      <div className="metric-chart">
        <div className="chart-bar">
          <div
            className="bar-fill mean"
            style={{
              height: `${(((mean - min) / (max - min || 1)) * 100) || 10}%`,
            }}
            title={`Mean: ${mean.toFixed(1)} dBW`}
          />
        </div>
        <div className="chart-stats">
          <span>P_Rx: min {min.toFixed(1)} / mean {mean.toFixed(1)} / max {max.toFixed(1)} dBW</span>
        </div>
      </div>
    );
  };

  return (
    <div className="metrics-dashboard">
      <div className="dashboard-header">
        <h3 className="section-title">
          {czmlFileName ? `Metrics: ${czmlFileName}` : 'Metrics Dashboard'}
        </h3>
        <div className="entity-type-summary">
          {overview && (
            <>
              <span className="type-badge">SAT: {overview.satellites.length}</span>
              <span className="type-badge">CVG: {overview.coverage.length}</span>
              <span className="type-badge">GS: {overview.groundStations.length}</span>
              <span className="type-badge">HAPS: {overview.haps.length}</span>
              <span className="type-badge">BS: {overview.baseStations.length}</span>
            </>
          )}
        </div>
      </div>

      <div className="dashboard-content">
        {/* Selected entity card */}
        <div className="entity-card">
          <h4 className="card-title">
            {selectedEntity ? selectedEntity.name || selectedEntity.id : 'No entity selected'}
          </h4>
          {selectedEntity && selectedEntity.type && (
            <span className={`entity-type-badge type-${selectedEntity.type}`}>
              {selectedEntity.type}
            </span>
          )}
          {selectedMetrics ? (
            <div className="metrics-list">
              {renderMetricRow('Mean P_Rx', selectedMetrics['meanPRx'], 'dBW')}
              {renderMetricRow('SNR', selectedMetrics['SNR (dB)'], 'dB')}
              {renderMetricRow('SINR', selectedMetrics['SINR (dB)'], 'dB')}
              {renderMetricRow('Distance', selectedMetrics['Distance (km)'], 'km')}
              {renderMetricRow('Latitude', selectedMetrics['lat'])}
              {renderMetricRow('Longitude', selectedMetrics['lon'])}
              {renderMetricRow('Elevation', selectedMetrics['Theta_el_sat_see_vsat'], 'deg')}
              {renderMetricRow('Azimuth', selectedMetrics['Theta_az_sat_see_vsat'], 'deg')}
              {renderMetricRow('theta_el_vsat', selectedMetrics['theta_el_vsat_see_sat'], 'deg')}
              {renderMetricRow('theta_az_vsat', selectedMetrics['theta_az_vsat_see_sat'], 'deg')}
            </div>
          ) : (
            <div className="no-selection">
              Click on a satellite, ground station, or coverage cell
              in the 3D view to inspect its metrics.
            </div>
          )}
        </div>

        {/* Overview charts */}
        {overview && overview.allMetrics.length > 0 && (
          <div className="charts-row">
            <div className="chart-card">
              <h4>SINR Distribution</h4>
              {renderSINRTrend()}
            </div>
            <div className="chart-card">
              <h4>Received Power</h4>
              {renderPRxTrend()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
