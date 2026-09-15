/**
 * API integration hook and context.
 *
 * The Aether-3D simulator can expose a REST API (e.g. via FastAPI / Flask)
 * that returns simulation results as JSON.  This module provides:
 *
 *  - `ApiProvider`   — React context provider that sets the base URL.
 *  - `useApi()`      — returns helper methods for fetching simulation data.
 *  - `apiClient`     — a standalone fetch-based client for non-React use.
 *
 * Endpoints (optional backend):
 *   GET /api/simulations        → list of recent runs
 *   GET /api/czml/<id>          → CZML for a specific run
 *   GET /api/metrics/<id>       → channel-quality metrics JSON
 *   GET /api/status             → server health check
 *
 * @module useApi
 */

import { createContext, useContext, useState, useCallback } from 'react';

const ApiContext = createContext(null);

export const ApiStatus = {
  IDLE: 'idle',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  ERROR: 'error',
};

export const apiClient = {
  /**
   * Fetch CZML data for a simulation run.
   * @param {string} base - Base URL of the API server.
   * @param {string} simulationId - Run identifier.
   * @returns {Promise<Array>} Parsed CZML array.
   */
  async fetchCzml(base, simulationId) {
    const res = await fetch(`${base}/api/czml/${simulationId}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch CZML: ${res.status} ${res.statusText}`);
    }
    return res.json();
  },

  /**
   * Fetch metrics for a simulation run.
   * @param {string} base - Base URL.
   * @param {string} simulationId - Run identifier.
   * @returns {Promise<Object>} Metrics object.
   */
  async fetchMetrics(base, simulationId) {
    const res = await fetch(`${base}/api/metrics/${simulationId}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch metrics: ${res.status} ${res.statusText}`);
    }
    return res.json();
  },

  /**
   * List available simulations.
   * @param {string} base - Base URL.
   * @returns {Promise<Array>}
   */
  async listSimulations(base) {
    const res = await fetch(`${base}/api/simulations`);
    if (!res.ok) {
      throw new Error(`Failed to list simulations: ${res.status}`);
    }
    return res.json();
  },

  /**
   * Check API server health.
   * @param {string} base - Base URL.
   * @returns {Promise<{ok: boolean, latency: number}>}
   */
  async checkHealth(base) {
    const start = Date.now();
    try {
      const res = await fetch(`${base}/api/status`, { signal: AbortSignal.timeout(5000) });
      const latency = Date.now() - start;
      return { ok: res.ok, latency };
    } catch (err) {
      return { ok: false, latency: Date.now() - start, error: err.message };
    }
  },
};

/**
 * React context provider for the API.
 *
 * Wraps the app so any child component can call `useApi()` to get
 * the current API status and fetch functions.
 */
export function ApiProvider({ endpoint, children }) {
  const [apiStatus, setApiStatus] = useState(ApiStatus.IDLE);
  const [apiError, setApiError] = useState(null);
  const [simulations, setSimulations] = useState([]);

  const checkConnection = useCallback(async () => {
    setApiStatus(ApiStatus.CONNECTING);
    setApiError(null);
    try {
      const result = await apiClient.checkHealth(endpoint);
      if (result.ok) {
        setApiStatus(ApiStatus.CONNECTED);
        const sims = await apiClient.listSimulations(endpoint);
        setSimulations(sims);
      } else {
        setApiStatus(ApiStatus.ERROR);
        setApiError(result.error || 'Connection failed');
      }
    } catch (err) {
      setApiStatus(ApiStatus.ERROR);
      setApiError(err.message);
    }
  }, [endpoint]);

  const fetchSimulation = useCallback(
    async (simulationId, type = 'czml') => {
      if (type === 'czml') {
        return apiClient.fetchCzml(endpoint, simulationId);
      }
      return apiClient.fetchMetrics(endpoint, simulationId);
    },
    [endpoint]
  );

  return (
    <ApiContext.Provider
      value={{
        endpoint,
        apiStatus,
        apiError,
        simulations,
        checkConnection,
        fetchSimulation,
      }}
    >
      {children}
    </ApiContext.Provider>
  );
}

/**
 * Hook to access the API context.
 * @returns {Object} API context value.
 */
export function useApi() {
  const ctx = useContext(ApiContext);
  if (!ctx) {
    // Provide a default no-op context when used outside the provider.
    return {
      endpoint: '',
      apiStatus: ApiStatus.IDLE,
      apiError: null,
      simulations: [],
      checkConnection: async () => {},
      fetchSimulation: async () => {
        throw new Error('ApiProvider not found in component tree');
      },
    };
  }
  return ctx;
}
