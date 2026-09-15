import React, { useMemo } from 'react';
import { EntityType, getEntitiesByType, extractEntityMetrics } from '@utils/czmlUtils.js';
import './MetricsDashboard.css';

function MetricHistogram({ values, metricName }) {
  const BINS = 10;
  const stats = useMemo(() => {
    if (!values || values.length === 0) return null;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const mean = values.reduce((a, b) => a + b, 0) / values.length;

    if (min === max) {
      return { min, max, mean, binCounts: [values.length], binRanges: [`${min.toFixed(1)}`] };
    }

    const range = max - min;
    const binWidth = range / BINS;
    const binCounts = new Array(BINS).fill(0);

    values.forEach((v) => {
      let idx = Math.floor((v - min) / binWidth);
      if (idx >= BINS) idx = BINS - 1;
      binCounts[idx]++;
    });

    return { min, max, mean, binCounts };
  }, [values]);

  if (!stats) {
    return <div className="no-histogram">No numerical data for histogram</div>;
  }

  const maxCount = Math.max(...stats.binCounts, 1);
  const svgWidth = 280;
  const svgHeight = 75;
  const barWidth = svgWidth / BINS - 2;

  return (
    <div className="histogram-container">
      <div className="histogram-header">
        <span className="histogram-title">{metricName} Distribution</span>
        <span className="histogram-stats">
          Mean: {stats.mean.toFixed(1)} | Min: {stats.min.toFixed(1)} | Max: {stats.max.toFixed(1)}
        </span>
      </div>

      <svg width={svgWidth} height={svgHeight} className="histogram-svg">
        {stats.binCounts.map((count, i) => {
          const barHeight = (count / maxCount) * (svgHeight - 15);
          const x = i * (barWidth + 2);
          const y = svgHeight - barHeight - 12;
          return (
            <g key={i}>
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                className="histogram-bar"
              />
              <text x={x + barWidth / 2} y={y - 2} textAnchor="middle" className="bar-label">
                {count > 0 ? count : ''}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export default function MetricsDashboard({
  selectedEntity,
  czmlData,
  collapsed,
  onToggleCollapse,
}) {
  const summary = useMemo(() => {
    if (!czmlData) return null;
    return {
      satellites: getEntitiesByType(czmlData, EntityType.SATELLITE).length,
      groundStations: getEntitiesByType(czmlData, EntityType.GROUND_STATION).length,
      haps: getEntitiesByType(czmlData, EntityType.HAPS).length,
      baseStations: getEntitiesByType(czmlData, EntityType.BASE_STATION).length,
      coverage: getEntitiesByType(czmlData, EntityType.COVERAGE).length,
      total: czmlData.filter((p) => p && p.id).length,
    };
  }, [czmlData]);

  const sinrValues = useMemo(() => {
    if (!czmlData) return [];
    return czmlData
      .map((p) => extractEntityMetrics(p)['SINR (dB)'])
      .filter((v) => typeof v === 'number');
  }, [czmlData]);

  return (
    <div className={`metrics-dashboard ${collapsed ? 'collapsed' : ''}`}>
      <div className="dashboard-header" onClick={onToggleCollapse}>
        <div className="header-left">
          <span className={`chevron ${collapsed ? 'collapsed' : ''}`}>▼</span>
          <span className="dashboard-title">
            {selectedEntity ? `Inspection: ${selectedEntity.name || selectedEntity.id}` : 'System Metrics & Analytics'}
          </span>
        </div>
        <div className="header-right">
          {summary && (
            <span className="summary-pill">
              {summary.total} Entities ({summary.satellites} Sats, {summary.groundStations} GS, {summary.haps} HAPS)
            </span>
          )}
        </div>
      </div>

      {!collapsed && (
        <div className="dashboard-content">
          <div className="metrics-pane">
            <h4 className="pane-title">Selected Entity Metrics</h4>
            {selectedEntity ? (
              <div className="entity-details">
                <div className="detail-row">
                  <span className="detail-key">ID / Name:</span>
                  <span className="detail-val">{selectedEntity.name || selectedEntity.id}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-key">Category:</span>
                  <span className="detail-val category-tag">{selectedEntity.type}</span>
                </div>
                {Object.entries(selectedEntity.metrics || {}).map(([k, v]) => (
                  <div key={k} className="detail-row">
                    <span className="detail-key">{k}:</span>
                    <span className="detail-val highlight">
                      {typeof v === 'number' ? v.toFixed(2) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-selection">
                Click any satellite, HAPS, or ground station on the 3D globe to inspect live channel metrics.
              </div>
            )}
          </div>

          <div className="metrics-pane">
            <h4 className="pane-title">RF Channel Distribution</h4>
            <MetricHistogram values={sinrValues} metricName="SINR (dB)" />
          </div>

          <div className="metrics-pane">
            <h4 className="pane-title">Topology Breakdown</h4>
            {summary ? (
              <div className="breakdown-grid">
                <div className="breakdown-card">
                  <span className="card-num">{summary.satellites}</span>
                  <span className="card-label">Satellites</span>
                </div>
                <div className="breakdown-card">
                  <span className="card-num">{summary.groundStations}</span>
                  <span className="card-label">Ground Stations</span>
                </div>
                <div className="breakdown-card">
                  <span className="card-num">{summary.haps}</span>
                  <span className="card-label">HAPS</span>
                </div>
                <div className="breakdown-card">
                  <span className="card-num">{summary.coverage}</span>
                  <span className="card-label">Coverage Cells</span>
                </div>
              </div>
            ) : (
              <div className="no-selection">No dataset loaded</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
