import { useEffect, useRef, useState, useCallback } from 'react';
import * as Cesium from 'cesium';
import { classifyEntity, EntityType, extractEntityMetrics } from '@utils/czmlUtils.js';
import 'cesium/Source/Widgets/widgets.css';
import './CesiumGlobe.css';

// No Cesium ion tokens required — we use OpenStreetMap imagery.
Cesium.Ion.defaultAccessToken = '';

/**
 * CesiumGlobe — the core 3D visualization component.
 *
 * Renders a CesiumJS Viewer inside a React-managed div and exposes
 * a clean API for:
 *
 *   - Loading CZML data (from file or API).
 *   - Toggling entity categories (satellites, coverage, ground stations, orbits).
 *   - Handling entity picking for the metrics dashboard.
 *   - Driving the timeline clock from CZML time-dynamic data.
 *
 * @param {Object} props
 * @param {Array|null} props.czmlData - Parsed CZML array (or null).
 * @param {boolean} props.showSatellites
 * @param {boolean} props.showCoverage
 * @param {boolean} props.showGroundStations
 * @param {boolean} props.showOrbits
 * @param {Function} props.onEntitySelect - Callback when an entity is clicked.
 * @param {Date|null} props.currentTime
 * @param {Function} props.onCurrentTimeChange
 * @param {boolean} props.isPlaying
 * @param {Function} props.onIsPlayingChange
 */
export default function CesiumGlobe({
  czmlData,
  showSatellites = true,
  showCoverage = true,
  showGroundStations = true,
  showOrbits = false,
  onEntitySelect,
  currentTime,
  onCurrentTimeChange,
  isPlaying,
  onIsPlayingChange,
}) {
  const cesiumContainerRef = useRef(null);
  const viewerRef = useRef(null);
  const czmlDataSourceRef = useRef(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [loadError, setLoadError] = useState(null);

  // Track which props have changed since last effect.
  const visibilityFlagsRef = useRef({
    showSatellites,
    showCoverage,
    showGroundStations,
    showOrbits,
  });
  visibilityFlagsRef.current = {
    showSatellites,
    showCoverage,
    showGroundStations,
    showOrbits,
  };

  // ------------------------------------------------------------------
  // Initialise Cesium Viewer (once).
  // ------------------------------------------------------------------
  useEffect(() => {
    if (!cesiumContainerRef.current || isInitialized) return;

    try {
      const viewer = new Cesium.Viewer(cesiumContainerRef.current, {
        baseLayerPicker: false,
        timeline: true,
        animation: true,
        fullscreenButton: true,
        scene3DModePicker: true,
        selectionModePicker: false,
        infoBox: false,
        selectionIndicator: false,
        navigationHelpButton: false,
        navigationInstructionsInitiallyVisible: false,
        requestWebGl2: true,
      });

      // Use OpenStreetMap imagery (no token needed).
      viewer.imageryLayers.removeAll();
      viewer.scene.globe.enableLighting = true;

      // Entity click handler for picking.
      viewer.screenSpaceEventHandler.setInputAction((movement) => {
        const picked = viewer.scene.pick(movement.position);
        if (
          picked &&
          picked.id
        ) {
          const entity = picked.id;
          const metrics = entity.properties
            ? extractEntityMetrics(entity.properties)
            : {};
          onEntitySelect?.({
            id: entity.id,
            name: entity.name,
            type: classifyEntity(entity.id),
            metrics,
          });
        }
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

      viewerRef.current = viewer;
      setIsInitialized(true);
      setLoadError(null);
    } catch (err) {
      console.error('Failed to initialise Cesium:', err);
      setLoadError(err.message);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isInitialized]);

  // ------------------------------------------------------------------
  // Apply visibility toggles to loaded entities.
  // ------------------------------------------------------------------
  const applyEntityVisibility = useCallback(() => {
    if (!czmlDataSourceRef.current) return;
    const flags = visibilityFlagsRef.current;
    const entities = czmlDataSourceRef.current.entities.values;

    entities.forEach((entity) => {
      const type = classifyEntity(entity.id);
      let visible = true;

      switch (type) {
        case EntityType.SATELLITE:
          visible = flags.showSatellites;
          break;
        case EntityType.HAPS:
          visible = flags.showSatellites;
          break;
        case EntityType.COVERAGE:
          visible = flags.showCoverage;
          break;
        case EntityType.GROUND_STATION:
          visible = flags.showGroundStations;
          break;
        case EntityType.BASE_STATION:
          visible = flags.showGroundStations;
          break;
        default:
          visible = true;
      }

      entity.show = visible;
    });
  }, []);

  // ------------------------------------------------------------------
  // Load / update CZML data when czmlData changes.
  // ------------------------------------------------------------------
  const loadCzml = useCallback(async () => {
    if (!viewerRef.current || !czmlData || !Array.isArray(czmlData)) return;
    const viewer = viewerRef.current;

    // Remove existing data source.
    if (czmlDataSourceRef.current) {
      viewer.dataSources.remove(czmlDataSourceRef.current, true);
    }
    czmlDataSourceRef.current = null;

    try {
      const dataSource = await Cesium.CzmlDataSource.load(czmlData);
      czmlDataSourceRef.current = dataSource;
      viewer.dataSources.add(dataSource);
      viewer.flyTo(dataSource);

      // Sync the timeline if the CZML has a clock.
      if (dataSource.clock) {
        viewer.clock = dataSource.clock;
        viewer.clock.shouldAnimate = isPlaying;
      }

      // Apply initial visibility.
      applyEntityVisibility();

      setLoadError(null);
    } catch (err) {
      console.error('Failed to load CZML:', err);
      setLoadError(err.message);
    }
  }, [czmlData, isPlaying, applyEntityVisibility]);

  // Load CZML when data changes.
  useEffect(() => {
    loadCzml();
  }, [loadCzml]);

  // Re-apply visibility when toggles change.
  useEffect(() => {
    applyEntityVisibility();
  }, [applyEntityVisibility]);

  // Sync timeline playback state.
  useEffect(() => {
    if (!viewerRef.current) return;
    if (czmlDataSourceRef.current && czmlDataSourceRef.current.clock) {
      viewerRef.current.clock = czmlDataSourceRef.current.clock;
    }
    viewerRef.current.clock.shouldAnimate = isPlaying;
  }, [isPlaying]);

  const togglePlayback = () => {
    if (!viewerRef.current) return;
    const next = !isPlaying;
    viewerRef.current.clock.shouldAnimate = next;
    onIsPlayingChange?.(next);
  };

  return (
    <>
      <div ref={cesiumContainerRef} id="cesiumContainer" />
      {loadError && (
        <div className="cesium-error-overlay">
          <span>⚠ Cesium error: {loadError}</span>
        </div>
      )}
      <div className="cesium-overlay">
        <button
          className={`play-btn ${isPlaying ? 'playing' : ''}`}
          onClick={togglePlayback}
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? '❚❚' : '▶'}
        </button>
      </div>
    </>
  );
}
