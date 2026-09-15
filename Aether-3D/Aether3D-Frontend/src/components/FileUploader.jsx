import React, { useState, useCallback } from 'react';
import { validateCzml, EntityType, classifyEntity, getEntitiesByType } from '@utils/czmlUtils.js';
import { useApi, ApiStatus } from '@hooks/useApi.jsx';
import './FileUploader.css';

/**
 * FileUploader — load CZML files or fetch them from the Aether-3D API.
 *
 * Features:
 *   - Drag-and-drop or click-to-browse for .czml files.
 *   - Validates CZML before passing to the globe.
 *   - Optionally lists simulations from the connected API.
 *
 * @param {Object} props
 * @param {Function} props.onCzmlLoad - (data, fileName) => void
 */
export default function FileUploader({ onCzmlLoad }) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const { apiStatus, simulations, checkConnection, fetchSimulation } = useApi();

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        readCzmlFile(file);
      }
    },
    []
  );

  const handleFileChange = useCallback(
    (e) => {
      const file = e.target.files[0];
      if (file) {
        readCzmlFile(file);
      }
      // Reset input so the same file can be re-selected.
      e.target.value = '';
    },
    []
  );

  const readCzmlFile = useCallback(
    (file) => {
      setError(null);
      setSuccess(null);

      if (!file.name.toLowerCase().endsWith('.czml') && file.type !== 'application/json') {
        setError('File type not recognised. Expected a .czml file.');
        return;
      }

      if (file.size > 50 * 1024 * 1024) {
        setError('File is too large (max 50 MB).');
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target.result;
          const data = JSON.parse(text);
          const validation = validateCzml(data);

          if (!validation.valid) {
            setError(`Invalid CZML: ${validation.error}`);
            return;
          }

          onCzmlLoad(data, file.name);
          setSuccess(
            `Loaded ${file.name} — ${validation.entityCount} entities`
          );

          // Show a breakdown of entity types.
          const breakdown = {
            satellites: getEntitiesByType(data, EntityType.SATELLITE).length,
            coverage: getEntitiesByType(data, EntityType.COVERAGE).length,
            groundStations: getEntitiesByType(data, EntityType.GROUND_STATION).length,
            haps: getEntitiesByType(data, EntityType.HAPS).length,
            baseStations: getEntitiesByType(data, EntityType.BASE_STATION).length,
          };

          setTimeout(() => {
            setSuccess(
              `${file.name} — ${validation.entityCount} entities ` +
                `(satellites: ${breakdown.satellites}, ` +
                `coverage: ${breakdown.coverage}, ` +
                `ground stations: ${breakdown.groundStations})`
            );
          }, 100);
        } catch (err) {
          setError(`Could not parse CZML: ${err.message}`);
        }
      };
      reader.readAsText(file);
    },
    [onCzmlLoad]
  );

  const handleApiSimulationSelect = useCallback(
    async (simulationId) => {
      try {
        setError(null);
        setSuccess(null);
        const data = await fetchSimulation(simulationId, 'czml');
        onCzmlLoad(data, `API: ${simulationId}`);
        setSuccess(`Loaded simulation ${simulationId} from API`);
      } catch (err) {
        setError(`API error: ${err.message}`);
      }
    },
    [fetchSimulation, onCzmlLoad]
  );

  const handleConnect = useCallback(() => {
    checkConnection();
  }, [checkConnection]);

  return (
    <div className="file-uploader">
      <h3 className="section-title">Data Source</h3>

      {/* Drag & drop area */}
      <div
        className={`drop-area ${isDragging ? 'dragging' : ''} ${error ? 'error' : ''} ${success ? 'success' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById('czml-file-input')?.click()}
      >
        <div className="drop-icon">{isDragging ? '📂' : '📁'}</div>
        <div className="drop-text">
          {isDragging
            ? 'Drop to load CZML...'
            : 'Click or drag a .czml file here'}
        </div>
        <input
          id="czml-file-input"
          type="file"
          accept=".czml,application/json"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </div>

      {error && <div className="upload-error">{error}</div>}
      {success && <div className="upload-success">{success}</div>}

      {/* API section */}
      <div className="api-section">
        <div className="api-header">
          <span className="api-status-indicator">
            <span
              className={`status-dot ${
                apiStatus === ApiStatus.CONNECTED
                  ? 'connected'
                  : apiStatus === ApiStatus.CONNECTING
                  ? 'connecting'
                  : apiStatus === ApiStatus.ERROR
                  ? 'error'
                  : 'idle'
              }`}
            />
            API: {apiStatus}
          </span>
          <button
            className="connect-btn"
            onClick={handleConnect}
            disabled={apiStatus === ApiStatus.CONNECTING}
          >
            {apiStatus === ApiStatus.CONNECTING ? 'Connecting...' : 'Connect'}
          </button>
        </div>

        {apiStatus === ApiStatus.CONNECTED && simulations.length > 0 && (
          <div className="simulation-list">
            {simulations.map((sim) => (
              <button
                key={sim.id || sim}
                className="simulation-item"
                onClick={() => handleApiSimulationSelect(sim.id || sim)}
              >
                <span className="sim-name">{sim.name || sim.id || sim}</span>
                <span className="sim-time">{sim.timestamp || ''}</span>
              </button>
            ))}
          </div>
        )}

        {apiStatus === ApiStatus.CONNECTED &&
          simulations.length === 0 && (
            <div className="no-simulations">No simulations available</div>
          )}
      </div>
    </div>
  );
}
