import React, { useState, useCallback } from 'react';
import CesiumGlobe from '@components/CesiumGlobe.jsx';
import FileUploader from '@components/FileUploader.jsx';
import ControlPanel from '@components/ControlPanel.jsx';
import MetricsDashboard from '@components/MetricsDashboard.jsx';
import StatusBar from '@components/StatusBar.jsx';
import { ApiProvider } from '@hooks/useApi.jsx';
import './App.css';

/**
 * Root application component for Aether3D-Frontend.
 *
 * Layout:
 *   ┌─────────────────────────────────────────────┐
 *   │  StatusBar                                 │
 *   ├─────┬──────────────┬──────────────────────┤
 *   │     │  ControlPanel │                      │
 *   │     │  CesiumGlobe │                      │
 *   │  M  │              │                      │
 *   │  e  │              │                      │
 *   │  t  └──────────────┘                      │
 *   │  r                                         │
 *   │  i                                         │
 *   │  c                                         │
 *   │  s                                         │
 *   │  D                                         │
 *   │  a                                         │
 *   │  s                                         │
 *   │  h                                         │
 *   │  b                                         │
 *   │  o                                         │
 *   │  a                                         │
 *   │  r                                         │
 *   └─────┴──────────────────────────────────────┘
 */
export default function App() {
  // Active CZML entities loaded into the globe.
  const [czmlData, setCzmlData] = useState(null);
  const [czmlFileName, setCzmlFileName] = useState('');

  // Visualisation toggles.
  const [showSatellites, setShowSatellites] = useState(true);
  const [showCoverage, setShowCoverage] = useState(true);
  const [showGroundStations, setShowGroundStations] = useState(true);
  const [showOrbits, setShowOrbits] = useState(false);

  // Time-animator state (driven by CZML clock when available).
  const [currentTime, setCurrentTime] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Selected entity for metrics inspection.
  const [selectedEntity, setSelectedEntity] = useState(null);

  // API integration.
  const [apiEndpoint, setApiEndpoint] = useState(
    import.meta.env.VITE_API_BASE || 'http://localhost:8000'
  );

  const handleCzmlLoad = useCallback((data, name) => {
    setCzmlData(data);
    setCzmlFileName(name);
    setSelectedEntity(null);
  }, []);

  const handleEntitySelect = useCallback((entity) => {
    setSelectedEntity(entity);
  }, []);

  return (
    <ApiProvider endpoint={apiEndpoint}>
      <div className="app">
        <StatusBar
          fileName={czmlFileName}
          apiEndpoint={apiEndpoint}
          onApiEndpointChange={setApiEndpoint}
        />

        <div className="main-area">
          {/* Left sidebar: file upload + controls */}
          <div className="sidebar">
            <FileUploader onCzmlLoad={handleCzmlLoad} />
            <ControlPanel
              showSatellites={showSatellites}
              onShowSatellitesChange={setShowSatellites}
              showCoverage={showCoverage}
              onShowCoverageChange={setShowCoverage}
              showGroundStations={showGroundStations}
              onShowGroundStationsChange={setShowGroundStations}
              showOrbits={showOrbits}
              onShowOrbitsChange={setShowOrbits}
            />
          </div>

          {/* Centre: Cesium 3D globe */}
          <div className="globe-container">
            <CesiumGlobe
              czmlData={czmlData}
              showSatellites={showSatellites}
              showCoverage={showCoverage}
              showGroundStations={showGroundStations}
              showOrbits={showOrbits}
              onEntitySelect={handleEntitySelect}
              currentTime={currentTime}
              onCurrentTimeChange={setCurrentTime}
              isPlaying={isPlaying}
              onIsPlayingChange={setIsPlaying}
            />
          </div>
        </div>

        {/* Bottom panel: metrics dashboard */}
        <MetricsDashboard
          selectedEntity={selectedEntity}
          czmlData={czmlData}
          czmlFileName={czmlFileName}
        />
      </div>
    </ApiProvider>
  );
}
