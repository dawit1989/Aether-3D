import React from 'react';
import { useApi, ApiStatus } from '@hooks/useApi.jsx';
import './StatusBar.css';

export default function StatusBar({ fileName, apiEndpoint, onApiEndpointChange }) {
  const { status } = useApi();

  return (
    <header className="status-bar">
      <div className="status-left">
        <span className="app-title">Aether-3D Viz</span>
        <span className="status-divider">|</span>
        <span className="file-info">
          {fileName ? `File: ${fileName}` : 'No dataset loaded'}
        </span>
      </div>

      <div className="status-right">
        <div className="api-config">
          <label htmlFor="api-url">Backend API:</label>
          <input
            id="api-url"
            type="text"
            value={apiEndpoint}
            onChange={(e) => onApiEndpointChange?.(e.target.value)}
            placeholder="http://localhost:8000"
          />
          <span className={`status-badge ${status}`}>
            {status === ApiStatus.CONNECTED && '● Online'}
            {status === ApiStatus.DISCONNECTED && '○ Offline'}
            {status === ApiStatus.CHECKING && '◌ Checking'}
          </span>
        </div>
      </div>
    </header>
  );
}
