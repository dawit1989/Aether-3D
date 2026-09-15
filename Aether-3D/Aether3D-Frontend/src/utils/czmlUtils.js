/**
 * CZML parsing and entity-classification utilities.
 *
 * The Aether-3D simulator's CZMLWriter emits entities for:
 *   - Satellite trajectories  (id: "Sat_<N>")
 *   - Ground stations         (id: "ground_station")
 *   - Coverage cells          (id: "coverage_sat_<N>")
 *   - HAPS                    (id: "haps_<N>")
 *   - Base stations           (id: "bs_<N>")
 *
 * Each entity may carry a `properties` block with channel-quality metrics
 * such as mean P_Rx, SNR, SINR, distance, elevation, etc.
 *
 * @module czmlUtils
 */

/** Entity type categories derived from the `id` prefix. */
export const EntityType = {
  SATELLITE: 'satellite',
  GROUND_STATION: 'ground_station',
  COVERAGE: 'coverage',
  HAPS: 'haps',
  BASE_STATION: 'base_station',
  UNKNOWN: 'unknown',
};

/**
 * Classify a CZML entity by its `id` field.
 *
 * @param {string} entityId - The CZML entity id.
 * @returns {string} A value from the EntityType enum.
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
 * Extract all entities of a given type from a CZML array.
 *
 * @param {Array} czmlData - The parsed CZML document (array of packets).
 * @param {string} type - A value from EntityType.
 * @returns {Array} Matching entity packets.
 */
export function getEntitiesByType(czmlData, type) {
  if (!Array.isArray(czmlData)) return [];
  return czmlData.filter((packet) => {
    if (!packet || !packet.id) return false;
    return classifyEntity(packet.id) === type;
  });
}

/**
 * Extract the channel-quality properties from a CZML entity packet.
 *
 * The CZMLWriter stores metrics in `packet.properties` as a map of
 * named number values.  This helper flattens them into a plain object.
 *
 * @param {Object} entityPacket - A CZML entity packet.
 * @returns {Object} Key-value metric pairs, or {} if none.
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
 * Validate that a parsed CZML array has at least one data-carrying packet.
 *
 * @param {Array} czmlData - The parsed CZML document.
 * @returns {{valid: boolean, entityCount: number, error: string|null}}
 */
export function validateCzml(czmlData) {
  if (!czmlData) {
    return { valid: false, entityCount: 0, error: 'No data' };
  }
  if (!Array.isArray(czmlData)) {
    return { valid: false, entityCount: 0, error: 'CZML must be an array' };
  }
  const hasData = czmlData.some(
    (p) => p && (p.id || p.version)
  );
  if (!hasData) {
    return { valid: false, entityCount: 0, error: 'No entities found' };
  }
  const entityCount = czmlData.filter((p) => p && p.id).length;
  return { valid: true, entityCount, error: null };
}

/**
 * Find the first clock packet in a CZML array (if the writer included one).
 *
 * @param {Array} czmlData - The parsed CZML document.
 * @returns {Object|null} The clock packet or null.
 */
export function findClockPacket(czmlData) {
  if (!Array.isArray(czmlData)) return null;
  return czmlData.find((p) => p && p.clock) || null;
}

/**
 * Convert a CZML entity packet into a human-readable summary string.
 *
 * @param {Object} packet - A CZML entity packet.
 * @returns {string}
 */
export function entitySummary(packet) {
  if (!packet) return 'Unknown entity';
  const metrics = extractEntityMetrics(packet);
  const parts = [packet.name || packet.id];
  const metricEntries = Object.entries(metrics).slice(0, 4);
  for (const [k, v] of metricEntries) {
    if (typeof v === 'number') {
      parts.push(`${k}: ${v.toFixed(2)}`);
    }
  }
  return parts.join(' — ');
}
