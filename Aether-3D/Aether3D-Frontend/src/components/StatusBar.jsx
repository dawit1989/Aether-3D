import React from 'react';
import './StatusBar.css';

/**
 * StatusBar — top bar showing the app title, loaded file name,
 * and an API endpoint input.
 *
 * @param {Object} props
 * @param {string} props.fileName - Currently loaded CZML file name.
 * @param {string} props.apiEndpoint - Current API base URL.
 * @param {Function} props.onApiEndpointChange - (url) => void
 */
export default function StatusBar({ fileName, apiEndpoint, onApiEndpointChange }) {
  return (
    <div className="status-bar-container">
      <div className="app-title">
        <span className="logo">🛰️</span>
        <span className="app-name">Aether3D-Frontend</span>
        <span className="app-tagline">Aether-3D Satellite Simulator</span>
      </div>

      {fileName && (
        <div className="file-info">
          <span className="file-icon">📄</span>
          <span className="file-name">{fileName}</span>
        </div>
      )}

      <div className="api-input">
        <label className="api-label">API:</label>
        <input
          type="url"
          className="api-endpoint-input"
          value={apiEndpoint}
          onChange={(e) => onApiEndpointChange(e.target.value)}
          placeholder="http://localhost:8000"
          title="Aether-3D API base URL for fetching live simulation data"
        />
      </div>
    </div>
  );
}
