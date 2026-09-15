import React, { useState, useCallback, Suspense, lazy } from 'react';
import { FluentProvider, webDarkTheme } from '@fluentui/react-components';
import FileUploader from '@components/FileUploader.jsx';
import ControlPanel from '@components/ControlPanel.jsx';
import MetricsDashboard from '@components/MetricsDashboard.jsx';
import StatusBar from '@components/StatusBar.jsx';
import { ApiProvider } from '@hooks/useApi.jsx';
import './App.css';

const CesiumGlobe = lazy(() => import('@components/CesiumGlobe.jsx'));

export default function App() {
  const [czmlData, setCzmlData] = useState(null);
  const [czmlFileName, setCzmlFileName] = useState('');

  const [showSatellites, setShowSatellites] = useState(true);
  const [showCoverage, setShowCoverage] = useState(true);
  const [showGroundStations, setShowGroundStations] = useState(true);
  const [showOrbits, setShowOrbits] = useState(false);

  const [terrainMode, setTerrainMode] = useState('ellipsoid');
  const [baseMap, setBaseMap] = useState('osm');

  const [currentTime, setCurrentTime] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const [selectedEntity, setSelectedEntity] = useState(null);
  const [dashboardCollapsed, setDashboardCollapsed] = useState(false);

  const [apiEndpoint, setApiEndpoint] = useState('http://localhost:8000');

  const handleCzmlLoad = useCallback((data, name) => {
    setCzmlData(data);
    setCzmlFileName(name);
    setSelectedEntity(null);
    setDashboardCollapsed(false);
  }, []);

  const handleEntitySelect = useCallback((entity) => {
    setSelectedEntity(entity);
    setDashboardCollapsed(false);
  }, []);

  return (
    <FluentProvider theme={webDarkTheme} className={`app ${dashboardCollapsed ? 'dashboard-collapsed' : ''}`}>
      <ApiProvider endpoint={apiEndpoint}>
        <StatusBar
          fileName={czmlFileName}
          apiEndpoint={apiEndpoint}
          onApiEndpointChange={setApiEndpoint}
        />

        <div className="main-area">
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
              terrainMode={terrainMode}
              onTerrainModeChange={setTerrainMode}
              baseMap={baseMap}
              onBaseMapChange={setBaseMap}
            />
          </div>

          <div className="globe-container">
            <Suspense
              fallback={
                <div className="globe-loading">
                  <div className="loading-spinner" />
                  <span>Loading 3D Globe Engine…</span>
                </div>
              }
            >
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
                terrainMode={terrainMode}
                baseMap={baseMap}
              />
            </Suspense>
          </div>
        </div>

        <MetricsDashboard
          selectedEntity={selectedEntity}
          czmlData={czmlData}
          collapsed={dashboardCollapsed}
          onToggleCollapse={() => setDashboardCollapsed((prev) => !prev)}
        />
      </ApiProvider>
    </FluentProvider>
  );
}
