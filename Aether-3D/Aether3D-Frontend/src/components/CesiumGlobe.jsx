import { useEffect, useRef, useState } from 'react';
import * as Cesium from 'cesium';
import { Button } from '@fluentui/react-components';
import { Play24Filled, Pause24Filled } from '@fluentui/react-icons';
import { classifyEntity, EntityType, extractEntityMetrics } from '@utils/czmlUtils.js';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import './CesiumGlobe.css';
import './CesiumDarkTheme.css';

Cesium.Ion.defaultAccessToken = '';

export default function CesiumGlobe({
  czmlData,
  showSatellites = true,
  showCoverage = true,
  showGroundStations = true,
  showOrbits = false,
  onEntitySelect,
  isPlaying,
  onIsPlayingChange,
  terrainMode = 'ellipsoid',
  baseMap = 'osm',
}) {
  const cesiumContainerRef = useRef(null);
  const viewerRef = useRef(null);
  const czmlDataSourceRef = useRef(null);
  const tooltipRef = useRef(null);
  const [loadError, setLoadError] = useState(null);

  // Initialise Cesium Viewer once
  useEffect(() => {
    if (!cesiumContainerRef.current || viewerRef.current) return;

    try {
      const viewer = new Cesium.Viewer(cesiumContainerRef.current, {
        baseLayer: new Cesium.ImageryLayer(
          new Cesium.OpenStreetMapImageryProvider({
            url: 'https://tile.openstreetmap.org/',
          })
        ),
        baseLayerPicker: false,
        timeline: true,
        animation: true,
        fullscreenButton: true,
        sceneModePicker: true,
        infoBox: false,
        selectionIndicator: false,
        navigationHelpButton: false,
        navigationInstructionsInitiallyVisible: false,
        requestWebgl2: true,
      });

      viewer.scene.globe.enableLighting = true;

      // Entity click picker
      viewer.screenSpaceEventHandler.setInputAction((movement) => {
        const picked = viewer.scene.pick(movement.position);
        if (picked && picked.id) {
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

      // Hover tooltip handler
      viewer.screenSpaceEventHandler.setInputAction((movement) => {
        const tooltip = tooltipRef.current;
        if (!tooltip) return;

        const picked = viewer.scene.pick(movement.endPosition);
        if (picked && picked.id && picked.id.id) {
          const entity = picked.id;
          const entityType = classifyEntity(entity.id);
          const metrics = entity.properties
            ? extractEntityMetrics(entity.properties)
            : {};

          let html = `<div class="tooltip-name">${entity.name || entity.id}</div>`;
          html += `<div class="tooltip-type">${entityType}</div>`;

          const metricKeys = ['SINR (dB)', 'SNR (dB)', 'Distance (km)', 'meanPRx'];
          let shown = 0;
          for (const key of metricKeys) {
            if (shown >= 3) break;
            const val = metrics[key];
            if (val !== undefined && typeof val === 'number') {
              const unit = key.includes('dB') ? 'dB' : key.includes('km') ? 'km' : 'dBW';
              html += `<div class="tooltip-metric"><span class="tooltip-metric-label">${key}:</span><span class="tooltip-metric-value">${val.toFixed(1)} ${unit}</span></div>`;
              shown++;
            }
          }

          tooltip.innerHTML = html;
          tooltip.style.display = 'block';
          tooltip.style.left = `${movement.endPosition.x + 16}px`;
          tooltip.style.top = `${movement.endPosition.y - 8}px`;
        } else {
          tooltip.style.display = 'none';
        }
      }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

      viewerRef.current = viewer;
      setLoadError(null);
    } catch (err) {
      console.error('Failed to initialise Cesium:', err);
      setLoadError(err.message);
    }

    return () => {
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        viewerRef.current.destroy();
      }
      viewerRef.current = null;
    };
  }, [onEntitySelect]);

  // Apply visibility toggles to loaded entities
  useEffect(() => {
    if (!czmlDataSourceRef.current) return;
    const entities = czmlDataSourceRef.current.entities.values;

    entities.forEach((entity) => {
      const type = classifyEntity(entity.id);
      let visible = true;

      switch (type) {
        case EntityType.SATELLITE:
        case EntityType.HAPS:
          visible = showSatellites;
          break;
        case EntityType.COVERAGE:
          visible = showCoverage;
          break;
        case EntityType.GROUND_STATION:
        case EntityType.BASE_STATION:
          visible = showGroundStations;
          break;
        default:
          break;
      }

      entity.show = visible;

      if (entity.path) {
        entity.path.show = showOrbits;
      }
    });

    viewerRef.current?.scene?.requestRender();
  }, [showSatellites, showCoverage, showGroundStations, showOrbits]);

  // Load CZML data into scene
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    if (czmlDataSourceRef.current) {
      viewer.dataSources.remove(czmlDataSourceRef.current, true);
      czmlDataSourceRef.current = null;
    }

    if (!czmlData) return;

    Cesium.CzmlDataSource.load(czmlData)
      .then((ds) => {
        czmlDataSourceRef.current = ds;
        return viewer.dataSources.add(ds);
      })
      .then(() => {
        viewer.zoomTo(czmlDataSourceRef.current);
      })
      .catch((err) => {
        console.error('Failed to load CZML:', err);
        setLoadError(err.message);
      });
  }, [czmlData]);

  // Terrain model provider switching
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    if (terrainMode === 'srtm') {
      Cesium.CesiumTerrainProvider.fromUrl(
        'https://assets.ion.cesium.com/1',
        { requestVertexNormals: true }
      )
        .then((provider) => {
          if (viewerRef.current && !viewerRef.current.isDestroyed()) {
            viewerRef.current.terrainProvider = provider;
          }
        })
        .catch(() => {
          viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
        });
    } else {
      viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
    }
  }, [terrainMode]);

  // Base map provider switching
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    viewer.imageryLayers.removeAll();

    switch (baseMap) {
      case 'osm':
        viewer.imageryLayers.addImageryProvider(
          new Cesium.OpenStreetMapImageryProvider({
            url: 'https://tile.openstreetmap.org/',
          })
        );
        break;
      case 'cartodb':
        viewer.imageryLayers.addImageryProvider(
          new Cesium.UrlTemplateImageryProvider({
            url: 'https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
          })
        );
        break;
      case 'arcgis':
        Cesium.ArcGisMapServerImageryProvider.fromUrl(
          'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
        )
          .then((provider) => {
            if (viewerRef.current && !viewerRef.current.isDestroyed()) {
              viewerRef.current.imageryLayers.addImageryProvider(provider);
            }
          })
          .catch(() => {
            viewer.imageryLayers.addImageryProvider(
              new Cesium.OpenStreetMapImageryProvider({
                url: 'https://tile.openstreetmap.org/',
              })
            );
          });
        break;
      case 'none':
        break;
      default:
        break;
    }
  }, [baseMap]);

  // Sync animation clock
  useEffect(() => {
    if (!viewerRef.current) return;
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
      <div ref={tooltipRef} className="cesium-hover-tooltip" style={{ display: 'none' }} />
      {loadError && (
        <div className="cesium-error-overlay">
          <span>⚠ Cesium error: {loadError}</span>
        </div>
      )}
      <div className="cesium-overlay">
        <Button
          circular
          appearance="primary"
          icon={isPlaying ? <Pause24Filled /> : <Play24Filled />}
          onClick={togglePlayback}
          title={isPlaying ? 'Pause' : 'Play'}
        />
      </div>
    </>
  );
}
