import React, { useMemo } from 'react';
import {
  Card,
  Badge,
  Text,
  Button,
} from '@fluentui/react-components';
import {
  ChevronDown24Regular,
  ChevronRight24Regular,
} from '@fluentui/react-icons';
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
      return { min, max, mean, binCounts: [values.length] };
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
    return <Text size={200} className="no-histogram">No numerical data for histogram</Text>;
  }

  const maxCount = Math.max(...stats.binCounts, 1);
  const svgWidth = 280;
  const svgHeight = 75;
  const barWidth = svgWidth / BINS - 2;

  return (
    <div className="histogram-container">
      <div className="histogram-header">
        <Text weight="semibold" size={200} className="histogram-title">{metricName} Distribution</Text>
        <Text size={100} className="histogram-stats">
          Mean: {stats.mean.toFixed(1)} | Min: {stats.min.toFixed(1)} | Max: {stats.max.toFixed(1)}
        </Text>
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
          <Button
            appearance="subtle"
            size="small"
            icon={collapsed ? <ChevronRight24Regular /> : <ChevronDown24Regular />}
          />
          <Text weight="semibold" size={300} className="dashboard-title">
            {selectedEntity ? `Inspection: ${selectedEntity.name || selectedEntity.id}` : 'System Metrics & Analytics'}
          </Text>
        </div>
        <div className="header-right">
          {summary && (
            <Badge appearance="tint" color="brand">
              {summary.total} Entities ({summary.satellites} Sats, {summary.groundStations} GS)
            </Badge>
          )}
        </div>
      </div>

      {!collapsed && (
        <div className="dashboard-content">
          <Card className="metrics-pane">
            <Text weight="semibold" size={200} className="pane-title">Selected Entity Metrics</Text>
            {selectedEntity ? (
              <div className="entity-details">
                <div className="detail-row">
                  <Text size={200} className="detail-key">ID / Name:</Text>
                  <Text weight="semibold" size={200} className="detail-val">{selectedEntity.name || selectedEntity.id}</Text>
                </div>
                <div className="detail-row">
                  <Text size={200} className="detail-key">Category:</Text>
                  <Badge appearance="tint" color="informative">{selectedEntity.type}</Badge>
                </div>
                {Object.entries(selectedEntity.metrics || {}).map(([k, v]) => (
                  <div key={k} className="detail-row">
                    <Text size={200} className="detail-key">{k}:</Text>
                    <Text weight="semibold" size={200} className="detail-val highlight">
                      {typeof v === 'number' ? v.toFixed(2) : String(v)}
                    </Text>
                  </div>
                ))}
              </div>
            ) : (
              <Text size={200} className="no-selection">
                Click any satellite, HAPS, or ground station on the 3D globe to inspect live channel metrics.
              </Text>
            )}
          </Card>

          <Card className="metrics-pane">
            <Text weight="semibold" size={200} className="pane-title">RF Channel Distribution</Text>
            <MetricHistogram values={sinrValues} metricName="SINR (dB)" />
          </Card>

          <Card className="metrics-pane">
            <Text weight="semibold" size={200} className="pane-title">Topology Breakdown</Text>
            {summary ? (
              <div className="breakdown-grid">
                <div className="breakdown-card">
                  <Text weight="bold" size={600} className="card-num">{summary.satellites}</Text>
                  <Text size={100} className="card-label">Satellites</Text>
                </div>
                <div className="breakdown-card">
                  <Text weight="bold" size={600} className="card-num">{summary.groundStations}</Text>
                  <Text size={100} className="card-label">Ground Stations</Text>
                </div>
                <div className="breakdown-card">
                  <Text weight="bold" size={600} className="card-num">{summary.haps}</Text>
                  <Text size={100} className="card-label">HAPS</Text>
                </div>
                <div className="breakdown-card">
                  <Text weight="bold" size={600} className="card-num">{summary.coverage}</Text>
                  <Text size={100} className="card-label">Coverage Cells</Text>
                </div>
              </div>
            ) : (
              <Text size={200} className="no-selection">No dataset loaded</Text>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
