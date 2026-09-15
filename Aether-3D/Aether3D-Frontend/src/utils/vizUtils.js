/**
 * Color mapping and visualization helpers.
 *
 * These helpers map channel-quality metrics to visually meaningful
 * colors for the Cesium entities.  The CZMLWriter in the Aether-3D
 * simulator already encodes received power as viridis colormap,
 * but these helpers provide a frontend-side fallback for cases
 * where the CZML doesn't carry color data or when overriding
 * colors based on selected metrics.
 *
 * @module vizUtils
 */

/**
 * Convert a received-power value (dBW) to a Cesium color.
 *
 * @param {number} pwrDbw - Received power in dBW.
 * @param {number} [vmin=-120] - Minimum power for normalization.
 * @param {number} [vmax=-60] - Maximum power for normalization.
 * @returns {object} Cesium Color object (import { Color } from 'cesium').
 */
export function pwrToColor(pwrDbw, vmin = -120, vmax = -60) {
  const norm = clamp((pwrDbw - vmin) / (vmax - vmin), 0, 1);
  // Simple gradient: red (bad) → yellow → green (good)
  const r = Math.round(255 * (1 - norm));
  const g = Math.round(255 * norm);
  const b = 0;
  return { r, g, b, a: 255 };
}

/**
 * Convert an SINR value (dB) to a color.
 *
 * @param {number} sinrDb - SINR in dB.
 * @param {number} [vmin=-10] - Minimum SINR.
 * @param {number} [vmax=30] - Maximum SINR.
 * @returns {object} RGBA color.
 */
export function sinrToColor(sinrDb, vmin = -10, vmax = 30) {
  const norm = clamp((sinrDb - vmin) / (vmax - vmin), 0, 1);
  const r = Math.round(255 * (1 - norm));
  const g = Math.round(255 * norm);
  const b = 0;
  return { r, g, b, a: 255 };
}

/**
 * Convert an elevation angle (degrees) to a color (blue → green → yellow).
 *
 * @param {number} elevDeg - Elevation angle in degrees.
 * @param {number} [vmin=0] - Minimum elevation.
 * @param {number} [vmax=90] - Maximum elevation.
 * @returns {object} RGBA color.
 */
export function elevationToColor(elevDeg, vmin = 0, vmax = 90) {
  const norm = clamp((elevDeg - vmin) / (vmax - vmin), 0, 1);
  const r = Math.round(255 * (1 - norm));
  const g = Math.round(255 * norm);
  const b = Math.round(255 * (1 - norm * 0.5));
  return { r, g, b, a: 255 };
}

/**
 * Format a number for display with appropriate precision.
 *
 * @param {number} value - The value to format.
 * @param {number} [decimals=2] - Number of decimal places.
 * @returns {string} Formatted string.
 */
export function formatMetric(value, decimals = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }
  return Number(value).toFixed(decimals);
}

/**
 * Clamp a number between min and max.
 *
 * @param {number} value
 * @param {number} min
 * @param {number} max
 * @returns {number}
 */
export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

/**
 * Format a Cesium time or JS Date to a human-readable string.
 *
 * @param {Date|number|string} time
 * @returns {string}
 */
export function formatTime(time) {
  if (!time) return '—';
  try {
    const d = new Date(time);
    return d.toLocaleString();
  } catch {
    return String(time);
  }
}
