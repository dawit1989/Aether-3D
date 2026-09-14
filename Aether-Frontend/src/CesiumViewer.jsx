import React, { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';

// Cesium's global base URL needs to be set before importing the full
// Cesium build so that workers, shaders, and assets resolve correctly.
// We point to the CDN copy which works for local development.
// If you have a local Cesium distribution, change this to 'cesium/'.
window.CESIUM_BASE_URL = window.CESIUM_BASE_URL || 'https://unpkg.com/cesium/Build/Cesium/';

/**
 * CesiumViewer – renders a full-page CesiumJS Viewer that looks at
 * San Francisco from a low angle.
 *
 * The Cesium ion token is read from the Vite environment variable
 * VITE_CESIUM_ION_TOKEN.  If the variable is missing or empty a
 * warning is printed and Cesium falls back to anonymous access.
 */
export default function CesiumViewer() {
  const viewerContainerRef = useRef(null);
  const viewerRef = useRef(null);

  useEffect(() => {
    if (!viewerContainerRef.current) return;

    // Read the token from the Vite environment.
    const token = import.meta.env.VITE_CESIUM_ION_TOKEN;

    if (token && token !== 'your_cesium_ion_token_here') {
      Cesium.Ion.defaultAccessToken = token;
    } else {
      console.warn(
        'Cesium ion token not set. Set VITE_CESIUM_ION_TOKEN in your .env file. ' +
        'The viewer will use anonymous access with limited features.'
      );
      Cesium.Ion.defaultAccessToken = '';
    }

    try {
      const viewer = new Cesium.Viewer(viewerContainerRef.current, {
        baseLayerPicker: false,
        timeline: false,
        animation: false,
        fullscreenButton: false,
        scene3DModePicker: false,
        selectionModePicker: false,
        infoBox: false,
        selectionIndicator: false,
        // Use OpenStreetMap imagery as the base layer (no token required).
        baseImageryLayer: Cesium.IonImageryProvider,
      });

      viewerRef.current = viewer;

      // --- Fly the camera to San Francisco from a low angle ----
      // San Francisco coordinates (approximate city centre).
      const sfPosition = Cesium.Cartesian3.fromDegrees(
        -122.4194,  // longitude
        37.7749,    // latitude
        15000.0     // height above ground in metres (low-angle)
      );

      // Set the camera to look at SF from a low angle (shallow pitch).
      viewer.camera.flyTo({
        destination: sfPosition,
        orientation: {
          heading: Cesium.Math.toRadians(0),   // north
          pitch: Cesium.Math.toRadians(-15),    // low angle (15° from horizontal)
          roll: 0,
        },
        duration: 0, // instant
      });

      // Clean up on unmount
      return () => {
        if (viewerRef.current && !viewerRef.current.isDestroyed()) {
          viewerRef.current.destroy();
          viewerRef.current = null;
        }
      };
    } catch (error) {
      console.error('Failed to initialise Cesium Viewer:', error);
    }
  }, []);

  return (
    <div
      ref={viewerContainerRef}
      style={{
        width: '100vw',
        height: '100vh',
        margin: 0,
        padding: 0,
        overflow: 'hidden',
      }}
    />
  );
}
