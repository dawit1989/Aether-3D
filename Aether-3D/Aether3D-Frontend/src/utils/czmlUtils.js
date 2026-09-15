/**
 * CZML parsing and entity-classification utilities for Aether-3D.
 *
 * Simulator CZML entity ID conventions:
 *   - Satellite trajectories  (id: "Sat_<N>", "satellite*")
 *   - Ground stations         (id: "ground_station*")
 *   - Coverage cells          (id: "coverage_sat_<N>")
 *   - HAPS                    (id: "haps_<N>")
 *   - Base stations           (id: "bs_<N>")
 */

export const EntityType = {
  SATELLITE: 'satellite',
  GROUND_STATION: 'ground_station',
  COVERAGE: 'coverage',
  HAPS: 'haps',
  BASE_STATION: 'base_station',
  UNKNOWN: 'unknown',
};

/**
 * Classify a CZML entity by its `id` string.
 * @param {string} entityId
 * @returns {string} EntityType value
 */
export function classifyEntity(entityId) {
  if (!entityId || typeof entityId !== 'string') {
    return EntityType.UNKNOWN;
  }
  const id = entityId.toLowerCase();

  if (id.startsWith('coverage_')) {
    return EntityType.COVERAGE;
  }
  if (id.startsWith('ground_station')) {
    return EntityType.GROUND_STATION;
  }
  if (id.startsWith('haps')) {
    return EntityType.HAPS;
  }
  if (id.startsWith('bs_')) {
    return EntityType.BASE_STATION;
  }
  if (id.startsWith('sat_') || id.startsWith('satellite')) {
    return EntityType.SATELLITE;
  }
  return EntityType.UNKNOWN;
}

/**
 * Filter entities by type.
 * @param {Array} czmlData
 * @param {string} type
 * @returns {Array}
 */
export function getEntitiesByType(czmlData, type) {
  if (!Array.isArray(czmlData)) return [];
  return czmlData.filter((packet) => packet && packet.id && classifyEntity(packet.id) === type);
}

/**
 * Extract numerical or string properties from CZML property object.
 * @param {Object} entityPacket
 * @returns {Object}
 */
export function extractEntityMetrics(entityPacket) {
  if (!entityPacket || !entityPacket.properties) return {};
  const metrics = {};
  for (const [key, val] of Object.entries(entityPacket.properties)) {
    if (val && typeof val === 'object' && 'number' in val) {
      metrics[key] = val.number;
    } else {
      metrics[key] = val;
    }
  }
  return metrics;
}

/**
 * Validate CZML array structure.
 * @param {Array} czmlData
 * @returns {{valid: boolean, entityCount: number, error: string|null}}
 */
export function validateCzml(czmlData) {
  if (!czmlData) {
    return { valid: false, entityCount: 0, error: 'No data provided' };
  }
  if (!Array.isArray(czmlData)) {
    return { valid: false, entityCount: 0, error: 'CZML document must be a JSON array' };
  }
  const entityCount = czmlData.filter((p) => p && p.id).length;
  if (entityCount === 0) {
    return { valid: false, entityCount: 0, error: 'No valid entity packets found in CZML' };
  }
  return { valid: true, entityCount, error: null };
}

/**
 * Find clock definition packet if present.
 * @param {Array} czmlData
 * @returns {Object|null}
 */
export function findClockPacket(czmlData) {
  if (!Array.isArray(czmlData)) return null;
  return czmlData.find((p) => p && p.clock) || null;
}
